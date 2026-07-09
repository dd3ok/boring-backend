import contextlib
import importlib.util
import io
import shutil
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "verify_boring_backend_skill_mirrors.py"


def load_module():
    spec = importlib.util.spec_from_file_location("verify_boring_backend_skill_mirrors", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class VerifyBoringBackendSkillMirrorsTests(unittest.TestCase):
    def test_runtime_routes_ordinary_subagents_to_a_small_reference(self):
        skill_md = (REPO / "skills" / "boring-backend" / "SKILL.md").read_text(encoding="utf-8")
        references = REPO / "skills" / "boring-backend" / "references"
        experiment_text = (references / "experiment-reporting.md").read_text(encoding="utf-8")
        subagent_path = references / "subagent-delegation.md"

        self.assertIn("references/subagent-delegation.md", skill_md)
        self.assertTrue(subagent_path.exists())
        self.assertNotIn("Subagent Prompt Boundary", experiment_text)
        self.assertLessEqual(len(subagent_path.read_text(encoding="utf-8").split()), 70)

    def test_runtime_routes_token_telemetry_out_of_core_routing(self):
        skill_md = (REPO / "skills" / "boring-backend" / "SKILL.md").read_text(encoding="utf-8")
        references = REPO / "skills" / "boring-backend" / "references"
        core_routing = (references / "core-guard-routing.md").read_text(encoding="utf-8")
        token_reporting = references / "token-reporting.md"

        self.assertIn("references/token-reporting.md", skill_md)
        self.assertTrue(token_reporting.exists())
        self.assertNotIn("## Token Reporting", core_routing)
        self.assertLessEqual(len(token_reporting.read_text(encoding="utf-8").split()), 70)

    def test_runtime_links_every_reference_directly_from_skill_md(self):
        skill_md = (REPO / "skills" / "boring-backend" / "SKILL.md").read_text(encoding="utf-8")
        references = REPO / "skills" / "boring-backend" / "references"

        for reference in references.glob("*.md"):
            with self.subTest(reference=reference.name):
                self.assertIn(f"references/{reference.name}", skill_md)

    def test_semantics_rejects_a_reference_only_reachable_through_another_reference(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "boring-backend"
            self.write_minimal_skill(base)
            skill_md = base / "SKILL.md"
            skill_md.write_text(
                skill_md.read_text(encoding="utf-8").replace(
                    "Read `references/core-guard-catalog.md`.\n",
                    "",
                ),
                encoding="utf-8",
            )

            issues: list[str] = []
            module.validate_boring_backend_semantics(base, issues)

            self.assertTrue(any("linked directly" in issue for issue in issues))

    def test_semantics_rejects_routing_ordinary_subagents_to_experiment_reporting(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "boring-backend"
            self.write_minimal_skill(base)
            skill_md = base / "SKILL.md"
            skill_md.write_text(
                skill_md.read_text(encoding="utf-8")
                .replace("Read `references/subagent-delegation.md` before ordinary subagent delegation.\n", "")
                .replace(
                    "Read `references/experiment-reporting.md` for experiment first attempts, guarded-run comparisons, handoffs, or multi-phase runs.",
                    "Read `references/experiment-reporting.md` before subagent delegation or first-attempt, multi-phase, handoff, and guarded-run comparison experiments.",
                ),
                encoding="utf-8",
            )

            issues: list[str] = []
            module.validate_boring_backend_semantics(base, issues)

            self.assertTrue(any("separate subagent delegation reference" in issue for issue in issues))

    def write_minimal_skill(self, base: Path, skill: str = "boring-backend") -> None:
        references = base / "references"
        agents = base / "agents"
        references.mkdir(parents=True)
        agents.mkdir()
        (base / "SKILL.md").write_text(
            "\n".join(
                [
                    "---",
                    f"name: {skill}",
                    "description: Use when validating boring-backend verifier fixtures.",
                    "---",
                    "",
                    "Operational escalation: performance, cost, migration, observability, or release risk escalates.",
                    "Read `references/core-guard-routing.md`.",
                    "Read `references/subagent-delegation.md` before ordinary subagent delegation.",
                    "Read `references/experiment-reporting.md` for experiment first attempts, guarded-run comparisons, handoffs, or multi-phase runs.",
                    "When token telemetry exists, read `references/token-reporting.md`.",
                    "Read `references/core-guard-catalog.md`.",
                    "Use a production-evidence run only when L4 evidence is requested.",
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
                    '  short_description: "Validate boring-backend verifier fixture."',
                    f'  default_prompt: "Use ${skill} to validate this fixture."',
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (references / "core-guard-catalog.md").write_text(
            "\n".join(
                [
                    "# Guard",
                    "",
                    "| Grade | Meaning |",
                    "|---|---|",
                    "| P3 | Maintainability, package structure, performance/ops risk, or undue complexity |",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (references / "core-guard-routing.md").write_text(
            "\n".join(
                [
                    "# Core Guard Routing",
                    "",
                    "Read `core-guard-catalog.md` for core behavior.",
                    "Route public field binding/mass assignment, CORS/TLS, and untrusted third-party responses to `security-guard-catalog.md`.",
                    "Use a production-evidence run only when production-ready evidence is requested.",
                    "L0 Static",
                    "L1 Unit/domain",
                    "L2 Integration",
                    "L3 Risk-specific",
                    "L4 Production-readiness",
                    "Use `catalog_route` to name why each non-default catalog was loaded.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (references / "token-reporting.md").write_text(
            "\n".join(
                [
                    "# Token Reporting",
                    "",
                    "Report total_tokens, input_tokens, cached_input_tokens, cache_write_tokens, noncached_input_tokens = input - cached, output_tokens, and reasoning_output_tokens.",
                    "Cache writes are input; do not add them to totals.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (references / "experiment-reporting.md").write_text(
            "\n".join(
                [
                    "# Experiment Reporting",
                    "",
                    "Use this file for Boring Backend experiment first attempts, guarded-run comparisons, handoffs, or multi-phase runs.",
                    "",
                    "## Handoff Index",
                    "",
                    "Write `reports/handoffs/<task>-first-handoff.json` as a handoff index.",
                    "",
                    "- `claim_id`",
                    "- `claim_summary`",
                    "- `file:line`",
                    "- `evidence_path`",
                    "- `command_exit`",
                    "- `known_gap`",
                    "- `token_usage`",
                    "",
                    "Use handoff-first review. Open the full first report only for a P0-P2 claim that cannot be resolved from the handoff index and cited evidence.",
                    "",
                    "## Delta Output",
                    "",
                    "Reference claim IDs and restate only changed assumptions, disputed claims, P0-P2 findings, unchecked evidence, and new commands/results.",
                    "",
                    "## Fairness",
                    "",
                    "First-run experiments must not receive postmortem traps. Use the same pre-registered guard list for every variant.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (references / "subagent-delegation.md").write_text(
            "\n".join(
                [
                    "# Subagent Delegation",
                    "",
                    "Pass only task-local context: the user request, mode, allowed catalogs, required evidence commands, and any handoff or changed-file paths.",
                    "Do not paste prior reports, transcripts, or catalog text.",
                    "When telemetry is requested, report only the subagent's own `token_usage` once.",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    def test_skill_frontmatter_requires_name_description_and_no_extra_keys(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "boring-backend"
            self.write_minimal_skill(base)
            (base / "SKILL.md").write_text(
                "\n".join(
                    [
                        "---",
                        "name: wrong-name",
                        "description: Use when validating boring-backend verifier fixtures.",
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
            base = Path(tmp) / "boring-backend"
            base.mkdir()
            (base / "SKILL.md").write_text("---\n---\n\n# Empty\n", encoding="utf-8")

            issues: list[str] = []
            module.validate_skill_frontmatter(base, issues)

            self.assertTrue(any("frontmatter name" in issue for issue in issues))
            self.assertTrue(any("frontmatter description" in issue for issue in issues))

    def test_skill_frontmatter_allows_standard_optional_keys(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "boring-backend"
            self.write_minimal_skill(base)
            (base / "SKILL.md").write_text(
                "\n".join(
                    [
                        "---",
                        "name: boring-backend",
                        "description: Use when validating boring-backend verifier fixtures.",
                        "license: MIT",
                        "allowed-tools:",
                        "  - shell",
                        "metadata:",
                        "  short-description: boring-backend fixture",
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
            base = Path(tmp) / "boring-backend"
            agents = base / "agents"
            agents.mkdir(parents=True)
            (agents / "openai.yaml").write_text(
                "\n".join(
                    [
                        "interface:",
                        '  display_name: "boring-backend"',
                        '  short_description: "This description is intentionally far too long for the OpenAI skill chip UI"',
                        '  default_prompt: "Use boring-backend to design the contract."',
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            issues: list[str] = []
            module.validate_openai_yaml(base, issues)

            self.assertTrue(any("short_description length" in issue for issue in issues))
            self.assertTrue(any("$boring-backend" in issue for issue in issues))

    def test_openai_metadata_rejects_invalid_yaml(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "boring-backend"
            agents = base / "agents"
            agents.mkdir(parents=True)
            (agents / "openai.yaml").write_text(
                "\n".join(
                    [
                        "interface:",
                        '  display_name: "boring-backend"',
                        '  short_description: "Design reliability contracts before code."',
                        '  default_prompt: "Use $boring-backend to design the contract."',
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
            base = Path(tmp) / "boring-backend"
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
            base = Path(tmp) / "boring-backend"
            nested = base / "references" / "nested"
            nested.mkdir(parents=True)
            (nested / "deep.md").write_text("# Deep\n", encoding="utf-8")
            (base / "SKILL.md").write_text(
                "\n".join(
                    [
                        "---",
                        "name: boring-backend",
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
            self.assertTrue(any("unsupported reference path" in issue for issue in issues))

    def test_reference_structure_checks_markdown_link_targets(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "boring-backend"
            base.mkdir()
            (base / "SKILL.md").write_text(
                "\n".join(
                    [
                        "---",
                        "name: boring-backend",
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

    def test_reference_structure_allows_repo_local_shared_common_references(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            root = Path(tmp)
            base = root / "skills" / "boring-backend"
            common = root / "skills" / "boring-backend-common"
            common.mkdir(parents=True)
            base.mkdir(parents=True)
            (common / "core-guard-routing.md").write_text("# Shared Routing\n", encoding="utf-8")
            (base / "SKILL.md").write_text(
                "\n".join(
                    [
                        "---",
                        "name: boring-backend",
                        "description: Use when designing reliability contracts.",
                        "---",
                        "",
                        "Read `../boring-backend-common/core-guard-routing.md`.",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            old_root = module.ROOT
            module.ROOT = root
            try:
                issues: list[str] = []
                module.validate_reference_structure(base, issues)
            finally:
                module.ROOT = old_root

            self.assertFalse(issues)

    def test_reference_structure_rejects_long_files_nested_links_and_path_escape(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "boring-backend"
            references = base / "references"
            references.mkdir(parents=True)
            (base / "SKILL.md").write_text(
                "\n".join(
                    [
                        "---",
                        "name: boring-backend",
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

            self.assertTrue(any("unsupported reference path" in issue for issue in issues))
            self.assertFalse(any("reference leaves skill folder" in issue for issue in issues))
            self.assertTrue(any("reference exceeds 100 lines" in issue for issue in issues))
            self.assertTrue(any("nested markdown reference" in issue for issue in issues))

    def test_learning_feedback_prompt_must_stay_out_of_runtime_references(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "boring-backend"
            references = base / "references"
            references.mkdir(parents=True)
            (references / "operations-guard-catalog.md").write_text(
                "# Operations\n\n## Learning Feedback Prompt\n\nWrong runtime location.\n",
                encoding="utf-8",
            )

            issues: list[str] = []
            module.validate_boring_backend_semantics(base, issues)

            self.assertTrue(any("Learning Feedback Prompt" in issue for issue in issues))

    def test_boring_backend_semantics_require_operational_escalation_evidence_levels_and_no_learning_prompt(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "boring-backend"
            self.write_minimal_skill(base)
            (base / "SKILL.md").write_text(
                (base / "SKILL.md").read_text(encoding="utf-8").replace("Operational escalation:", "Ops escalation:"),
                encoding="utf-8",
            )
            (base / "references" / "operations-guard-catalog.md").write_text(
                "## Learning Feedback Lens\n",
                encoding="utf-8",
            )

            issues: list[str] = []
            module.validate_boring_backend_semantics(base, issues)

            self.assertTrue(any("operational escalation" in issue for issue in issues))
            self.assertTrue(any("Learning Feedback Lens" in issue for issue in issues))

    def test_boring_backend_semantics_require_routing_handoff_l4_and_token_guidance(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "boring-backend"
            self.write_minimal_skill(base)
            (base / "references" / "core-guard-routing.md").unlink()
            (base / "references" / "token-reporting.md").unlink()
            (base / "SKILL.md").write_text(
                "\n".join(
                    [
                        "---",
                        "name: boring-backend",
                        "description: Use when validating boring-backend verifier fixtures.",
                        "---",
                        "",
                        "Read `references/core-guard-catalog.md`.",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            issues: list[str] = []
            module.validate_boring_backend_semantics(base, issues)

            self.assertTrue(any("core-guard-routing.md" in issue for issue in issues))
            self.assertTrue(any("experiment-reporting.md" in issue for issue in issues))
            self.assertTrue(any("production-evidence" in issue for issue in issues))
            self.assertTrue(any("noncached_input_tokens" in issue for issue in issues))

    def test_boring_backend_semantics_require_experiment_reporting_boundaries(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "boring-backend"
            self.write_minimal_skill(base)
            reporting = base / "references" / "experiment-reporting.md"
            reporting.write_text("# Experiment Reporting\n", encoding="utf-8")
            (base / "SKILL.md").write_text(
                (base / "SKILL.md")
                .read_text(encoding="utf-8")
                .replace(
                    "Read `references/experiment-reporting.md` for experiment first attempts, guarded-run comparisons, handoffs, or multi-phase runs.\n",
                    "",
                ),
                encoding="utf-8",
            )
            (base / "references" / "core-guard-routing.md").write_text(
                (base / "references" / "core-guard-routing.md")
                .read_text(encoding="utf-8")
                .replace("Use `catalog_route` to name why each non-default catalog was loaded.\n", ""),
                encoding="utf-8",
            )

            issues: list[str] = []
            module.validate_boring_backend_semantics(base, issues)

            self.assertTrue(any("experiment-reporting.md" in issue for issue in issues))
            self.assertTrue(any("handoff index" in issue for issue in issues))
            self.assertTrue(any("catalog_route" in issue for issue in issues))

    def test_boring_backend_semantics_require_small_subagent_boundaries(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "boring-backend"
            self.write_minimal_skill(base)
            (base / "references" / "subagent-delegation.md").write_text(
                "# Subagent Delegation\n",
                encoding="utf-8",
            )

            issues: list[str] = []
            module.validate_boring_backend_semantics(base, issues)

            self.assertTrue(any("subagent delegation boundaries" in issue for issue in issues))

    def test_boring_backend_semantics_require_security_route_coverage(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "boring-backend"
            self.write_minimal_skill(base)
            routing = base / "references" / "core-guard-routing.md"
            routing.write_text(
                routing.read_text(encoding="utf-8").replace(
                    "Route public field binding/mass assignment, CORS/TLS, and untrusted third-party responses to `security-guard-catalog.md`.\n",
                    "",
                ),
                encoding="utf-8",
            )

            issues: list[str] = []
            module.validate_boring_backend_semantics(base, issues)

            self.assertTrue(any("security route coverage" in issue for issue in issues))

    def test_boring_backend_semantics_require_subagent_route_and_evidence_gated_fallback(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "boring-backend"
            self.write_minimal_skill(base)
            skill_md = base / "SKILL.md"
            skill_md.write_text(
                skill_md.read_text(encoding="utf-8").replace(
                    "Read `references/subagent-delegation.md` before ordinary subagent delegation.\n",
                    "",
                ),
                encoding="utf-8",
            )
            reporting = base / "references" / "experiment-reporting.md"
            reporting.write_text(
                reporting.read_text(encoding="utf-8").replace(
                    "Open the full first report only for a P0-P2 claim that cannot be resolved from the handoff index and cited evidence.",
                    "Open the full first report when a claim is P0-P2-relevant.",
                ),
                encoding="utf-8",
            )

            issues: list[str] = []
            module.validate_boring_backend_semantics(base, issues)

            self.assertTrue(any("ordinary subagent route" in issue for issue in issues))
            self.assertTrue(any("evidence-gated handoff fallback" in issue for issue in issues))

    def test_boring_backend_semantics_rejects_severity_agnostic_full_report_fallback(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "boring-backend"
            self.write_minimal_skill(base)
            reporting = base / "references" / "experiment-reporting.md"
            reporting.write_text(
                reporting.read_text(encoding="utf-8").replace(
                    "Open the full first report only for a P0-P2 claim that cannot be resolved from the handoff index and cited evidence.",
                    "Open the full first report only when a claim is missing, unclear, or contradicted, or when a P0-P2 claim cannot be resolved from the handoff index and cited evidence.",
                ),
                encoding="utf-8",
            )

            issues: list[str] = []
            module.validate_boring_backend_semantics(base, issues)

            self.assertTrue(any("P0-P2-only full-report fallback" in issue for issue in issues))

    def test_boring_backend_semantics_require_claim_summary_and_cache_write_tokens(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "boring-backend"
            self.write_minimal_skill(base)
            reporting = base / "references" / "experiment-reporting.md"
            reporting.write_text(
                reporting.read_text(encoding="utf-8").replace("- `claim_summary`\n", ""),
                encoding="utf-8",
            )
            token_reporting = base / "references" / "token-reporting.md"
            token_reporting.write_text(
                token_reporting.read_text(encoding="utf-8").replace("cache_write_tokens", ""),
                encoding="utf-8",
            )

            issues: list[str] = []
            module.validate_boring_backend_semantics(base, issues)

            self.assertTrue(any("claim_summary" in issue for issue in issues))
            self.assertTrue(any("cache_write_tokens" in issue for issue in issues))

    def test_boring_backend_semantics_rejects_experiment_fairness_in_core_catalog(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "boring-backend"
            self.write_minimal_skill(base)
            guard_catalog = base / "references" / "core-guard-catalog.md"
            guard_catalog.write_text(
                guard_catalog.read_text(encoding="utf-8")
                + "\nFor first-run experiments, pre-register the same guard list for every variant.\n",
                encoding="utf-8",
            )

            issues: list[str] = []
            module.validate_boring_backend_semantics(base, issues)

            self.assertTrue(any("experiment fairness belongs" in issue for issue in issues))

    def test_boring_backend_semantics_rejects_handoff_detail_in_skill_md(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            base = Path(tmp) / "boring-backend"
            self.write_minimal_skill(base)
            (base / "SKILL.md").write_text(
                (base / "SKILL.md").read_text(encoding="utf-8")
                + "\nWrite `reports/handoffs/<task>-first-handoff.json` with full handoff-first details.\n",
                encoding="utf-8",
            )

            issues: list[str] = []
            module.validate_boring_backend_semantics(base, issues)

            self.assertTrue(any("handoff detail belongs" in issue for issue in issues))

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
            base = Path(tmp) / "boring-backend"
            self.write_minimal_skill(base)
            (base / "SKILL.md").write_text(
                (base / "SKILL.md").read_text(encoding="utf-8")
                + "\nRead `references/operations-guard-catalog.md` for compatibility and backup/restore.\n"
                + "Stale Boring Backend-review text.\n",
                encoding="utf-8",
            )
            (base / "references" / "core-guard-catalog.md").write_text(
                "| P3 | Maintainability, package structure, or undue complexity |\n",
                encoding="utf-8",
            )

            issues: list[str] = []
            module.check_skill_package(base, issues)

            self.assertTrue(any("stale pattern" in issue for issue in issues))
            self.assertTrue(any("operations route overlaps" in issue for issue in issues))
            self.assertTrue(any("core P3 severity" in issue for issue in issues))
            self.assertTrue(any("Boring Backend-review" in issue for issue in issues))

    def test_main_passes_against_temp_repo_with_synced_mirrors(self):
        module = load_module()
        with tempfile.TemporaryDirectory(dir=REPO / "reports") as tmp:
            root = Path(tmp)
            source_root = root / "skills"
            mirror_roots = (root / ".agents" / "skills", root / ".claude" / "skills")
            skills = ("boring-backend",)
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

