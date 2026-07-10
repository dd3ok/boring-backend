#!/usr/bin/env python3
"""Run a provider-neutral skill activation evaluation.

The adapter command receives ``--request PATH --response PATH``. Requests expose
the query, variant runtime path, isolated directories, trial, and paired seed,
but no case id or expected label. Responses may contain nullable ``activation``,
``catalogs``, and ``usage`` fields plus bounded declared artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import random
import re
import signal
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, BinaryIO, NamedTuple


ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = Path(__file__).resolve()
PROTOCOL_VERSION = 3
STDERR_EXCERPT_LIMIT = 2048
RESPONSE_BYTE_LIMIT = 64 * 1024
JSON_DEPTH_LIMIT = 100
USAGE_VALUE_MAX = (1 << 53) - 1
ARTIFACT_COUNT_LIMIT = 32
ARTIFACT_TOTAL_BYTE_LIMIT = 16 * 1024 * 1024
PROCESS_TERMINATE_GRACE_SECONDS = 1.0
STDERR_DRAIN_GRACE_SECONDS = 1.0
WINDOWS_REPARSE_POINT_ATTRIBUTE = 0x400
VARIANT_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
RESPONSE_FIELDS = {"activation", "catalogs", "usage", "artifacts", "metadata", "isolation"}
ISOLATION_FIELDS = {"verified", "method", "unexpected_same_name_skills"}
DISCOVERY_SKILL_ROOTS = (
    Path(".agents/skills"),
    Path(".claude/skills"),
    Path(".codex/skills"),
    Path(".gemini/config/skills"),
)


class EvalError(Exception):
    """A harness or runner protocol failure."""


class RunnerResult(NamedTuple):
    returncode: int
    stderr_excerpt: str
    stderr_truncated: bool
    timed_out: bool
    cleanup_errors: tuple[str, ...]


class BoundedByteCollector:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.buffer = bytearray()
        self.truncated = False
        self.error: OSError | None = None

    def append(self, chunk: bytes) -> None:
        remaining = self.limit - len(self.buffer)
        if remaining > 0:
            self.buffer.extend(chunk[:remaining])
        if len(chunk) > remaining:
            self.truncated = True

    def excerpt(self) -> str:
        raw = bytes(self.buffer)
        if self.truncated:
            suffix = b"\n[truncated]"
            raw = raw[: max(0, self.limit - len(suffix))] + suffix
        value = raw.decode("utf-8", errors="replace")
        while len(value.encode("utf-8")) > self.limit:
            value = value[:-1]
        return value


def strict_json_loads(raw: str | bytes) -> Any:
    def reject_constant(value: str) -> None:
        raise ValueError(f"nonstandard JSON constant {value}")

    raw_bytes = raw.encode("utf-8") if isinstance(raw, str) else raw
    depth = 0
    in_string = False
    escaped = False
    for value in raw_bytes:
        if in_string:
            if escaped:
                escaped = False
            elif value == ord("\\"):
                escaped = True
            elif value == ord('"'):
                in_string = False
            continue
        if value == ord('"'):
            in_string = True
        elif value in (ord("["), ord("{")):
            depth += 1
            if depth > JSON_DEPTH_LIMIT:
                raise ValueError(f"JSON nesting exceeds {JSON_DEPTH_LIMIT}")
        elif value in (ord("]"), ord("}")):
            depth -= 1

    try:
        return json.loads(raw, parse_constant=reject_constant)
    except RecursionError as exc:
        raise ValueError("JSON nesting exceeds the supported limit") from exc


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--suite",
        type=Path,
        default=ROOT / "validation" / "trigger-eval-cases.json",
        help="JSON evaluation suite (defaults to validation/trigger-eval-cases.json)",
    )
    parser.add_argument("--output", type=Path, required=True, help="new or empty report directory")
    parser.add_argument(
        "--work-root",
        type=Path,
        help=(
            "new or empty execution directory outside the repository and same-name "
            "skill discovery ancestors; defaults to an auto-cleaned system temp directory"
        ),
    )
    parser.add_argument("--trials", type=int, default=1, help="trials per case and variant")
    parser.add_argument("--seed", type=int, default=0, help="root seed for deterministic run seeds")
    parser.add_argument(
        "--variant",
        action="append",
        required=True,
        metavar="NAME[=SKILL_PATH]",
        help="named skill variant; omit =SKILL_PATH for a no-skill variant",
    )
    runner = parser.add_mutually_exclusive_group(required=True)
    runner.add_argument(
        "--runner-command",
        help='JSON argument array, for example ["python", "adapter.py"]',
    )
    runner.add_argument("--runner-exe", help="runner executable")
    parser.add_argument(
        "--runner-arg",
        action="append",
        default=[],
        help="runner argument; repeat for multiple arguments",
    )
    parser.add_argument(
        "--runner-metadata",
        default="{}",
        help="JSON object describing the runner/model settings",
    )
    parser.add_argument(
        "--runner-meta",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="string runner metadata; repeat for shell-friendly metadata",
    )
    parser.add_argument("--timeout-seconds", type=float, default=300.0)
    return parser.parse_args(argv)


def parse_json_argument(raw: str, label: str, expected_type: type) -> Any:
    try:
        value = strict_json_loads(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        raise EvalError(f"{label} must be valid JSON: {exc}") from exc
    if not isinstance(value, expected_type):
        raise EvalError(f"{label} must be a JSON {expected_type.__name__}")
    return value


def parse_runner_command(raw: str) -> list[str]:
    command = parse_json_argument(raw, "runner command", list)
    if not command or not all(isinstance(arg, str) for arg in command):
        raise EvalError("runner command must be a nonempty JSON array of strings")
    if not command[0]:
        raise EvalError("runner command executable must not be empty")
    return command


def resolve_runner_file_arguments(command: list[str]) -> list[str]:
    resolved = []
    for argument in command:
        candidate = Path(argument).expanduser()
        if not candidate.is_absolute():
            candidate = ROOT / candidate
        if candidate.is_file():
            resolved.append(str(candidate.resolve()))
        else:
            resolved.append(argument)
    return resolved


def runner_configuration(args: argparse.Namespace) -> tuple[list[str], dict[str, Any]]:
    if args.runner_command is not None:
        command = parse_runner_command(args.runner_command)
        if args.runner_arg:
            raise EvalError("runner args require --runner-exe")
    else:
        command = [args.runner_exe, *args.runner_arg]

    metadata = parse_json_argument(args.runner_metadata, "runner metadata", dict)
    for raw in args.runner_meta:
        if "=" not in raw:
            raise EvalError(f"runner metadata must use KEY=VALUE: {raw!r}")
        key, value = raw.split("=", 1)
        if not key:
            raise EvalError("runner metadata key must not be empty")
        if key in metadata:
            raise EvalError(f"duplicate runner metadata key: {key}")
        metadata[key] = value
    return resolve_runner_file_arguments(command), metadata


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_windows_reparse_point(path: Path) -> bool:
    attributes = getattr(os.lstat(path), "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse_flag)


def reject_linked_skill_path(path: Path) -> None:
    if path.is_symlink():
        raise EvalError(f"skill path must not be a symlink: {path}")
    if is_windows_reparse_point(path):
        raise EvalError(f"skill path must not be a Windows reparse point: {path}")


def tree_entries(root: Path) -> list[tuple[str, str, Path]]:
    reject_linked_skill_path(root)
    entries: list[tuple[str, str, Path]] = [("directory", ".", root)]
    for current, directory_names, file_names in os.walk(root, followlinks=False):
        current_path = Path(current)
        for name in directory_names:
            path = current_path / name
            reject_linked_skill_path(path)
            entries.append(("directory", path.relative_to(root).as_posix(), path))
        for name in file_names:
            path = current_path / name
            reject_linked_skill_path(path)
            if not path.is_file():
                raise EvalError(f"skill tree contains a non-regular file: {path}")
            entries.append(("file", path.relative_to(root).as_posix(), path))
    return sorted(entries, key=lambda item: (item[1], item[0]))


def hash_skill_tree(root: Path) -> str:
    digest = hashlib.sha256()
    for kind, relative, path in tree_entries(root):
        kind_bytes = kind.encode("ascii")
        relative_bytes = relative.encode("utf-8")
        digest.update(len(kind_bytes).to_bytes(4, "big"))
        digest.update(kind_bytes)
        digest.update(len(relative_bytes).to_bytes(8, "big"))
        digest.update(relative_bytes)
        if kind == "file":
            size = path.stat().st_size
            digest.update(size.to_bytes(8, "big"))
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
    return digest.hexdigest()


def parse_variants(raw_variants: list[str]) -> list[dict[str, Any]]:
    variants = []
    names = set()
    for raw in raw_variants:
        if "=" in raw:
            name, raw_path = raw.split("=", 1)
            if not raw_path:
                raise EvalError(f"variant {name!r} has an empty skill path")
            source_path = Path(os.path.abspath(Path(raw_path).expanduser()))
        else:
            name = raw
            source_path = None
        if not VARIANT_NAME_RE.fullmatch(name):
            raise EvalError(
                f"invalid variant name {name!r}; use 1-64 ASCII letters, digits, dot, underscore, or hyphen"
            )
        if name in names:
            raise EvalError(f"duplicate variant name: {name}")
        names.add(name)
        skill_hash = None
        if source_path is not None:
            reject_linked_skill_path(source_path)
            if not source_path.is_dir():
                raise EvalError(f"variant skill path is not a directory: {source_path}")
            skill_hash = hash_skill_tree(source_path)
        variants.append(
            {
                "name": name,
                "source_path": source_path,
                "skill_tree_sha256": skill_hash,
            }
        )
    return variants


def load_suite(path: Path) -> tuple[dict[str, Any], str]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise EvalError(f"cannot read suite {path}: {exc}") from exc
    try:
        suite = strict_json_loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        raise EvalError(f"suite must be valid UTF-8 JSON: {exc}") from exc
    if not isinstance(suite, dict) or not isinstance(suite.get("cases"), list) or not suite["cases"]:
        raise EvalError("suite must be an object with a nonempty cases array")
    skill_name = suite.get("skill_name")
    if not isinstance(skill_name, str) or not re.fullmatch(
        r"[a-z0-9]+(?:-[a-z0-9]+)*", skill_name
    ):
        raise EvalError("suite skill_name must use lowercase letters, digits, and hyphens")
    case_ids = set()
    for index, case in enumerate(suite["cases"]):
        if not isinstance(case, dict):
            raise EvalError(f"suite case {index} must be an object")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            raise EvalError(f"suite case {index} must have a nonempty string id")
        if case_id in case_ids:
            raise EvalError(f"duplicate suite case id: {case_id}")
        case_ids.add(case_id)
        if not isinstance(case.get("query"), str) or not case["query"].strip():
            raise EvalError(f"suite case {case_id!r} must have a nonempty query")
        if type(case.get("should_trigger")) is not bool:
            raise EvalError(f"suite case {case_id!r} should_trigger must be boolean")
        if not isinstance(case.get("rationale"), str) or not case["rationale"].strip():
            raise EvalError(f"suite case {case_id!r} must have a nonempty rationale")
    return suite, hashlib.sha256(raw).hexdigest()


def run_git(arguments: list[str]) -> bytes:
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=ROOT,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise EvalError(f"git {' '.join(arguments)} failed: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr[:STDERR_EXCERPT_LIMIT].decode("utf-8", errors="replace").strip()
        raise EvalError(f"git {' '.join(arguments)} failed: {detail or completed.returncode}")
    return completed.stdout


def update_digest_part(digest: Any, label: bytes, value: bytes) -> None:
    digest.update(len(label).to_bytes(4, "big"))
    digest.update(label)
    digest.update(len(value).to_bytes(8, "big"))
    digest.update(value)


def git_provenance() -> dict[str, Any]:
    commit = run_git(["rev-parse", "HEAD"]).strip().decode("ascii", errors="strict")
    if not re.fullmatch(r"[0-9a-fA-F]{40}", commit):
        raise EvalError("cannot determine git commit: git rev-parse returned invalid output")

    status = run_git(["status", "--porcelain=v1", "-z", "--untracked-files=all"])
    dirty = bool(status)
    worktree_digest = None
    if dirty:
        digest = hashlib.sha256()
        update_digest_part(digest, b"status", status)
        diff = run_git(["diff", "--binary", "--full-index", "--no-ext-diff", "HEAD", "--"])
        update_digest_part(digest, b"tracked-diff", diff)
        untracked = run_git(["ls-files", "--others", "--exclude-standard", "-z"])
        for raw_path in sorted(value for value in untracked.split(b"\0") if value):
            update_digest_part(digest, b"untracked-path", raw_path)
            path = ROOT / os.fsdecode(raw_path)
            if path.is_symlink():
                update_digest_part(digest, b"symlink-target", os.fsencode(os.readlink(path)))
            elif path.is_file():
                update_digest_part(digest, b"file-sha256", hash_file(path).encode("ascii"))
            else:
                raise EvalError(f"untracked git path is not a regular file: {path}")
        worktree_digest = digest.hexdigest()

    return {
        "commit": commit.lower(),
        "dirty": dirty,
        "worktree_diff_sha256": worktree_digest,
    }


def command_file_hashes(command: list[str]) -> list[dict[str, Any]]:
    files = []
    for index, argument in enumerate(command):
        candidate = Path(argument).expanduser()
        if not candidate.is_absolute():
            candidate = ROOT / candidate
        if not candidate.is_file() and index == 0:
            executable = shutil.which(argument)
            if executable is not None:
                candidate = Path(executable)
        if candidate.is_file():
            resolved = candidate.resolve()
            files.append(
                {
                    "argument_index": index,
                    "argument": argument,
                    "path": str(resolved),
                    "sha256": hash_file(resolved),
                }
            )
    return files


def prepare_output(path: Path) -> Path:
    if path.is_symlink():
        raise EvalError(f"output must not be a symlink: {path}")
    if path.exists():
        if not path.is_dir():
            raise EvalError(f"output is not a directory: {path}")
        if any(path.iterdir()):
            raise EvalError(f"output directory must be empty: {path}")
    else:
        path.mkdir(parents=True)
    return path.resolve()


def discovery_skill_paths(path: Path, skill_name: str) -> list[Path]:
    found = []
    for ancestor in (path, *path.parents):
        for skill_root in DISCOVERY_SKILL_ROOTS:
            candidate = ancestor / skill_root / skill_name / "SKILL.md"
            if candidate.is_file():
                found.append(candidate.resolve())
    return sorted(set(found), key=str)


def validate_work_root(path: Path, output: Path, skill_name: str) -> None:
    if path.is_relative_to(ROOT):
        raise EvalError(f"work root must be outside the repository: {path}")
    if path.is_relative_to(output) or output.is_relative_to(path):
        raise EvalError(f"work root and output must not contain one another: {path}")
    discovered = discovery_skill_paths(path, skill_name)
    if discovered:
        joined = ", ".join(str(candidate) for candidate in discovered)
        raise EvalError(
            f"work root has same-name skill discovery ancestors for {skill_name!r}: "
            f"{joined}"
        )


def prepare_work_root(
    requested: Path | None, output: Path, skill_name: str
) -> tuple[Path, bool]:
    owned = requested is None
    if owned:
        path = Path(tempfile.mkdtemp(prefix="boring-backend-eval-"))
    else:
        path = requested.expanduser()
        if path.is_symlink():
            raise EvalError(f"work root must not be a symlink: {path}")
        if path.exists():
            if not path.is_dir():
                raise EvalError(f"work root is not a directory: {path}")
            if any(path.iterdir()):
                raise EvalError(f"work root directory must be empty: {path}")
        else:
            path.mkdir(parents=True)

    resolved = path.resolve()
    try:
        if is_windows_reparse_point(resolved):
            raise EvalError(f"work root must not be a Windows reparse point: {resolved}")
        validate_work_root(resolved, output, skill_name)
    except Exception:
        if owned:
            shutil.rmtree(resolved, ignore_errors=True)
        raise
    return resolved, owned


def archive_file(source: Path, destination: Path, byte_limit: int | None = None) -> None:
    if not source.is_file() or source.is_symlink():
        return
    if byte_limit is not None and source.stat().st_size > byte_limit:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def archive_run(
    work_run_dir: Path,
    report_run_dir: Path,
    artifacts: list[str] | None = None,
) -> None:
    report_run_dir.mkdir(parents=True, exist_ok=True)
    archive_file(work_run_dir / "request.json", report_run_dir / "request.json")
    archive_file(
        work_run_dir / "response.json",
        report_run_dir / "response.json",
        RESPONSE_BYTE_LIMIT,
    )
    archive_file(
        work_run_dir / "runner.stderr",
        report_run_dir / "runner.stderr",
    )
    for relative in artifacts or []:
        source = (work_run_dir / relative).resolve()
        destination = report_run_dir / relative
        archive_file(source, destination)


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        serialized = json.dumps(value, allow_nan=False, indent=2, sort_keys=True) + "\n"
    except (RecursionError, ValueError) as exc:
        raise EvalError(f"cannot serialize JSON output: {exc}") from exc
    temporary.write_text(serialized, encoding="utf-8")
    temporary.replace(path)


def drain_pipe(stream: BinaryIO, collector: BoundedByteCollector) -> None:
    try:
        while True:
            chunk = stream.read(8192)
            if not chunk:
                return
            collector.append(chunk)
    except OSError as exc:
        collector.error = exc
    finally:
        try:
            stream.close()
        except OSError:
            pass


def wait_for_process(process: subprocess.Popen[bytes], timeout: float) -> bool:
    try:
        process.wait(timeout=timeout)
        return True
    except subprocess.TimeoutExpired:
        return False


def wait_for_process_group_exit(process_group: int, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while True:
        try:
            os.killpg(process_group, 0)
        except ProcessLookupError:
            return True
        except PermissionError:
            pass
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.05)


def fallback_terminate_process(process: subprocess.Popen[bytes]) -> list[str]:
    errors = []
    if process.poll() is not None:
        return errors
    try:
        process.terminate()
    except OSError as exc:
        errors.append(f"terminate failed: {exc}")
    if wait_for_process(process, PROCESS_TERMINATE_GRACE_SECONDS):
        return errors
    try:
        process.kill()
    except OSError as exc:
        errors.append(f"kill failed: {exc}")
    if not wait_for_process(process, PROCESS_TERMINATE_GRACE_SECONDS):
        errors.append("process did not exit after kill")
    return errors


def terminate_process_tree(process: subprocess.Popen[bytes]) -> list[str]:
    errors = []
    if os.name == "nt":
        try:
            completed = subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                cwd=ROOT,
                shell=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
            if completed.returncode != 0 and process.poll() is None:
                errors.append(f"taskkill exited {completed.returncode}")
        except (OSError, subprocess.SubprocessError) as exc:
            errors.append(f"taskkill failed: {exc}")
        if not wait_for_process(process, PROCESS_TERMINATE_GRACE_SECONDS):
            errors.extend(fallback_terminate_process(process))
        return errors

    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return errors
    except OSError as exc:
        errors.append(f"process-group terminate failed: {exc}")
        errors.extend(fallback_terminate_process(process))
        return errors
    wait_for_process(process, PROCESS_TERMINATE_GRACE_SECONDS)
    if wait_for_process_group_exit(process.pid, PROCESS_TERMINATE_GRACE_SECONDS):
        return errors
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except OSError as exc:
        errors.append(f"process-group kill failed: {exc}")
        errors.extend(fallback_terminate_process(process))
        return errors
    if not wait_for_process(process, PROCESS_TERMINATE_GRACE_SECONDS):
        errors.append("process group did not exit after kill")
        errors.extend(fallback_terminate_process(process))
    if not wait_for_process_group_exit(process.pid, PROCESS_TERMINATE_GRACE_SECONDS):
        errors.append("process group still exists after kill")
    return errors


def invoke_runner(
    command: list[str],
    request_path: Path,
    response_path: Path,
    cwd: Path,
    timeout_seconds: float,
) -> RunnerResult:
    popen_arguments: dict[str, Any] = {
        "cwd": cwd,
        "shell": False,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.PIPE,
        "bufsize": 0,
    }
    if os.name == "nt":
        popen_arguments["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_arguments["start_new_session"] = True
    try:
        process = subprocess.Popen(
            command + ["--request", str(request_path), "--response", str(response_path)],
            **popen_arguments,
        )
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise EvalError(f"cannot start runner: {exc}") from exc
    if process.stderr is None:
        terminate_process_tree(process)
        raise EvalError("runner stderr pipe was not created")

    collector = BoundedByteCollector(STDERR_EXCERPT_LIMIT)
    stderr_thread = threading.Thread(
        target=drain_pipe,
        args=(process.stderr, collector),
        name="skill-eval-stderr-drain",
        daemon=True,
    )
    stderr_thread.start()
    timed_out = not wait_for_process(process, timeout_seconds)
    cleanup_errors: list[str] = []
    if timed_out:
        cleanup_errors.extend(terminate_process_tree(process))

    stderr_thread.join(STDERR_DRAIN_GRACE_SECONDS)
    drain_incomplete = stderr_thread.is_alive()
    if drain_incomplete:
        cleanup_errors.append("stderr pipe remained open; background descendants are forbidden")
        if not timed_out:
            cleanup_errors.extend(terminate_process_tree(process))
        stderr_thread.join(STDERR_DRAIN_GRACE_SECONDS)
    if collector.error is not None:
        cleanup_errors.append(f"stderr drain failed: {collector.error}")

    returncode = process.returncode if process.returncode is not None else -1
    return RunnerResult(
        returncode=returncode,
        stderr_excerpt=collector.excerpt(),
        stderr_truncated=collector.truncated,
        timed_out=timed_out,
        cleanup_errors=tuple(cleanup_errors),
    )


def write_stderr_excerpt(path: Path, value: str) -> None:
    if value:
        path.write_text(value, encoding="utf-8")
    else:
        path.unlink(missing_ok=True)


def path_has_parent_traversal(value: str) -> bool:
    return ".." in PurePosixPath(value).parts or ".." in PureWindowsPath(value).parts


def validate_artifacts(raw_artifacts: Any, run_dir: Path) -> list[str]:
    if raw_artifacts is None:
        return []
    if not isinstance(raw_artifacts, list):
        raise EvalError("runner response artifacts must be an array")
    if len(raw_artifacts) > ARTIFACT_COUNT_LIMIT:
        raise EvalError(
            f"runner response artifact count exceeds {ARTIFACT_COUNT_LIMIT}"
        )
    normalized = []
    run_root = run_dir.resolve()
    total_bytes = 0
    for value in raw_artifacts:
        if not isinstance(value, str) or not value:
            raise EvalError("runner response artifact paths must be nonempty strings")
        if path_has_parent_traversal(value):
            raise EvalError(f"runner response artifact uses path traversal: {value}")
        native = Path(value)
        if native.is_absolute():
            target = native.resolve()
        elif PureWindowsPath(value).is_absolute() or PurePosixPath(value).is_absolute():
            raise EvalError(f"runner response artifact is outside the run directory: {value}")
        else:
            target = (run_root / native).resolve()
        if not target.is_relative_to(run_root):
            raise EvalError(f"runner response artifact is outside the run directory: {value}")
        if not target.is_file():
            raise EvalError(f"runner response artifact is not a regular file: {value}")
        artifact_bytes = target.stat().st_size
        if artifact_bytes > ARTIFACT_TOTAL_BYTE_LIMIT - total_bytes:
            raise EvalError(
                f"runner response artifact bytes exceed {ARTIFACT_TOTAL_BYTE_LIMIT}"
            )
        total_bytes += artifact_bytes
        normalized.append(target.relative_to(run_root).as_posix())
    return normalized


def read_response_bytes(path: Path) -> bytes:
    with path.open("rb") as handle:
        raw = handle.read(RESPONSE_BYTE_LIMIT + 1)
    if len(raw) > RESPONSE_BYTE_LIMIT:
        raise EvalError(f"runner response exceeds {RESPONSE_BYTE_LIMIT} bytes")
    return raw


def validate_response(path: Path, run_dir: Path) -> dict[str, Any]:
    if not path.exists() or not path.is_file() or path.is_symlink():
        raise EvalError("runner did not write a regular response JSON file")
    if not path.resolve().is_relative_to(run_dir.resolve()):
        raise EvalError("runner response path escaped the run directory")
    try:
        response = strict_json_loads(read_response_bytes(path))
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError, OSError) as exc:
        raise EvalError(f"runner response is not valid JSON: {exc}") from exc
    if not isinstance(response, dict):
        raise EvalError("runner response must be a JSON object")
    unknown_fields = sorted(set(response) - RESPONSE_FIELDS)
    if unknown_fields:
        raise EvalError(f"runner response has unknown fields: {', '.join(unknown_fields)}")

    activation = response.get("activation")
    if activation is not None and type(activation) is not bool:
        raise EvalError("runner response activation must be boolean or null")

    catalogs = response.get("catalogs")
    if catalogs is not None:
        if not isinstance(catalogs, list) or not all(
            isinstance(catalog, str) and catalog for catalog in catalogs
        ):
            raise EvalError("runner response catalogs must be an array of nonempty strings or null")
        if len(catalogs) != len(set(catalogs)):
            raise EvalError("runner response catalogs must not contain duplicates")

    usage = response.get("usage")
    if usage is not None:
        if not isinstance(usage, dict):
            raise EvalError("runner response usage must be an object or null")
        for field, value in usage.items():
            if not isinstance(field, str) or not field:
                raise EvalError("runner response usage fields must be nonempty strings")
            if value is None:
                continue
            if type(value) is not int or not 0 <= value <= USAGE_VALUE_MAX:
                raise EvalError(
                    f"runner response usage.{field} must be null or a nonnegative integer "
                    f"no greater than {USAGE_VALUE_MAX}"
                )

    metadata = response.get("metadata", {})
    if not isinstance(metadata, dict):
        raise EvalError("runner response metadata must be an object")

    isolation = response.get("isolation")
    if not isinstance(isolation, dict):
        raise EvalError("runner response isolation attestation must be an object")
    unknown_isolation_fields = sorted(set(isolation) - ISOLATION_FIELDS)
    if unknown_isolation_fields:
        raise EvalError(
            "runner response isolation has unknown fields: "
            + ", ".join(unknown_isolation_fields)
        )
    if isolation.get("verified") is not True:
        raise EvalError("runner response must attest isolation.verified=true")
    isolation_method = isolation.get("method")
    if not isinstance(isolation_method, str) or not isolation_method.strip():
        raise EvalError("runner response isolation.method must be a nonempty string")
    unexpected_skills = isolation.get("unexpected_same_name_skills")
    if not isinstance(unexpected_skills, list) or not all(
        isinstance(value, str) and value for value in unexpected_skills
    ):
        raise EvalError(
            "runner response isolation.unexpected_same_name_skills must be an array of strings"
        )
    if unexpected_skills:
        raise EvalError(
            "runner reported unexpected same-name skills: " + ", ".join(unexpected_skills)
        )

    return {
        "activation": activation,
        "catalogs": catalogs,
        "usage": usage,
        "artifacts": validate_artifacts(response.get("artifacts", []), run_dir),
        "metadata": metadata,
        "isolation": isolation,
    }


def ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def usage_median(values: list[int]) -> int | float:
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    lower = ordered[midpoint - 1]
    upper = ordered[midpoint]
    return lower + (upper - lower) / 2


def summarize_variant(
    records: list[dict[str, Any]], variant: dict[str, Any]
) -> dict[str, Any]:
    selected = [record for record in records if record["variant"] == variant["name"]]
    observed_activation = [
        record for record in selected if record["response"]["activation"] is not None
    ]
    activation: dict[str, Any] = {
        "observed": len(observed_activation),
        "unknown": len(selected) - len(observed_activation),
        "confusion": None,
        "accuracy": None,
        "precision": None,
        "recall": None,
        "specificity": None,
    }
    if variant["source_path"] is not None:
        true_positive = sum(
            record["expected_activation"] and record["response"]["activation"]
            for record in observed_activation
        )
        true_negative = sum(
            not record["expected_activation"] and not record["response"]["activation"]
            for record in observed_activation
        )
        false_positive = sum(
            not record["expected_activation"] and record["response"]["activation"]
            for record in observed_activation
        )
        false_negative = sum(
            record["expected_activation"] and not record["response"]["activation"]
            for record in observed_activation
        )
        activation.update(
            {
                "confusion": {
                    "true_positive": true_positive,
                    "true_negative": true_negative,
                    "false_positive": false_positive,
                    "false_negative": false_negative,
                },
                "accuracy": ratio(true_positive + true_negative, len(observed_activation)),
                "precision": ratio(true_positive, true_positive + false_positive),
                "recall": ratio(true_positive, true_positive + false_negative),
                "specificity": ratio(true_negative, true_negative + false_positive),
            }
        )

    observed_catalogs = [
        record["response"]["catalogs"]
        for record in selected
        if record["response"]["catalogs"] is not None
    ]
    catalog_counts = Counter(catalog for catalogs in observed_catalogs for catalog in catalogs)
    catalogs = {
        "observed": len(observed_catalogs),
        "unknown": len(selected) - len(observed_catalogs),
        "frequencies": {
            catalog: {
                "count": count,
                "frequency": ratio(count, len(observed_catalogs)),
            }
            for catalog, count in sorted(catalog_counts.items())
        },
    }

    observed_usage = [
        record["response"]["usage"]
        for record in selected
        if record["response"]["usage"] is not None
    ]
    usage_fields = sorted({field for usage in observed_usage for field in usage})
    usage_summary = {
        "observed": len(observed_usage),
        "unknown": len(selected) - len(observed_usage),
        "fields": {},
    }
    for field in usage_fields:
        values = [usage[field] for usage in observed_usage if usage.get(field) is not None]
        usage_summary["fields"][field] = {
            "observed": len(values),
            "median": usage_median(values) if values else None,
        }

    case_summary = {}
    for case_id in sorted({record["case_id"] for record in selected}):
        case_records = [record for record in selected if record["case_id"] == case_id]
        case_activations = [
            record["response"]["activation"]
            for record in case_records
            if record["response"]["activation"] is not None
        ]
        expected = case_records[0]["expected_activation"]
        case_summary[case_id] = {
            "runs": len(case_records),
            "expected_activation": expected if variant["source_path"] is not None else None,
            "activation": {
                "observed": len(case_activations),
                "unknown": len(case_records) - len(case_activations),
                "rate": ratio(sum(case_activations), len(case_activations)),
                "correct_rate": (
                    ratio(sum(value is expected for value in case_activations), len(case_activations))
                    if variant["source_path"] is not None
                    else None
                ),
            },
        }

    return {
        "has_skill": variant["source_path"] is not None,
        "runs": len(selected),
        "activation": activation,
        "catalogs": catalogs,
        "usage": usage_summary,
        "cases": case_summary,
    }


def build_summary(
    records: list[dict[str, Any]],
    variants: list[dict[str, Any]],
    suite_sha256: str | None,
    status: str,
    error: str | None = None,
) -> dict[str, Any]:
    summary = {
        "protocol_version": PROTOCOL_VERSION,
        "status": status,
        "suite_sha256": suite_sha256,
        "total_runs": len(records),
        "variants": {
            variant["name"]: summarize_variant(records, variant) for variant in variants
        },
    }
    if error is not None:
        summary["error"] = error
    return summary


def make_manifest(
    suite_path: Path,
    suite_sha256: str,
    variants: list[dict[str, Any]],
    command: list[str],
    runner_metadata: dict[str, Any],
    work_root: Path,
    work_root_owned: bool,
    skill_name: str,
    seed: int,
    trials: int,
    timeout_seconds: float,
) -> dict[str, Any]:
    return {
        "protocol_version": PROTOCOL_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "suite": {"path": str(suite_path.resolve()), "sha256": suite_sha256},
        "git": git_provenance(),
        "harness": {"path": str(HARNESS_PATH), "sha256": hash_file(HARNESS_PATH)},
        "platform": platform.platform(),
        "python": platform.python_version(),
        "seed": seed,
        "trials": trials,
        "execution": {
            "work_root": str(work_root),
            "auto_cleanup": work_root_owned,
            "runner_cwd": "per-run run directory",
            "skill_name": skill_name,
            "same_name_ancestor_scan": "passed",
        },
        "runner": {
            "command": command,
            "command_files": command_file_hashes(command),
            "metadata": runner_metadata,
            "timeout_seconds": timeout_seconds,
            "stderr_excerpt_limit": STDERR_EXCERPT_LIMIT,
            "response_byte_limit": RESPONSE_BYTE_LIMIT,
            "json_depth_limit": JSON_DEPTH_LIMIT,
            "usage_value_max": USAGE_VALUE_MAX,
            "artifact_count_limit": ARTIFACT_COUNT_LIMIT,
            "artifact_total_byte_limit": ARTIFACT_TOTAL_BYTE_LIMIT,
        },
        "variants": [
            {
                "name": variant["name"],
                "skill_path": (
                    str(variant["source_path"]) if variant["source_path"] is not None else None
                ),
                "skill_tree_sha256": variant["skill_tree_sha256"],
            }
            for variant in variants
        ],
    }


def copy_skill(variant: dict[str, Any], runtime_dir: Path) -> Path | None:
    source = variant["source_path"]
    if source is None:
        return None
    destination = runtime_dir / "skill"
    shutil.copytree(source, destination)
    if hash_skill_tree(destination) != variant["skill_tree_sha256"]:
        raise EvalError(f"skill tree changed while preparing variant {variant['name']!r}")
    return destination


def build_run_schedule(
    cases: list[dict[str, Any]],
    trials: int,
    variants: list[dict[str, Any]],
    seed: int,
) -> list[tuple[dict[str, Any], int, dict[str, Any], int]]:
    generator = random.Random(seed)
    blocks = [(case, trial) for case in cases for trial in range(1, trials + 1)]
    generator.shuffle(blocks)
    schedule = []
    for case, trial in blocks:
        paired_seed = generator.getrandbits(64)
        ordered_variants = list(variants)
        generator.shuffle(ordered_variants)
        schedule.extend(
            (case, trial, variant, paired_seed) for variant in ordered_variants
        )
    return schedule


def run_evaluation(args: argparse.Namespace) -> int:
    output: Path | None = None
    work_root: Path | None = None
    work_root_owned = False
    variants: list[dict[str, Any]] = []
    suite_sha256: str | None = None
    records: list[dict[str, Any]] = []

    try:
        output = prepare_output(args.output)
        if args.trials < 1:
            raise EvalError("trials must be at least 1")
        if not math.isfinite(args.timeout_seconds) or args.timeout_seconds <= 0:
            raise EvalError("timeout seconds must be finite and positive")
        command, runner_metadata = runner_configuration(args)
        variants = parse_variants(args.variant)
        suite, suite_sha256 = load_suite(args.suite)
        skill_name = suite["skill_name"]
        work_root, work_root_owned = prepare_work_root(args.work_root, output, skill_name)
        manifest = make_manifest(
            args.suite,
            suite_sha256,
            variants,
            command,
            runner_metadata,
            work_root,
            work_root_owned,
            skill_name,
            args.seed,
            args.trials,
            args.timeout_seconds,
        )
        report_runs_root = output / "runs"
        report_runs_root.mkdir()
        work_runs_root = work_root / "runs"
        work_runs_root.mkdir()
        write_json(output / "manifest.json", manifest)
        results_path = output / "results.jsonl"
        results_path.touch()
        schedule = build_run_schedule(suite["cases"], args.trials, variants, args.seed)

        with results_path.open("a", encoding="utf-8", newline="\n") as results_file:
            for run_number, (case, trial, variant, run_seed) in enumerate(schedule, start=1):
                run_id = f"run-{run_number:06d}"
                work_run_dir = work_runs_root / run_id
                report_run_dir = report_runs_root / run_id
                if work_run_dir.exists() or report_run_dir.exists():
                    raise EvalError(f"run directory already exists: {run_id}")
                work_run_dir.mkdir()
                workspace = work_run_dir / "workspace"
                runtime = work_run_dir / "runtime"
                workspace.mkdir()
                runtime.mkdir()
                runtime_skill = copy_skill(variant, runtime)
                request = {
                    "protocol_version": PROTOCOL_VERSION,
                    "run_id": run_id,
                    "seed": run_seed,
                    "trial": trial,
                    "query": case["query"],
                    "variant": {
                        "skill_path": str(runtime_skill) if runtime_skill is not None else None,
                    },
                    "isolation": {
                        "skill_name": skill_name,
                        "allowed_skill_path": (
                            str(runtime_skill) if runtime_skill is not None else None
                        ),
                        "require_no_other_same_name_skill": True,
                    },
                    "paths": {
                        "run_dir": str(work_run_dir),
                        "workspace": str(workspace),
                        "runtime": str(runtime),
                    },
                }
                request_path = work_run_dir / "request.json"
                response_path = work_run_dir / "response.json"
                stderr_path = work_run_dir / "runner.stderr"
                write_json(request_path, request)
                try:
                    completed = invoke_runner(
                        command,
                        request_path,
                        response_path,
                        work_run_dir,
                        args.timeout_seconds,
                    )
                    write_stderr_excerpt(stderr_path, completed.stderr_excerpt)
                    detail = f": {completed.stderr_excerpt}" if completed.stderr_excerpt else ""
                    if completed.timed_out:
                        cleanup = (
                            f"; cleanup best effort: {'; '.join(completed.cleanup_errors)}"
                            if completed.cleanup_errors
                            else ""
                        )
                        raise EvalError(f"runner timed out for {run_id}{detail}{cleanup}")
                    if completed.cleanup_errors:
                        raise EvalError(
                            f"runner cleanup failed for {run_id}: "
                            f"{'; '.join(completed.cleanup_errors)}"
                        )
                    if completed.returncode != 0:
                        raise EvalError(
                            f"runner exited {completed.returncode} for {run_id}{detail}"
                        )
                    response = validate_response(response_path, work_run_dir)
                except Exception:
                    archive_run(work_run_dir, report_run_dir)
                    raise
                archive_run(work_run_dir, report_run_dir, response["artifacts"])
                record = {
                    "protocol_version": PROTOCOL_VERSION,
                    "run_id": run_id,
                    "run_dir": report_run_dir.relative_to(output).as_posix(),
                    "variant": variant["name"],
                    "skill_tree_sha256": variant["skill_tree_sha256"],
                    "case_id": case["id"],
                    "trial": trial,
                    "seed": run_seed,
                    "expected_activation": case["should_trigger"],
                    "response": response,
                    "runner": {
                        "returncode": completed.returncode,
                        "stderr_excerpt": completed.stderr_excerpt,
                        "stderr_truncated": completed.stderr_truncated,
                    },
                }
                try:
                    serialized_record = json.dumps(record, allow_nan=False, sort_keys=True) + "\n"
                except (RecursionError, ValueError) as exc:
                    raise EvalError(f"cannot serialize evaluation result: {exc}") from exc
                results_file.write(serialized_record)
                results_file.flush()
                records.append(record)
        write_json(output / "summary.json", build_summary(records, variants, suite_sha256, "ok"))
        return 0
    except (EvalError, OSError, RecursionError, ValueError, subprocess.SubprocessError) as exc:
        error = str(exc) or exc.__class__.__name__
        if output is not None:
            try:
                write_json(
                    output / "summary.json",
                    build_summary(records, variants, suite_sha256, "failed", error),
                )
            except (OSError, ValueError) as summary_error:
                raise EvalError(
                    f"{error}; cannot write failure summary: {summary_error}"
                ) from summary_error
        if isinstance(exc, EvalError):
            raise
        raise EvalError(error) from exc
    finally:
        if work_root_owned and work_root is not None:
            shutil.rmtree(work_root, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    try:
        return run_evaluation(parse_args(argv))
    except (EvalError, OSError, RecursionError, ValueError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
