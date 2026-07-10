import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "verify_all.py"


def load_module():
    spec = importlib.util.spec_from_file_location("verify_all", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class VerifyAllTests(unittest.TestCase):
    def test_build_commands_uses_current_interpreter_and_argument_lists(self):
        module = load_module()

        commands = module.build_commands(REPO)

        self.assertEqual(len(commands), 3)
        self.assertTrue(all(command.args[0] == sys.executable for command in commands))
        self.assertEqual(commands[0].args[1:], [str(REPO / "scripts" / "verify_boring_backend_skill_mirrors.py")])
        self.assertEqual(commands[1].args[1:], ["-m", "unittest", "discover", "-s", str(REPO / "tests")])
        self.assertEqual(
            commands[2].args[1:],
            [
                "-B",
                "-m",
                "unittest",
                "discover",
                "-s",
                str(REPO / "reports" / "boring-backend-forward-test-implementation"),
                "-p",
                "test_*.py",
            ],
        )

    def test_main_returns_first_failing_command_code(self):
        module = load_module()

        with mock.patch.object(module.subprocess, "run") as run, mock.patch("builtins.print"):
            run.side_effect = [
                mock.Mock(returncode=0),
                mock.Mock(returncode=7),
                mock.Mock(returncode=0),
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
        requirements_path = REPO / "requirements-dev.txt"
        self.assertTrue(workflow_path.exists(), "missing cross-platform verification workflow")
        self.assertTrue(requirements_path.exists(), "missing development dependency manifest")
        workflow = workflow_path.read_text(encoding="utf-8")
        requirements = requirements_path.read_text(encoding="utf-8")

        for runner in ("ubuntu-latest", "macos-latest", "windows-latest"):
            with self.subTest(runner=runner):
                self.assertIn(runner, workflow)
        self.assertIn("actions/checkout@v6", workflow)
        self.assertIn("actions/setup-python@v6", workflow)
        self.assertIn("python-version: '3.13'", workflow)
        self.assertIn("python -m pip install -r requirements-dev.txt", workflow)
        self.assertIn("python scripts/verify_all.py", workflow)
        self.assertIn("PyYAML", requirements)


if __name__ == "__main__":
    unittest.main()
