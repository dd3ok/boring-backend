import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

import yaml


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "verify_all.py"


def load_module():
    spec = importlib.util.spec_from_file_location("verify_all", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_yaml(path):
    return yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


class VerifyAllTests(unittest.TestCase):
    def test_build_commands_uses_current_interpreter_and_argument_lists(self):
        module = load_module()

        commands = module.build_commands(REPO)

        self.assertEqual(len(commands), 2)
        self.assertTrue(all(command.args[0] == sys.executable for command in commands))
        self.assertEqual(commands[0].args[1:], [str(REPO / "scripts" / "verify_boring_backend_skill_mirrors.py")])
        self.assertEqual(commands[1].args[1:], ["-m", "unittest", "discover", "-s", str(REPO / "tests")])

    def test_main_returns_first_failing_command_code(self):
        module = load_module()

        with mock.patch.object(module.subprocess, "run") as run, mock.patch("builtins.print"):
            run.side_effect = [
                mock.Mock(returncode=0),
                mock.Mock(returncode=7),
            ]

            result = module.main()

        self.assertEqual(result, 7)
        self.assertEqual(run.call_count, 2)
        self.assertTrue(all(call.kwargs["shell"] is False for call in run.call_args_list))
        self.assertTrue(all(call.kwargs["cwd"] == REPO for call in run.call_args_list))

    def test_docs_show_python_launchers_for_supported_platforms(self):
        for path in (REPO / "README.md", REPO / "README.ko.md", REPO / "AGENTS.md"):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn("python3 scripts/verify_all.py", text)
                self.assertIn("py -3 scripts/verify_all.py", text)

    def test_ci_verifies_supported_platforms_with_declared_dependencies(self):
        workflow_path = REPO / ".github" / "workflows" / "verify.yml"
        dependabot_path = REPO / ".github" / "dependabot.yml"
        requirements_path = REPO / "requirements-dev.txt"
        self.assertTrue(workflow_path.exists(), "missing cross-platform verification workflow")
        self.assertTrue(dependabot_path.exists(), "missing automated dependency updates")
        self.assertTrue(requirements_path.exists(), "missing development dependency manifest")
        workflow = workflow_path.read_text(encoding="utf-8")
        workflow_config = load_yaml(workflow_path)
        dependabot_config = load_yaml(dependabot_path)
        requirements = requirements_path.read_text(encoding="utf-8")

        self.assertEqual(workflow_config["permissions"], {"contents": "read"})
        triggers = workflow_config["on"]
        self.assertEqual(triggers["push"]["branches"], ["main"])
        self.assertIn("pull_request", triggers)
        self.assertIn("concurrency:", workflow)
        self.assertIn("cancel-in-progress: true", workflow)

        jobs = workflow_config["jobs"]
        self.assertEqual(set(jobs), {"verify", "verify-minimum-python"})

        matrix_job = jobs["verify"]
        self.assertEqual(matrix_job["name"], "verify (${{ matrix.os }})")
        self.assertEqual(
            matrix_job["strategy"]["matrix"]["os"],
            ["ubuntu-latest", "macos-latest", "windows-latest"],
        )
        self.assertEqual(matrix_job["runs-on"], "${{ matrix.os }}")

        minimum_job = jobs["verify-minimum-python"]
        self.assertEqual(minimum_job["name"], "verify-minimum-python")
        self.assertEqual(minimum_job["runs-on"], "ubuntu-latest")

        expected_python_versions = {"verify": "3.14", "verify-minimum-python": "3.11"}
        for job_id, job in jobs.items():
            with self.subTest(job=job_id):
                self.assertEqual(job["timeout-minutes"], "10")
                action_steps = [step for step in job["steps"] if "uses" in step]
                self.assertTrue(action_steps)
                for step in action_steps:
                    self.assertRegex(step["uses"], r"\A[^@]+@[0-9a-f]{40}\Z")

                checkout = next(
                    step for step in action_steps if step["uses"].startswith("actions/checkout@")
                )
                self.assertEqual(checkout.get("with", {}).get("persist-credentials"), "false")

                setup_python = next(
                    step for step in action_steps if step["uses"].startswith("actions/setup-python@")
                )
                self.assertEqual(
                    setup_python.get("with", {}).get("python-version"),
                    expected_python_versions[job_id],
                )
                run_steps = [step["run"] for step in job["steps"] if "run" in step]
                self.assertIn("python -m pip install -r requirements-dev.txt", run_steps)
                self.assertIn("python scripts/verify_all.py", run_steps)

        updates = {entry["package-ecosystem"]: entry for entry in dependabot_config["updates"]}
        self.assertEqual(set(updates), {"github-actions", "pip"})
        expected_schedule = {
            "interval": "weekly",
            "day": "monday",
            "time": "09:00",
            "timezone": "Asia/Seoul",
        }
        for ecosystem, update in updates.items():
            with self.subTest(ecosystem=ecosystem):
                self.assertEqual(update["directory"], "/")
                self.assertEqual(update["schedule"], expected_schedule)
                self.assertEqual(update["open-pull-requests-limit"], "5")

        requirement_lines = [
            line.strip() for line in requirements.splitlines() if line.strip() and not line.startswith("#")
        ]
        pyyaml_pins = [line for line in requirement_lines if line.lower().startswith("pyyaml")]
        self.assertEqual(len(pyyaml_pins), 1)
        self.assertRegex(pyyaml_pins[0], r"\APyYAML==[0-9]+(?:\.[0-9]+)+(?:[A-Za-z0-9.+-]*)\Z")

    def test_readmes_declare_supported_cpython_range(self):
        readme = (REPO / "README.md").read_text(encoding="utf-8")
        korean_readme = (REPO / "README.ko.md").read_text(encoding="utf-8")

        self.assertIn("CPython 3.11 through 3.14", readme)
        self.assertIn("Newer CPython versions are unverified", readme)
        self.assertIn("CPython 3.11부터 3.14까지", korean_readme)
        self.assertIn("더 최신 CPython 버전은 검증되지 않았습니다", korean_readme)

    def test_contributor_security_and_pull_request_guidance(self):
        contributing_path = REPO / "CONTRIBUTING.md"
        security_path = REPO / ".github" / "SECURITY.md"
        pull_request_template_path = REPO / ".github" / "pull_request_template.md"

        for path in (contributing_path, security_path, pull_request_template_path):
            with self.subTest(path=path.name):
                self.assertTrue(path.exists())

        contributing = contributing_path.read_text(encoding="utf-8")
        self.assertIn("`skills/boring-backend/`", contributing)
        self.assertIn("`.agents/skills/boring-backend/`", contributing)
        self.assertIn("`.claude/skills/boring-backend/`", contributing)
        self.assertIn("`validation/`", contributing)
        self.assertIn("runtime skill", contributing)
        self.assertIn("python scripts/verify_all.py", contributing)
        self.assertIn("secrets", contributing.lower())

        security = security_path.read_text(encoding="utf-8").lower()
        self.assertIn("private vulnerability reporting", security)
        self.assertIn("do not open a public issue", security)
        self.assertIn("secrets", security)

        pull_request_template = pull_request_template_path.read_text(encoding="utf-8")
        checklist_lines = [
            line.lower() for line in pull_request_template.splitlines() if line.startswith("- [ ]")
        ]
        for required_term in ("source", "mirror", "tests", "evaluation", "runtime", "secrets"):
            with self.subTest(checklist_term=required_term):
                self.assertTrue(any(required_term in line for line in checklist_lines))

    def test_public_package_has_license(self):
        self.assertTrue((REPO / "LICENSE").exists())

    def test_evaluation_assets_stay_lightweight_and_cover_trigger_boundaries(self):
        fairness_path = REPO / "validation" / "experiment-fairness.md"
        trigger_path = REPO / "validation" / "trigger-eval-cases.json"
        forward_test_path = REPO / "validation" / "forward-test-prompts.md"
        runtime_root = REPO / "skills" / "boring-backend"

        self.assertTrue(fairness_path.exists())
        self.assertTrue(trigger_path.exists())
        self.assertTrue(forward_test_path.exists())
        self.assertFalse((runtime_root / "references" / "experiment-reporting.md").exists())
        self.assertTrue((runtime_root / "references" / "handoff-reporting.md").exists())

        fairness = fairness_path.read_text(encoding="utf-8").lower()
        for term in ("clean context", "same prompt", "postmortem traps", "pre-registered guards"):
            with self.subTest(fairness_term=term):
                self.assertIn(term, fairness)

        data = json.loads(trigger_path.read_text(encoding="utf-8"))
        cases = data["cases"]
        ids = [case["id"] for case in cases]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(sum(case["should_trigger"] is True for case in cases), 8)
        self.assertGreaterEqual(sum(case["should_trigger"] is False for case in cases), 8)
        cases_by_id = {case["id"]: case for case in cases}
        self.assertIs(cases_by_id["openapi-nullability-contract"]["should_trigger"], True)
        self.assertIs(cases_by_id["backend-guide-prose-copy"]["should_trigger"], False)
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertIsInstance(case["should_trigger"], bool)
                self.assertTrue(case["query"].strip())
                self.assertTrue(case["rationale"].strip())
                self.assertNotIn("$boring-backend", case["query"])
                self.assertNotIn("boring-backend", case["query"].lower())


if __name__ == "__main__":
    unittest.main()
