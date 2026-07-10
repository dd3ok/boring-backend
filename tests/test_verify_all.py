import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path, PurePosixPath, PureWindowsPath
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


def load_yaml(path: Path):
    return yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


def load_json_object(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"{path} must contain a JSON object")
    return payload


class VerifyAllTests(unittest.TestCase):
    def assert_non_empty_string(self, value, label: str) -> None:
        self.assertIsInstance(value, str, label)
        self.assertTrue(value.strip(), label)

    def assert_relative_existing_path(self, raw_path: str, label: str) -> Path:
        self.assertIsInstance(raw_path, str, label)
        posix_path = PurePosixPath(raw_path.replace("\\", "/"))
        self.assertFalse(posix_path.is_absolute(), label)
        self.assertFalse(PureWindowsPath(raw_path).is_absolute(), label)
        self.assertNotIn("..", posix_path.parts, label)
        target = REPO.joinpath(*posix_path.parts).resolve()
        self.assertTrue(target.is_relative_to(REPO.resolve()), label)
        self.assertTrue(target.exists(), f"{label} points to missing {target}")
        return target

    def test_build_commands_use_official_validator_and_current_interpreter(self):
        module = load_module()

        commands = module.build_commands(REPO)

        self.assertEqual(len(commands), 3)
        self.assertTrue(all(command.args[0] == sys.executable for command in commands))
        self.assertEqual(
            commands[0].args[1:],
            [
                "-m",
                "skills_ref.cli",
                "validate",
                str(REPO / "skills" / "boring-backend"),
            ],
        )
        self.assertEqual(
            commands[1].args[1:],
            [str(REPO / "scripts" / "verify_boring_backend_skill_mirrors.py")],
        )
        self.assertEqual(
            commands[2].args[1:],
            ["-m", "unittest", "discover", "-s", str(REPO / "tests")],
        )

    def test_main_stops_after_each_possible_failing_command(self):
        module = load_module()

        for failure_index in range(3):
            with self.subTest(failure_index=failure_index):
                return_codes = [0, 0, 0]
                return_codes[failure_index] = 7
                with mock.patch.object(module.subprocess, "run") as run, mock.patch(
                    "builtins.print"
                ):
                    run.side_effect = [
                        mock.Mock(returncode=return_code) for return_code in return_codes
                    ]

                    result = module.main()

                self.assertEqual(result, 7)
                self.assertEqual(run.call_count, failure_index + 1)
                self.assertTrue(
                    all(call.kwargs["shell"] is False for call in run.call_args_list)
                )
                self.assertTrue(all(call.kwargs["cwd"] == REPO for call in run.call_args_list))

    def test_dev_dependencies_are_exactly_pinned(self):
        requirements = (REPO / "requirements-dev.txt").read_text(encoding="utf-8")
        pins = {
            line.strip().lower()
            for line in requirements.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }

        self.assertEqual(
            pins,
            {
                "pyyaml==6.0.3",
                "skills-ref==0.1.1",
                "click==8.4.2",
                'colorama==0.4.6; sys_platform == "win32"',
                "python-dateutil==2.9.0.post0",
                "six==1.17.0",
                "strictyaml==1.7.3",
            },
        )

    def test_docs_show_python_launchers_for_supported_platforms(self):
        for path in (REPO / "README.md", REPO / "README.ko.md", REPO / "AGENTS.md"):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn("python3 scripts/verify_all.py", text)
                self.assertIn("py -3 scripts/verify_all.py", text)

    def test_ci_preserves_required_checks_and_adds_supported_python_matrix(self):
        workflow_path = REPO / ".github" / "workflows" / "verify.yml"
        workflow = workflow_path.read_text(encoding="utf-8")
        config = load_yaml(workflow_path)

        self.assertEqual(config["permissions"], {"contents": "read"})
        self.assertEqual(config["on"]["push"]["branches"], ["main"])
        self.assertEqual(config["on"]["push"]["tags"], ["v*"])
        self.assertIn("pull_request", config["on"])
        self.assertIn("cancel-in-progress: true", workflow)

        jobs = config["jobs"]
        self.assertEqual(
            set(jobs),
            {"verify", "verify-minimum-python", "verify-supported-python"},
        )

        primary = jobs["verify"]
        self.assertEqual(primary["name"], "verify (${{ matrix.os }})")
        self.assertEqual(
            primary["strategy"]["matrix"]["os"],
            ["ubuntu-latest", "macos-latest", "windows-latest"],
        )
        self.assertEqual(primary["runs-on"], "${{ matrix.os }}")

        minimum = jobs["verify-minimum-python"]
        self.assertEqual(minimum["name"], "verify-minimum-python")
        self.assertEqual(minimum["runs-on"], "ubuntu-latest")

        supported = jobs["verify-supported-python"]
        self.assertEqual(supported["name"], "verify-supported-python (${{ matrix.python-version }})")
        self.assertEqual(supported["runs-on"], "ubuntu-latest")
        self.assertEqual(supported["strategy"]["matrix"]["python-version"], ["3.12", "3.13"])

        expected_python = {
            "verify": "3.14",
            "verify-minimum-python": "3.11",
            "verify-supported-python": "${{ matrix.python-version }}",
        }
        for job_id, job in jobs.items():
            with self.subTest(job=job_id):
                self.assertEqual(job["timeout-minutes"], "10")
                action_steps = [step for step in job["steps"] if "uses" in step]
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
                    setup_python["with"]["python-version"],
                    expected_python[job_id],
                )
                run_steps = [step["run"] for step in job["steps"] if "run" in step]
                self.assertEqual(
                    run_steps,
                    [
                        "python -m pip install -r requirements-dev.txt",
                        "python scripts/verify_all.py",
                    ],
                )

    def test_readmes_keep_release_install_and_support_range_in_sync(self):
        readmes = [
            (REPO / "README.md").read_text(encoding="utf-8"),
            (REPO / "README.ko.md").read_text(encoding="utf-8"),
        ]
        install_pattern = re.compile(
            r"--repo\s+(\S+)\s+--ref\s+(v\d+\.\d+\.\d+)\s+--path\s+(\S+)"
        )
        support_pattern = re.compile(r"CPython\s+(3\.\d+).*?(3\.\d+)", re.DOTALL)

        installs = []
        support_ranges = []
        for text in readmes:
            install = install_pattern.search(text)
            support = support_pattern.search(text)
            self.assertIsNotNone(install)
            self.assertIsNotNone(support)
            installs.append(install.groups())
            support_ranges.append(support.groups())
            self.assertIn("skills/boring-backend", text)

        self.assertEqual(installs[0], installs[1])
        self.assertEqual(support_ranges[0], support_ranges[1])

    def test_runtime_skill_license_matches_repository_license(self):
        root_license = REPO / "LICENSE"
        runtime_license = REPO / "skills" / "boring-backend" / "LICENSE"

        self.assertTrue(root_license.is_file())
        self.assertTrue(runtime_license.is_file())
        self.assertEqual(
            runtime_license.read_text(encoding="utf-8"),
            root_license.read_text(encoding="utf-8"),
        )

    def test_trigger_eval_cases_have_stable_minimal_schema(self):
        path = REPO / "validation" / "trigger-eval-cases.json"
        data = load_json_object(path)

        self.assertEqual(data.get("schema_version"), 1)
        self.assertEqual(data.get("skill_name"), "boring-backend")
        cases = data.get("cases")
        self.assertIsInstance(cases, list)
        self.assertTrue(cases)
        ids = [case.get("id") for case in cases]
        self.assertEqual(len(ids), len(set(ids)))
        outcomes = set()
        for case in cases:
            with self.subTest(case=case.get("id")):
                self.assert_non_empty_string(case.get("id"), "case.id")
                self.assert_non_empty_string(case.get("query"), "case.query")
                self.assert_non_empty_string(case.get("rationale"), "case.rationale")
                self.assertIsInstance(case.get("should_trigger"), bool)
                outcomes.add(case["should_trigger"])
                self.assertNotIn("boring-backend", case["query"].lower())
        self.assertEqual(outcomes, {False, True})

    def test_behavior_eval_cases_have_expectations_and_safe_paths(self):
        path = REPO / "validation" / "behavior-eval-cases.json"
        self.assertTrue(path.is_file(), f"missing {path}")
        data = load_json_object(path)

        self.assertEqual(data.get("schema_version"), 1)
        self.assertEqual(data.get("skill_name"), "boring-backend")
        cases = data.get("cases")
        self.assertIsInstance(cases, list)
        self.assertTrue(cases)
        ids = [case.get("id") for case in cases]
        self.assertEqual(len(ids), len(set(ids)))
        for case in cases:
            with self.subTest(case=case.get("id")):
                self.assert_non_empty_string(case.get("id"), "case.id")
                self.assert_non_empty_string(case.get("prompt"), "case.prompt")
                expected_behavior = case.get("expected_behavior")
                self.assertIsInstance(expected_behavior, list, "case.expected_behavior")
                self.assertTrue(expected_behavior, "case.expected_behavior")
                self.assertTrue(
                    all(isinstance(value, str) and value.strip() for value in expected_behavior),
                    "case.expected_behavior",
                )
                input_files = case.get("input_files")
                self.assertIsInstance(input_files, list, "case.input_files")
                for index, raw_path in enumerate(input_files):
                    self.assert_relative_existing_path(raw_path, f"case.input_files[{index}]")

    def test_plugin_manifest_has_core_schema_and_safe_component_paths(self):
        manifest_path = REPO / ".codex-plugin" / "plugin.json"
        self.assertTrue(manifest_path.is_file(), f"missing {manifest_path}")
        manifest = load_json_object(manifest_path)

        self.assertEqual(manifest.get("name"), "boring-backend")
        self.assertRegex(manifest.get("version", ""), r"\A(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\Z")
        self.assert_non_empty_string(manifest.get("description"), "description")
        self.assertEqual(manifest.get("license"), "MIT")

        author = manifest.get("author")
        self.assertIsInstance(author, dict)
        self.assert_non_empty_string(author.get("name"), "author.name")

        interface = manifest.get("interface")
        self.assertIsInstance(interface, dict)
        for field in (
            "displayName",
            "shortDescription",
            "longDescription",
            "developerName",
            "category",
        ):
            self.assert_non_empty_string(interface.get(field), f"interface.{field}")
        default_prompt = interface.get("defaultPrompt")
        self.assertIsInstance(default_prompt, list, "interface.defaultPrompt")
        self.assertTrue(default_prompt, "interface.defaultPrompt")
        self.assertTrue(
            all(isinstance(value, str) and value.strip() for value in default_prompt),
            "interface.defaultPrompt",
        )
        capabilities = interface.get("capabilities")
        self.assertIsInstance(capabilities, list)
        self.assertTrue(all(isinstance(value, str) and value.strip() for value in capabilities))

        skills_root = self.assert_relative_existing_path(manifest.get("skills"), "skills")
        self.assertEqual(skills_root, (REPO / "skills").resolve())
        self.assertTrue((skills_root / "boring-backend" / "SKILL.md").is_file())

        for field in ("apps", "mcpServers"):
            value = manifest.get(field)
            if isinstance(value, str):
                self.assert_relative_existing_path(value, field)
        for field in ("composerIcon", "logo", "logoDark"):
            value = interface.get(field)
            if value is not None:
                self.assert_relative_existing_path(value, f"interface.{field}")
        screenshots = interface.get("screenshots", [])
        self.assertIsInstance(screenshots, list, "interface.screenshots")
        for index, raw_path in enumerate(screenshots):
            self.assert_relative_existing_path(raw_path, f"interface.screenshots[{index}]")


if __name__ == "__main__":
    unittest.main()
