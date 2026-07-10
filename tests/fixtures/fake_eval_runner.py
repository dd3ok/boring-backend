#!/usr/bin/env python3
"""Deterministic subprocess fixture for the provider-neutral eval protocol."""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--response", required=True)
    return parser.parse_args()


def parse_tokens(query: str) -> dict[str, str]:
    values = {}
    for token in query.split():
        if "=" in token:
            key, value = token.split("=", 1)
            values[key] = value
    return values


def nullable_bool(value: str | None):
    if value is None or value == "null":
        return None
    return value == "true"


def main() -> int:
    args = parse_args()
    request_path = Path(args.request)
    response_path = Path(args.response)
    request = json.loads(request_path.read_text(encoding="utf-8"))
    forbidden_keys = {"case", "case_id", "labels", "rationale", "should_trigger", "suite"}
    if forbidden_keys.intersection(request):
        print("runner received hidden evaluation semantics", file=sys.stderr)
        return 9

    tokens = parse_tokens(request["query"])
    stderr_bytes = int(tokens.get("stderr_bytes", "0"))
    if stderr_bytes:
        print("x" * stderr_bytes, file=sys.stderr, end="")

    child_marker = tokens.get("spawn_child_marker")
    if child_marker:
        marker_path = request_path.parent / child_marker
        subprocess.Popen(
            [
                sys.executable,
                "-c",
                (
                    "import pathlib,sys,time; time.sleep(0.7); "
                    "pathlib.Path(sys.argv[1]).write_text('alive', encoding='utf-8')"
                ),
                str(marker_path),
            ]
        )
    resistant_marker = tokens.get("spawn_term_resistant_marker")
    if resistant_marker:
        marker_path = request_path.parent / resistant_marker
        subprocess.Popen(
            [
                sys.executable,
                "-c",
                (
                    "import pathlib,signal,sys,time; "
                    "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                    "time.sleep(3.0); "
                    "pathlib.Path(sys.argv[1]).write_text('alive', encoding='utf-8')"
                ),
                str(marker_path),
            ],
        )
    sleep_seconds = float(tokens.get("sleep_seconds", "0"))
    if sleep_seconds:
        time.sleep(sleep_seconds)

    if tokens.get("mode") == "invalid-json":
        response_path.write_text("{", encoding="utf-8")
        return 0
    if tokens.get("mode") == "invalid-response":
        response_path.write_text(json.dumps({"activation": "yes"}), encoding="utf-8")
        return 0
    if tokens.get("mode") == "nonstandard-json":
        response_path.write_text('{"activation": NaN}', encoding="utf-8")
        return 0
    if tokens.get("mode") == "oversized-response":
        response_path.write_text(json.dumps({"metadata": {"padding": "x" * 70000}}), encoding="utf-8")
        return 0
    if tokens.get("mode") == "deep-response":
        deeply_nested = '{"x":' * 5000 + "0" + "}" * 5000
        response_path.write_text('{"metadata":' + deeply_nested + "}", encoding="utf-8")
        return 0
    if tokens.get("mode") == "huge-usage":
        response_path.write_text(
            json.dumps({"usage": {"total_tokens": 10**400}}), encoding="utf-8"
        )
        return 0
    if tokens.get("mode") == "float-usage":
        response_path.write_text(
            json.dumps({"usage": {"total_tokens": 1e308}}), encoding="utf-8"
        )
        return 0
    if tokens.get("mode") == "missing-isolation":
        response_path.write_text(json.dumps({"activation": True}), encoding="utf-8")
        return 0

    catalogs_token = tokens.get("catalogs")
    if catalogs_token is None or catalogs_token == "null":
        catalogs = None
    elif catalogs_token == "":
        catalogs = []
    else:
        catalogs = catalogs_token.split(",")

    if tokens.get("usage") == "null":
        usage = None
    else:
        usage = {}
        for field in ("total_tokens", "cached_input_tokens", "output_tokens"):
            value = tokens.get(field)
            if value is not None:
                usage[field] = None if value == "null" else int(value)

    artifacts = []
    artifact = tokens.get("artifact")
    if artifact:
        artifacts.append(artifact)
        artifact_path = Path(artifact)
        if not artifact_path.is_absolute() and ".." not in artifact_path.parts:
            target = request_path.parent / artifact_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("evidence\n", encoding="utf-8")

    response = {
        "activation": nullable_bool(tokens.get("activation")),
        "catalogs": catalogs,
        "usage": usage,
        "artifacts": artifacts,
        "metadata": {"fixture": "fake-eval-runner", "cwd": str(Path.cwd())},
        "isolation": {
            "verified": True,
            "method": "fixture isolated work root",
            "unexpected_same_name_skills": (
                ["/unexpected/example-skill"]
                if tokens.get("mode") == "unexpected-skill"
                else []
            ),
        },
    }
    response_path.write_text(json.dumps(response), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
