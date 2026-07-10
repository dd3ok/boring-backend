from contextlib import redirect_stderr
import hashlib
import importlib.util
import io
import json
import math
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "run_skill_eval.py"
FAKE_RUNNER = REPO / "tests" / "fixtures" / "fake_eval_runner.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_skill_eval", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_suite(root: Path, cases: list[dict]) -> Path:
    path = root / "suite.json"
    path.write_text(
        json.dumps({"skill_name": "example-skill", "purpose": "test", "cases": cases}),
        encoding="utf-8",
    )
    return path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def contains_key(value, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(contains_key(child, key) for child in value.values())
    if isinstance(value, list):
        return any(contains_key(child, key) for child in value)
    return False


class RunSkillEvalTests(unittest.TestCase):
    def run_cli(
        self,
        suite: Path,
        output: Path,
        skill: Path,
        *extra_args: str,
        variants: list[str] | None = None,
        shell_friendly_runner: bool = False,
        runner_script: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        args = [
            sys.executable,
            str(SCRIPT),
            "--suite",
            str(suite),
            "--output",
            str(output),
            "--trials",
            "2",
            "--seed",
            "17",
        ]
        runner_script = runner_script or str(FAKE_RUNNER)
        if shell_friendly_runner:
            args.extend(
                [
                    "--runner-exe",
                    sys.executable,
                    "--runner-arg",
                    runner_script,
                    "--runner-meta",
                    "adapter=fake",
                    "--runner-meta",
                    "model=deterministic",
                ]
            )
        else:
            args.extend(
                [
                    "--runner-command",
                    json.dumps([sys.executable, runner_script]),
                    "--runner-metadata",
                    json.dumps({"adapter": "fake", "model": "deterministic"}),
                ]
            )
        for variant in variants or [f"skilled={skill}", "baseline"]:
            args.extend(["--variant", variant])
        args.extend(extra_args)
        return subprocess.run(args, capture_output=True, text=True, shell=False, cwd=REPO)

    def make_skill(self, root: Path) -> Path:
        skill = root / "skill"
        (skill / "references").mkdir(parents=True)
        (skill / "SKILL.md").write_text("# Example\n", encoding="utf-8")
        (skill / "references" / "guard.md").write_text("guard\n", encoding="utf-8")
        return skill

    def test_repeated_variants_write_provenance_results_and_null_aware_metrics(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self.make_skill(root)
            suite = write_suite(
                root,
                [
                    {
                        "id": "positive",
                        "query": (
                            "activation=true catalogs=core,security "
                            "total_tokens=10 cached_input_tokens=2 artifact=workspace/evidence.txt"
                        ),
                        "should_trigger": True,
                        "rationale": "positive label must stay in the harness",
                    },
                    {
                        "id": "wrong-negative",
                        "query": "activation=true catalogs=core total_tokens=30 cached_input_tokens=null",
                        "should_trigger": False,
                        "rationale": "an ordinary false positive must not fail the harness",
                    },
                    {
                        "id": "unknown",
                        "query": "activation=null catalogs=null usage=null",
                        "should_trigger": True,
                        "rationale": "unknown values are not negative observations",
                    },
                ],
            )
            output = root / "reports" / "eval"

            completed = self.run_cli(suite, output, skill)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            results = read_jsonl(output / "results.jsonl")
            summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))

            self.assertEqual(manifest["suite"]["sha256"], hashlib.sha256(suite.read_bytes()).hexdigest())
            self.assertRegex(manifest["git"]["commit"], r"^[0-9a-f]{40}$")
            self.assertIs(type(manifest["git"]["dirty"]), bool)
            if manifest["git"]["dirty"]:
                self.assertRegex(manifest["git"]["worktree_diff_sha256"], r"^[0-9a-f]{64}$")
            else:
                self.assertIsNone(manifest["git"]["worktree_diff_sha256"])
            self.assertEqual(
                manifest["harness"]["sha256"], hashlib.sha256(SCRIPT.read_bytes()).hexdigest()
            )
            self.assertTrue(manifest["platform"])
            self.assertTrue(manifest["python"])
            self.assertEqual(manifest["seed"], 17)
            self.assertEqual(manifest["trials"], 2)
            self.assertTrue(manifest["execution"]["auto_cleanup"])
            self.assertEqual(manifest["execution"]["runner_cwd"], "per-run run directory")
            self.assertEqual(manifest["execution"]["skill_name"], "example-skill")
            self.assertEqual(manifest["execution"]["same_name_ancestor_scan"], "passed")
            self.assertFalse(Path(manifest["execution"]["work_root"]).exists())
            self.assertEqual(
                manifest["runner"]["command"],
                [str(Path(sys.executable).resolve()), str(FAKE_RUNNER)],
            )
            self.assertEqual(
                manifest["runner"]["metadata"], {"adapter": "fake", "model": "deterministic"}
            )
            command_files = {
                item["argument_index"]: item for item in manifest["runner"]["command_files"]
            }
            self.assertEqual(command_files[0]["sha256"], hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest())
            self.assertEqual(command_files[1]["sha256"], hashlib.sha256(FAKE_RUNNER.read_bytes()).hexdigest())
            variants = {item["name"]: item for item in manifest["variants"]}
            self.assertRegex(variants["skilled"]["skill_tree_sha256"], r"^[0-9a-f]{64}$")
            self.assertIsNone(variants["baseline"]["skill_path"])
            self.assertIsNone(variants["baseline"]["skill_tree_sha256"])

            self.assertEqual(len(results), 12)
            self.assertEqual(len({result["run_id"] for result in results}), 12)
            self.assertTrue(all(result["run_dir"].startswith("runs/run-") for result in results))
            unknown_results = [result for result in results if result["case_id"] == "unknown"]
            self.assertTrue(all(result["response"]["activation"] is None for result in unknown_results))
            self.assertTrue(all(result["response"]["catalogs"] is None for result in unknown_results))
            self.assertTrue(all(result["response"]["usage"] is None for result in unknown_results))
            self.assertTrue(
                all(result["response"]["isolation"]["verified"] for result in results)
            )

            for result in results:
                run_dir = output / result["run_dir"]
                request = json.loads((run_dir / "request.json").read_text(encoding="utf-8"))
                self.assertNotIn("should_trigger", request)
                self.assertNotIn("rationale", request)
                self.assertNotIn("case", request)
                self.assertNotIn("case_id", request)
                self.assertEqual(request["query"], next(
                    case["query"] for case in json.loads(suite.read_text(encoding="utf-8"))["cases"]
                    if case["id"] == result["case_id"]
                ))
                work_run_dir = Path(request["paths"]["run_dir"])
                self.assertFalse(work_run_dir.exists())
                self.assertFalse(work_run_dir.is_relative_to(REPO))
                self.assertFalse(work_run_dir.is_relative_to(output))
                self.assertEqual(
                    request["isolation"]["require_no_other_same_name_skill"], True
                )
                self.assertEqual(request["isolation"]["skill_name"], "example-skill")
                if result["variant"] == "skilled":
                    copied_skill = Path(request["variant"]["skill_path"])
                    self.assertTrue(copied_skill.is_relative_to(work_run_dir))
                    self.assertEqual(
                        request["isolation"]["allowed_skill_path"], str(copied_skill)
                    )
                else:
                    self.assertIsNone(request["variant"]["skill_path"])
                    self.assertIsNone(request["isolation"]["allowed_skill_path"])
                if "artifact=workspace/evidence.txt" in request["query"]:
                    self.assertEqual(
                        (run_dir / "workspace" / "evidence.txt").read_text(encoding="utf-8"),
                        "evidence\n",
                    )
                self.assertFalse((run_dir / "runtime").exists())

            skilled = summary["variants"]["skilled"]
            self.assertEqual(summary["status"], "ok")
            self.assertEqual(summary["total_runs"], 12)
            self.assertEqual(skilled["activation"]["observed"], 4)
            self.assertEqual(skilled["activation"]["unknown"], 2)
            self.assertEqual(
                skilled["activation"]["confusion"],
                {"true_positive": 2, "true_negative": 0, "false_positive": 2, "false_negative": 0},
            )
            self.assertEqual(skilled["activation"]["accuracy"], 0.5)
            self.assertEqual(skilled["activation"]["precision"], 0.5)
            self.assertEqual(skilled["activation"]["recall"], 1.0)
            self.assertEqual(skilled["activation"]["specificity"], 0.0)
            self.assertIsNone(summary["variants"]["baseline"]["activation"]["confusion"])
            self.assertEqual(skilled["catalogs"]["observed"], 4)
            self.assertEqual(skilled["catalogs"]["unknown"], 2)
            self.assertEqual(
                skilled["catalogs"]["frequencies"]["core"], {"count": 4, "frequency": 1.0}
            )
            self.assertEqual(
                skilled["catalogs"]["frequencies"]["security"],
                {"count": 2, "frequency": 0.5},
            )
            self.assertEqual(skilled["usage"]["observed"], 4)
            self.assertEqual(skilled["usage"]["unknown"], 2)
            self.assertEqual(
                skilled["usage"]["fields"]["total_tokens"], {"observed": 4, "median": 20.0}
            )
            self.assertEqual(
                skilled["usage"]["fields"]["cached_input_tokens"],
                {"observed": 2, "median": 2.0},
            )
            self.assertEqual(
                skilled["cases"]["positive"]["activation"],
                {"observed": 2, "unknown": 0, "rate": 1.0, "correct_rate": 1.0},
            )
            self.assertEqual(
                skilled["cases"]["wrong-negative"]["activation"],
                {"observed": 2, "unknown": 0, "rate": 1.0, "correct_rate": 0.0},
            )
            self.assertIsNone(
                summary["variants"]["baseline"]["cases"]["positive"]["expected_activation"]
            )
            self.assertFalse(contains_key(manifest, "cost"))
            self.assertFalse(contains_key(summary, "cost"))

    def test_runner_invocation_uses_argument_array_shell_false_and_json_paths(self):
        module = load_module()
        command = ["runner executable", "adapter.py", "--fixed-option"]
        request = Path("request path.json")
        response = Path("response path.json")
        run_dir = Path("run dir")
        process = mock.Mock(pid=1234, returncode=0)
        process.stderr = io.BytesIO(b"x" * 10000)
        process.wait.return_value = 0

        with mock.patch.object(module.subprocess, "Popen", return_value=process) as popen:
            completed = module.invoke_runner(
                command, request, response, run_dir, timeout_seconds=12
            )

        self.assertEqual(completed.returncode, 0)
        self.assertTrue(completed.stderr_truncated)
        self.assertLessEqual(len(completed.stderr_excerpt.encode("utf-8")), module.STDERR_EXCERPT_LIMIT)
        args, kwargs = popen.call_args
        self.assertEqual(
            args[0], command + ["--request", str(request), "--response", str(response)]
        )
        self.assertEqual(kwargs["cwd"], run_dir)
        self.assertFalse(kwargs["shell"])
        self.assertIs(kwargs["stdout"], subprocess.DEVNULL)
        self.assertIs(kwargs["stderr"], subprocess.PIPE)
        if os.name == "nt":
            self.assertTrue(kwargs["creationflags"] & subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            self.assertTrue(kwargs["start_new_session"])

    def test_shell_friendly_runner_arguments_work_without_json_cli_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self.make_skill(root)
            suite = write_suite(
                root,
                [
                    {
                        "id": "shell-friendly",
                        "query": "activation=true",
                        "should_trigger": True,
                        "rationale": "runner arguments must work in PowerShell and POSIX shells",
                    }
                ],
            )
            output = root / "output"

            completed = self.run_cli(
                suite,
                output,
                skill,
                variants=[f"skilled={skill}"],
                shell_friendly_runner=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(
                manifest["runner"]["command"],
                [str(Path(sys.executable).resolve()), str(FAKE_RUNNER)],
            )
            self.assertEqual(
                manifest["runner"]["metadata"],
                {"adapter": "fake", "model": "deterministic"},
            )

    def test_relative_adapter_path_is_resolved_before_per_run_launch_and_hashed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self.make_skill(root)
            suite = write_suite(
                root,
                [
                    {
                        "id": "relative-adapter",
                        "query": "activation=true",
                        "should_trigger": True,
                        "rationale": "relative adapter files resolve before the per-run launch",
                    }
                ],
            )
            output = root / "output"

            completed = self.run_cli(
                suite,
                output,
                skill,
                variants=[f"skilled={skill}"],
                shell_friendly_runner=True,
                runner_script="tests/fixtures/fake_eval_runner.py",
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            command_file = next(
                item
                for item in manifest["runner"]["command_files"]
                if item["argument_index"] == 1
            )
            self.assertEqual(Path(command_file["path"]), FAKE_RUNNER)
            self.assertEqual(
                command_file["sha256"], hashlib.sha256(FAKE_RUNNER.read_bytes()).hexdigest()
            )
            self.assertEqual(manifest["runner"]["command"][1], str(FAKE_RUNNER))

    def test_explicit_isolated_work_root_is_preserved_and_used_as_runner_cwd(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self.make_skill(root)
            suite = write_suite(
                root,
                [
                    {
                        "id": "explicit-work-root",
                        "query": "activation=true",
                        "should_trigger": True,
                        "rationale": "explicit execution roots support retained debugging artifacts",
                    }
                ],
            )
            output = root / "output"
            work_root = root / "isolated-work"

            completed = self.run_cli(
                suite,
                output,
                skill,
                "--work-root",
                str(work_root),
                variants=[f"skilled={skill}"],
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            result = read_jsonl(output / "results.jsonl")[0]
            self.assertFalse(manifest["execution"]["auto_cleanup"])
            self.assertEqual(Path(manifest["execution"]["work_root"]), work_root.resolve())
            self.assertTrue(work_root.is_dir())
            work_run_dir = work_root / "runs" / result["run_id"]
            self.assertEqual(
                Path(result["response"]["metadata"]["cwd"]).resolve(),
                work_run_dir.resolve(),
            )

    def test_rejects_work_root_with_same_name_project_skill_ancestor(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self.make_skill(root)
            suite = write_suite(
                root,
                [
                    {
                        "id": "contaminated-work-root",
                        "query": "activation=true",
                        "should_trigger": True,
                        "rationale": "same-name ancestor skills invalidate a no-skill baseline",
                    }
                ],
            )
            contaminating_skill = root / ".agents" / "skills" / "example-skill"
            contaminating_skill.mkdir(parents=True)
            (contaminating_skill / "SKILL.md").write_text("# Contaminating skill\n", encoding="utf-8")
            output = root / "output"
            work_root = root / "isolated-work"

            completed = self.run_cli(
                suite,
                output,
                skill,
                "--work-root",
                str(work_root),
                variants=[f"skilled={skill}", "baseline"],
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("same-name skill discovery ancestors", completed.stderr)
            self.assertIn(str((contaminating_skill / "SKILL.md").resolve()), completed.stderr)

    def test_rejects_work_root_inside_the_repository_even_for_another_skill(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "output"
            with self.assertRaisesRegex(module.EvalError, "outside the repository"):
                module.validate_work_root(
                    REPO / "reports" / "work",
                    output,
                    "another-skill",
                )

    def test_successful_stderr_is_capped_in_results(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self.make_skill(root)
            suite = write_suite(
                root,
                [
                    {
                        "id": "stderr",
                        "query": "activation=false catalogs= usage=null stderr_bytes=10000",
                        "should_trigger": False,
                        "rationale": "exercise stderr capture",
                    }
                ],
            )
            output = root / "output"

            completed = self.run_cli(suite, output, skill, variants=[f"skilled={skill}"])

            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = read_jsonl(output / "results.jsonl")[0]
            self.assertTrue(result["runner"]["stderr_truncated"])
            self.assertLessEqual(len(result["runner"]["stderr_excerpt"]), 2100)
            self.assertTrue(result["runner"]["stderr_excerpt"].endswith("[truncated]"))
            run_dir = output / result["run_dir"]
            self.assertLessEqual((run_dir / "runner.stderr").stat().st_size, 2100)

    def test_timeout_drains_bounded_stderr_and_terminates_descendants_best_effort(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self.make_skill(root)
            suite = write_suite(
                root,
                [
                    {
                        "id": "timeout",
                        "query": (
                            "activation=true stderr_bytes=10000 sleep_seconds=5 "
                            "spawn_child_marker=child-alive.txt"
                        ),
                        "should_trigger": True,
                        "rationale": "timeout cleanup covers the adapter process tree",
                    }
                ],
            )
            output = root / "output"

            completed = self.run_cli(
                suite,
                output,
                skill,
                "--timeout-seconds",
                "0.2",
                variants=[f"skilled={skill}"],
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("timed out", completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)
            stderr_path = output / "runs" / "run-000001" / "runner.stderr"
            if stderr_path.exists():
                self.assertLessEqual(stderr_path.stat().st_size, 2100)
            time.sleep(0.9)
            self.assertFalse((stderr_path.parent / "child-alive.txt").exists())

    @unittest.skipIf(os.name == "nt", "POSIX process-group behavior")
    def test_timeout_kills_sigterm_resistant_process_group_descendant(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self.make_skill(root)
            suite = write_suite(
                root,
                [
                    {
                        "id": "resistant-timeout",
                        "query": (
                            "activation=true sleep_seconds=5 "
                            "spawn_term_resistant_marker=resistant-child-alive.txt"
                        ),
                        "should_trigger": True,
                        "rationale": "SIGKILL follows the process-group grace period",
                    }
                ],
            )
            output = root / "output"

            completed = self.run_cli(
                suite,
                output,
                skill,
                "--timeout-seconds",
                "0.2",
                variants=[f"skilled={skill}"],
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("timed out", completed.stderr)
            marker = output / "runs" / "run-000001" / "resistant-child-alive.txt"
            time.sleep(3.3)
            self.assertFalse(marker.exists())

    def test_invalid_runner_json_is_a_protocol_failure_with_failure_summary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self.make_skill(root)
            suite = write_suite(
                root,
                [
                    {
                        "id": "invalid-json",
                        "query": "mode=invalid-json stderr_bytes=10000",
                        "should_trigger": True,
                        "rationale": "invalid JSON is not an activation miss",
                    }
                ],
            )
            output = root / "output"

            completed = self.run_cli(suite, output, skill, variants=[f"skilled={skill}"])

            self.assertNotEqual(completed.returncode, 0)
            self.assertTrue((output / "manifest.json").is_file())
            self.assertTrue((output / "results.jsonl").is_file())
            summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["status"], "failed")
            self.assertIn("valid JSON", summary["error"])
            self.assertLessEqual(len(completed.stderr), 2300)

    def test_missing_or_contaminated_isolation_attestation_is_a_protocol_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self.make_skill(root)
            for mode, expected in (
                ("missing-isolation", "isolation attestation"),
                ("unexpected-skill", "unexpected same-name skills"),
            ):
                with self.subTest(mode=mode):
                    suite = write_suite(
                        root,
                        [
                            {
                                "id": mode,
                                "query": f"activation=true mode={mode}",
                                "should_trigger": True,
                                "rationale": "adapter isolation must be explicitly attested",
                            }
                        ],
                    )
                    output = root / f"output-{mode}"

                    completed = self.run_cli(
                        suite,
                        output,
                        skill,
                        variants=[f"skilled={skill}"],
                    )

                    self.assertNotEqual(completed.returncode, 0)
                    self.assertIn(expected, completed.stderr)
                    summary = json.loads(
                        (output / "summary.json").read_text(encoding="utf-8")
                    )
                    self.assertEqual(summary["status"], "failed")

    def test_invalid_response_field_type_is_a_protocol_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self.make_skill(root)
            suite = write_suite(
                root,
                [
                    {
                        "id": "invalid-response",
                        "query": "mode=invalid-response",
                        "should_trigger": True,
                        "rationale": "activation must be bool or null",
                    }
                ],
            )

            completed = self.run_cli(
                suite, root / "output", skill, variants=[f"skilled={skill}"]
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("activation", completed.stderr)

    def test_nonstandard_json_constant_is_a_protocol_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self.make_skill(root)
            suite = write_suite(
                root,
                [
                    {
                        "id": "nonstandard-json",
                        "query": "mode=nonstandard-json",
                        "should_trigger": True,
                        "rationale": "NaN is not valid JSON",
                    }
                ],
            )

            completed = self.run_cli(
                suite, root / "output", skill, variants=[f"skilled={skill}"]
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("valid JSON", completed.stderr)

    def test_rejects_oversized_runner_response(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self.make_skill(root)
            suite = write_suite(
                root,
                [
                    {
                        "id": "oversized-response",
                        "query": "mode=oversized-response",
                        "should_trigger": True,
                        "rationale": "response files are byte bounded",
                    }
                ],
            )

            completed = self.run_cli(
                suite, root / "output", skill, variants=[f"skilled={skill}"]
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("exceeds", completed.stderr)

    def test_deeply_nested_response_is_a_controlled_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self.make_skill(root)
            suite = write_suite(
                root,
                [
                    {
                        "id": "deep-response",
                        "query": "mode=deep-response",
                        "should_trigger": True,
                        "rationale": "response nesting is controlled",
                    }
                ],
            )
            output = root / "output"

            completed = self.run_cli(
                suite, output, skill, variants=[f"skilled={skill}"]
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertNotIn("Traceback", completed.stderr)
            summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["status"], "failed")
            self.assertIn("nesting", summary["error"])

    def test_response_reader_uses_one_bounded_binary_read(self):
        module = load_module()
        path = mock.Mock(spec=Path)
        opened = mock.mock_open(read_data=b"{}")
        path.open = opened

        raw = module.read_response_bytes(path)

        self.assertEqual(raw, b"{}")
        opened.assert_called_once_with("rb")
        opened().read.assert_called_once_with(module.RESPONSE_BYTE_LIMIT + 1)

    def test_rejects_usage_values_outside_bounded_integer_contract(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self.make_skill(root)
            for mode in ("huge-usage", "float-usage"):
                with self.subTest(mode=mode):
                    suite = write_suite(
                        root,
                        [
                            {
                                "id": mode,
                                "query": f"mode={mode}",
                                "should_trigger": True,
                                "rationale": "usage values are bounded integers",
                            }
                        ],
                    )
                    output = root / mode

                    completed = self.run_cli(
                        suite, output, skill, variants=[f"skilled={skill}"]
                    )

                    self.assertNotEqual(completed.returncode, 0)
                    self.assertIn("usage.total_tokens", completed.stderr)
                    self.assertNotIn("Traceback", completed.stderr)

    def test_maximum_usage_values_aggregate_to_a_finite_median(self):
        module = load_module()

        median = module.usage_median(
            [module.USAGE_VALUE_MAX - 1, module.USAGE_VALUE_MAX]
        )

        self.assertTrue(math.isfinite(median))
        self.assertGreaterEqual(median, module.USAGE_VALUE_MAX - 1)
        self.assertLessEqual(median, module.USAGE_VALUE_MAX)

    def test_rejects_declared_artifact_outside_its_run_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self.make_skill(root)
            suite = write_suite(
                root,
                [
                    {
                        "id": "outside-artifact",
                        "query": "activation=true catalogs=core usage=null artifact=../escape.txt",
                        "should_trigger": True,
                        "rationale": "artifact traversal is a protocol failure",
                    }
                ],
            )
            output = root / "output"

            completed = self.run_cli(suite, output, skill, variants=[f"skilled={skill}"])

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("artifact", completed.stderr.lower())
            self.assertFalse((output / "runs" / "escape.txt").exists())

    def test_caps_declared_artifact_count_and_total_bytes(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            too_many = [f"artifact-{index}.txt" for index in range(module.ARTIFACT_COUNT_LIMIT + 1)]
            with self.assertRaisesRegex(module.EvalError, "artifact count"):
                module.validate_artifacts(too_many, run_dir)

            oversized = run_dir / "oversized.bin"
            with oversized.open("wb") as handle:
                handle.truncate(module.ARTIFACT_TOTAL_BYTE_LIMIT + 1)
            with self.assertRaisesRegex(module.EvalError, "artifact bytes"):
                module.validate_artifacts([oversized.name], run_dir)

    def test_case_trial_blocks_are_deterministic_interleaved_and_seed_paired(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self.make_skill(root)
            suite = write_suite(
                root,
                [
                    {
                        "id": "first",
                        "query": "activation=true",
                        "should_trigger": True,
                        "rationale": "first schedule block",
                    },
                    {
                        "id": "second",
                        "query": "activation=false",
                        "should_trigger": False,
                        "rationale": "second schedule block",
                    },
                ],
            )
            variants = [f"alpha={skill}", f"beta={skill}", "baseline"]
            schedules = []

            for name in ("one", "two"):
                output = root / name
                completed = self.run_cli(suite, output, skill, variants=variants)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                results = read_jsonl(output / "results.jsonl")
                schedule = [
                    (result["case_id"], result["trial"], result["variant"], result["seed"])
                    for result in results
                ]
                schedules.append(schedule)
                block_orders = []
                for offset in range(0, len(results), len(variants)):
                    block = results[offset : offset + len(variants)]
                    self.assertEqual(len({(item["case_id"], item["trial"]) for item in block}), 1)
                    self.assertEqual(len({item["seed"] for item in block}), 1)
                    self.assertEqual(
                        {item["variant"] for item in block}, {"alpha", "beta", "baseline"}
                    )
                    block_orders.append([item["variant"] for item in block])
                self.assertTrue(any(order != ["alpha", "beta", "baseline"] for order in block_orders))

            self.assertEqual(schedules[0], schedules[1])

    def test_rejects_traversal_variant_name_before_running(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self.make_skill(root)
            suite = write_suite(
                root,
                [
                    {
                        "id": "case",
                        "query": "activation=true",
                        "should_trigger": True,
                        "rationale": "test",
                    }
                ],
            )

            completed = self.run_cli(suite, root / "output", skill, variants=[f"../escape={skill}"])

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("variant name", completed.stderr.lower())
            self.assertFalse((root / "escape").exists())

    def test_rejects_windows_reparse_skill_path_without_creating_a_junction(self):
        module = load_module()
        fake_stat = mock.Mock(st_file_attributes=0x400)
        with mock.patch.object(module.os, "lstat", return_value=fake_stat):
            self.assertTrue(module.is_windows_reparse_point(Path("skill")))

        with tempfile.TemporaryDirectory() as temp_dir:
            skill = self.make_skill(Path(temp_dir))
            with mock.patch.object(module, "is_windows_reparse_point", return_value=True):
                with self.assertRaisesRegex(module.EvalError, "reparse"):
                    module.parse_variants([f"skilled={skill}"])

    def test_preflight_failure_writes_summary_without_traceback(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self.make_skill(root)
            suite = root / "invalid-suite.json"
            suite.write_text("{", encoding="utf-8")
            output = root / "output"

            completed = self.run_cli(suite, output, skill, variants=[f"skilled={skill}"])

            self.assertNotEqual(completed.returncode, 0)
            self.assertNotIn("Traceback", completed.stderr)
            summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["status"], "failed")
            self.assertEqual(summary["total_runs"], 0)
            self.assertIn("suite", summary["error"])

    def test_deeply_nested_json_is_a_controlled_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self.make_skill(root)
            suite = root / "deep-suite.json"
            deeply_nested_case = '{"x":' * 5000 + "0" + "}" * 5000
            suite.write_text(
                '{"cases":[' + deeply_nested_case + "]}",
                encoding="utf-8",
            )
            output = root / "output"

            completed = self.run_cli(suite, output, skill, variants=[f"skilled={skill}"])

            self.assertNotEqual(completed.returncode, 0)
            self.assertNotIn("Traceback", completed.stderr)
            summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["status"], "failed")
            self.assertIn("nesting", summary["error"])

    def test_main_converts_unexpected_preflight_failures_to_controlled_errors(self):
        module = load_module()
        stderr = io.StringIO()
        with (
            mock.patch.object(module, "parse_args", return_value=mock.Mock()),
            mock.patch.object(module, "run_evaluation", side_effect=ValueError("preflight failed")),
            redirect_stderr(stderr),
        ):
            returncode = module.main([])

        self.assertEqual(returncode, 2)
        self.assertIn("preflight failed", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_rejects_nonempty_output_to_preserve_existing_reports(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = self.make_skill(root)
            suite = write_suite(
                root,
                [
                    {
                        "id": "case",
                        "query": "activation=true",
                        "should_trigger": True,
                        "rationale": "test",
                    }
                ],
            )
            output = root / "output"
            output.mkdir()
            sentinel = output / "keep.txt"
            sentinel.write_text("keep", encoding="utf-8")

            completed = self.run_cli(suite, output, skill, variants=[f"skilled={skill}"])

            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()
