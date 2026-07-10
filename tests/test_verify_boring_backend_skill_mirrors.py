import contextlib
import importlib.util
import io
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "verify_boring_backend_skill_mirrors.py"


def load_module():
    spec = importlib.util.spec_from_file_location("verify_boring_backend_skill_mirrors", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class VerifyBoringBackendSkillMirrorsTests(unittest.TestCase):
    def write_source_package(self, root: Path) -> Path:
        module = load_module()
        base = root / "skills" / "boring-backend"
        references = base / "references"
        agents = base / "agents"
        references.mkdir(parents=True)
        agents.mkdir()

        links = ", ".join(
            f"[{name}](references/{name})" for name in module.REQUIRED_REFERENCES
        )
        (base / "SKILL.md").write_text(
            "\n".join(
                [
                    "---",
                    "name: boring-backend",
                    (
                        "description: Use for API/service auth, integrity, idempotency, "
                        "and concurrency work; not for UI-only work."
                    ),
                    "license: MIT",
                    "---",
                    "",
                    "# Boring Backend",
                    "",
                    "Modes: Design, Implementation, and Review.",
                    f"References: {links}.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (agents / "openai.yaml").write_text(
            "\n".join(
                [
                    "interface:",
                    '  display_name: "Boring Backend"',
                    '  short_description: "API service reliability checks"',
                    '  default_prompt: "Use $boring-backend for this service task."',
                    "",
                ]
            ),
            encoding="utf-8",
        )

        (references / "core-guard-catalog.md").write_text(
            (
                "# Core Guards\n\n"
                "Check idempotency, atomic concurrency, API status codes, and runnable tests.\n"
            ),
            encoding="utf-8",
        )
        for name in module.REQUIRED_REFERENCES:
            path = references / name
            if not path.exists():
                path.write_text(f"# {name.removesuffix('.md')}\n", encoding="utf-8")

        license_text = "MIT fixture license\n"
        (root / "LICENSE").write_text(license_text, encoding="utf-8")
        (base / "LICENSE").write_text(license_text, encoding="utf-8")
        return base

    def test_source_package_accepts_structural_invariants(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.write_source_package(root)
            issues: list[str] = []

            module.check_source_package(source, issues, root)

            self.assertEqual(issues, [])

    def test_source_references_must_be_local_flat_and_directly_linked(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.write_source_package(root)
            skill_md = source / "SKILL.md"
            skill_md.write_text(
                skill_md.read_text(encoding="utf-8")
                + "Read [outside](../outside/extra.md).\n",
                encoding="utf-8",
            )
            nested = source / "references" / "nested" / "extra.md"
            nested.parent.mkdir()
            nested.write_text("# Nested\n", encoding="utf-8")

            issues: list[str] = []
            module.validate_reference_structure(source, issues)

            self.assertTrue(any("unsupported source reference" in issue for issue in issues))
            self.assertTrue(any("flat Markdown" in issue for issue in issues))

    def test_source_references_reject_backslashes(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.write_source_package(root)
            skill_md = source / "SKILL.md"
            skill_md.write_text(
                skill_md.read_text(encoding="utf-8").replace(
                    "references/core-guard-catalog.md",
                    "references\\core-guard-catalog.md",
                ),
                encoding="utf-8",
            )

            issues: list[str] = []
            module.validate_reference_structure(source, issues)

            self.assertTrue(any("non-portable source reference" in issue for issue in issues))

    def test_source_references_require_core_catalogs_and_no_orphans(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.write_source_package(root)
            missing = source / "references" / "operations-guard-catalog.md"
            missing.unlink()
            orphan = source / "references" / "new-guard-catalog.md"
            orphan.write_text("# New guard\n", encoding="utf-8")

            issues: list[str] = []
            module.validate_reference_structure(source, issues)

            self.assertTrue(any("missing required reference" in issue for issue in issues))
            self.assertTrue(any("not linked directly" in issue for issue in issues))

    def test_openai_metadata_requires_interface_and_skill_selection(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.write_source_package(root)
            metadata = source / "agents" / "openai.yaml"
            metadata.write_text(
                "interface:\n  display_name: Boring Backend\n  short_description: API checks\n",
                encoding="utf-8",
            )

            issues: list[str] = []
            module.validate_openai_yaml(source, issues)

            self.assertTrue(any("interface.default_prompt" in issue for issue in issues))

    def test_openai_metadata_requires_bounded_short_description(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.write_source_package(root)
            metadata = source / "agents" / "openai.yaml"
            metadata.write_text(
                "interface:\n"
                "  display_name: Boring Backend\n"
                "  short_description: Short\n"
                "  default_prompt: Use $boring-backend for this service task.\n",
                encoding="utf-8",
            )

            issues: list[str] = []
            module.validate_openai_yaml(source, issues)

            self.assertTrue(any("25-64 characters" in issue for issue in issues))

    def test_runtime_license_must_match_repository_license(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.write_source_package(root)
            (source / "LICENSE").write_text("different\n", encoding="utf-8")

            issues: list[str] = []
            module.validate_runtime_license(source, root, issues)

            self.assertTrue(any("runtime license differs" in issue for issue in issues))

    def test_check_mirror_flags_only_file_set_and_hash_drift(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            mirror = root / "mirror"
            source.mkdir()
            mirror.mkdir()
            (source / "a.txt").write_text("source\n", encoding="utf-8")

            issues: list[str] = []
            module.check_mirror(source, mirror, issues)
            self.assertTrue(any("file set mismatch" in issue for issue in issues))

            (mirror / "a.txt").write_text("mirror\n", encoding="utf-8")
            issues = []
            module.check_mirror(source, mirror, issues)
            self.assertEqual(len(issues), 1)
            self.assertIn("mirror drift", issues[0])

    def test_main_checks_source_once_and_mirrors_only_for_drift(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "skills" / "boring-backend"
            mirrors = (
                root / ".agents" / "skills" / "boring-backend",
                root / ".claude" / "skills" / "boring-backend",
            )
            with (
                mock.patch.object(module, "check_source_package") as check_source,
                mock.patch.object(module, "check_mirror") as check_mirror,
                contextlib.redirect_stdout(io.StringIO()),
            ):
                result = module.main(root, source, mirrors)

            self.assertEqual(result, 0)
            check_source.assert_called_once_with(source, mock.ANY, root)
            self.assertEqual(check_mirror.call_count, 2)
            checked_mirrors = {call.args[1] for call in check_mirror.call_args_list}
            self.assertEqual(checked_mirrors, set(mirrors))

    def test_main_passes_for_a_synced_package(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.write_source_package(root)
            mirrors = (
                root / ".agents" / "skills" / "boring-backend",
                root / ".claude" / "skills" / "boring-backend",
            )
            for mirror in mirrors:
                shutil.copytree(source, mirror)

            with contextlib.redirect_stdout(io.StringIO()):
                result = module.main(root, source, mirrors)

            self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
