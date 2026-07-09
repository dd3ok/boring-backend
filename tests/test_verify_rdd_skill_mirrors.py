import importlib.util
import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "verify_rdd_skill_mirrors.py"


def load_module():
    spec = importlib.util.spec_from_file_location("verify_rdd_skill_mirrors", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class VerifyRddSkillMirrorsTests(unittest.TestCase):
    def write_minimal_skill(self, base: Path, skill: str) -> None:
        references = base / "references"
        agents = base / "agents"
        references.mkdir(parents=True)
        agents.mkdir()
        review_rule = (
            "Operational escalation: performance, cost, migration, observability, or release risk escalates.\n"
            if skill == "rdd-review"
            else ""
        )
        (base / "SKILL.md").write_text(
            "\n".join(
                [
                    "---",
                    f"name: {skill}",
                    "description: Use when validating RDD verifier fixtures.",
                    "---",
                    "",
                    review_rule,
                    "Read `references/guard-catalog.md`.",
                    "Read `references/forward-test-prompts.md`.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (agents / "openai.yaml").write_text(
            "\n".join(
                [
                    "interface:",
                    f'  display_name: "{skill}"',
                    '  short_description: "Validate RDD verifier fixture."',
                    f'  default_prompt: "Use ${skill} to validate this fixture."',
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (references / "guard-catalog.md").write_text(
            "\n".join(
                [
                    "# Guard",
                    "",
                    "| Grade | Meaning |",
                    "|---|---|",
                    "| P3 | Maintainability, package structure, performance/ops risk, or undue complexity |",
                    "",
                    "For first-run experiments, pre-register the same guard list for every variant.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (references / "forward-test-prompts.md").write_text(
            "# Forward\n\n## Learning Feedback Prompt\n\nUse only during skill maintenance.\n",
            encoding="utf-8",
        )

    def test_skill_frontmatter_requires_name_description_and_no_extra_keys(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "rdd-design"
            self.write_minimal_skill(base, "rdd-design")
            (base / "SKILL.md").write_text(
                "\n".join(
                    [
                        "---",
                        "name: wrong-name",
                        "description: Use when validating RDD verifier fixtures.",
                        "extra: not allowed",
                        "---",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            issues: list[str] = []
            module.validate_skill_frontmatter(base, issues)

            self.assertTrue(any("frontmatter name" in issue for issue in issues))
            self.assertTrue(any("extra frontmatter keys" in issue for issue in issues))

    def test_skill_frontmatter_rejects_empty_mapping(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "rdd-design"
            base.mkdir()
            (base / "SKILL.md").write_text("---\n---\n\n# Empty\n", encoding="utf-8")

            issues: list[str] = []
            module.validate_skill_frontmatter(base, issues)

            self.assertTrue(any("frontmatter name" in issue for issue in issues))
            self.assertTrue(any("frontmatter description" in issue for issue in issues))

    def test_skill_frontmatter_allows_standard_optional_keys(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "rdd-design"
            self.write_minimal_skill(base, "rdd-design")
            (base / "SKILL.md").write_text(
                "\n".join(
                    [
                        "---",
                        "name: rdd-design",
                        "description: Use when validating RDD verifier fixtures.",
                        "license: MIT",
                        "allowed-tools:",
                        "  - shell",
                        "metadata:",
                        "  short-description: RDD fixture",
                        "---",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            issues: list[str] = []
            module.validate_skill_frontmatter(base, issues)

            self.assertFalse(issues)

    def test_openai_metadata_requires_valid_short_description_and_prompt(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "rdd-design"
            agents = base / "agents"
            agents.mkdir(parents=True)
            (agents / "openai.yaml").write_text(
                "\n".join(
                    [
                        "interface:",
                        '  display_name: "RDD Design"',
                        '  short_description: "This description is intentionally far too long for the OpenAI skill chip UI"',
                        '  default_prompt: "Use rdd-design to design the contract."',
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            issues: list[str] = []
            module.validate_openai_yaml(base, issues)

            self.assertTrue(any("short_description length" in issue for issue in issues))
            self.assertTrue(any("$rdd-design" in issue for issue in issues))

    def test_openai_metadata_rejects_invalid_yaml(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "rdd-design"
            agents = base / "agents"
            agents.mkdir(parents=True)
            (agents / "openai.yaml").write_text(
                "\n".join(
                    [
                        "interface:",
                        '  display_name: "RDD Design"',
                        '  short_description: "Design reliability contracts before code."',
                        '  default_prompt: "Use $rdd-design to design the contract."',
                        "  broken: [",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            issues: list[str] = []
            module.validate_openai_yaml(base, issues)

            self.assertTrue(any("invalid openai yaml" in issue for issue in issues))

    def test_openai_metadata_requires_interface_mapping_and_strings(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "rdd-design"
            agents = base / "agents"
            agents.mkdir(parents=True)
            (agents / "openai.yaml").write_text(
                "\n".join(
                    [
                        "interface:",
                        "  display_name: 123",
                        '  short_description: ""',
                        "  default_prompt:",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            issues: list[str] = []
            module.validate_openai_yaml(base, issues)

            self.assertTrue(any("interface.display_name" in issue for issue in issues))
            self.assertTrue(any("interface.short_description" in issue for issue in issues))
            self.assertTrue(any("interface.default_prompt" in issue for issue in issues))

    def test_reference_structure_rejects_nested_reference_files_and_links(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "rdd-design"
            nested = base / "references" / "nested"
            nested.mkdir(parents=True)
            (nested / "deep.md").write_text("# Deep\n", encoding="utf-8")
            (base / "SKILL.md").write_text(
                "\n".join(
                    [
                        "---",
                        "name: rdd-design",
                        "description: Use when designing reliability contracts.",
                        "---",
                        "",
                        "Read `references/nested/deep.md`.",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            issues: list[str] = []
            module.validate_reference_structure(base, issues)

            self.assertTrue(any("nested reference file" in issue for issue in issues))
            self.assertTrue(any("one-level references file" in issue for issue in issues))

    def test_reference_structure_checks_markdown_link_targets(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "rdd-design"
            base.mkdir()
            (base / "SKILL.md").write_text(
                "\n".join(
                    [
                        "---",
                        "name: rdd-design",
                        "description: Use when designing reliability contracts.",
                        "---",
                        "",
                        "Read [Missing](references/missing.md).",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            issues: list[str] = []
            module.validate_reference_structure(base, issues)

            self.assertTrue(any("missing reference" in issue for issue in issues))

    def test_reference_structure_rejects_long_files_nested_links_and_path_escape(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "rdd-design"
            references = base / "references"
            references.mkdir(parents=True)
            (base / "SKILL.md").write_text(
                "\n".join(
                    [
                        "---",
                        "name: rdd-design",
                        "description: Use when designing reliability contracts.",
                        "---",
                        "",
                        "Read `../outside.md`.",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            (references / "long.md").write_text("\n".join(["line"] * 101), encoding="utf-8")
            (references / "with-link.md").write_text("[Nested](other.md)\n", encoding="utf-8")

            issues: list[str] = []
            module.validate_reference_structure(base, issues)

            self.assertTrue(any("one-level references file" in issue for issue in issues))
            self.assertTrue(any("reference leaves skill folder" in issue for issue in issues))
            self.assertTrue(any("reference exceeds 100 lines" in issue for issue in issues))
            self.assertTrue(any("nested markdown reference" in issue for issue in issues))

    def test_learning_feedback_prompt_must_stay_in_forward_test_prompts(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "rdd-design"
            references = base / "references"
            references.mkdir(parents=True)
            (references / "operations-guard-catalog.md").write_text(
                "# Operations\n\n## Learning Feedback Prompt\n\nWrong runtime location.\n",
                encoding="utf-8",
            )

            issues: list[str] = []
            module.validate_rdd_semantics(base, issues)

            self.assertTrue(any("Learning Feedback Prompt" in issue for issue in issues))

    def test_rdd_semantics_require_operational_escalation_evidence_levels_and_learning_prompt(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "rdd-review"
            self.write_minimal_skill(base, "rdd-review")
            (base / "SKILL.md").write_text(
                (base / "SKILL.md").read_text(encoding="utf-8").replace("Operational escalation:", "Ops escalation:"),
                encoding="utf-8",
            )
            (base / "references" / "evidence-strength.md").write_text("L0 Static\n", encoding="utf-8")
            (base / "references" / "operations-guard-catalog.md").write_text(
                "## Learning Feedback Lens\n",
                encoding="utf-8",
            )
            (base / "references" / "forward-test-prompts.md").write_text("# Forward\n", encoding="utf-8")

            issues: list[str] = []
            module.validate_rdd_semantics(base, issues)

            self.assertTrue(any("operational escalation" in issue for issue in issues))
            self.assertTrue(any("L1 Unit/domain" in issue for issue in issues))
            self.assertTrue(any("Learning Feedback Lens" in issue for issue in issues))
            self.assertTrue(any("missing Learning Feedback Prompt" in issue for issue in issues))

    def test_check_mirror_flags_file_set_mismatch_and_hash_drift(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
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
            self.assertTrue(any("mirror drift" in issue for issue in issues))

    def test_check_skill_package_flags_stale_and_semantic_failures(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "rdd-design"
            self.write_minimal_skill(base, "rdd-design")
            (base / "SKILL.md").write_text(
                (base / "SKILL.md").read_text(encoding="utf-8")
                + "\nRead `references/operations-guard-catalog.md` for compatibility and backup/restore.\n"
                + "Stale ../rdd-common text and guarded-pragmatic text.\n",
                encoding="utf-8",
            )
            (base / "references" / "guard-catalog.md").write_text(
                "| P3 | Maintainability, package structure, or undue complexity |\n",
                encoding="utf-8",
            )

            issues: list[str] = []
            module.check_skill_package(base, issues)

            self.assertTrue(any("stale pattern" in issue for issue in issues))
            self.assertTrue(any("operations route overlaps" in issue for issue in issues))
            self.assertTrue(any("core P3 severity" in issue for issue in issues))
            self.assertTrue(any("guarded-pragmatic" in issue or "Guarded Pragmatic" in issue for issue in issues))

    def test_main_passes_against_temp_repo_with_synced_mirrors(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            root = Path(tmp)
            source_root = root / "skills"
            mirror_roots = (root / ".agents" / "skills", root / ".claude" / "skills")
            skills = ("rdd-design", "rdd-implementation", "rdd-review")
            for skill in skills:
                self.write_minimal_skill(source_root / skill, skill)
                for mirror_root in mirror_roots:
                    shutil.copytree(source_root / skill, mirror_root / skill)

            old_values = module.ROOT, module.SOURCE_ROOT, module.MIRROR_ROOTS, module.SKILLS
            module.ROOT = root
            module.SOURCE_ROOT = source_root
            module.MIRROR_ROOTS = mirror_roots
            module.SKILLS = skills
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    result = module.main()
            finally:
                module.ROOT, module.SOURCE_ROOT, module.MIRROR_ROOTS, module.SKILLS = old_values

            self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
