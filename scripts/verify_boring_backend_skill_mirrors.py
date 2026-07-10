#!/usr/bin/env python3
"""Verify boring-backend skill source packages and vendor-local mirrors stay in sync."""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("boring-backend",)
SOURCE_ROOT = ROOT / "skills"
MIRROR_ROOTS = (ROOT / ".agents" / "skills", ROOT / ".claude" / "skills")
STALE_PATTERNS = (
    "guarded-pragmatic",
    "Guarded Pragmatic",
    "Boring Backend-design",
    "Boring Backend-implementation",
    "Boring Backend-review",
    "boring-backend skills",
    "an boring-backend",
    "an Boring Backend",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def rel_files(base: Path) -> list[Path]:
    return sorted(p.relative_to(base) for p in base.rglob("*") if p.is_file())


def referenced_markdown(skill_md: Path) -> list[str]:
    text = skill_md.read_text(encoding="utf-8")
    refs = set(re.findall(r"`([^`\n]+\.md(?:#[^`\n]+)?)`", text))
    refs.update(re.findall(r"\[[^\]]+\]\(([^)\s]+\.md(?:#[^)\s]+)?)\)", text))
    return sorted(ref.split("#", 1)[0] for ref in refs)


def fail(message: str, issues: list[str]) -> None:
    issues.append(message)


def skill_frontmatter(skill_md: Path, issues: list[str]) -> dict[str, object] | None:
    lines = skill_md.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        fail(f"missing frontmatter in {display_path(skill_md)}", issues)
        return None

    try:
        end = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration:
        fail(f"unterminated frontmatter in {display_path(skill_md)}", issues)
        return None

    try:
        data = yaml.safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError as exc:
        fail(f"invalid skill frontmatter in {display_path(skill_md)}: {exc}", issues)
        return None

    if data is None:
        data = {}

    if not isinstance(data, dict):
        fail(f"skill frontmatter must be a mapping in {display_path(skill_md)}", issues)
        return None

    return data


def validate_skill_frontmatter(base: Path, issues: list[str]) -> None:
    skill_md = base / "SKILL.md"
    data = skill_frontmatter(skill_md, issues)
    if data is None:
        return

    allowed_keys = {"name", "description", "license", "compatibility", "allowed-tools", "metadata"}
    extra_keys = sorted(set(data) - allowed_keys)
    if extra_keys:
        fail(f"extra frontmatter keys {extra_keys!r} in {display_path(skill_md)}", issues)

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        fail(f"missing string frontmatter name in {display_path(skill_md)}", issues)
    elif name != base.name:
        fail(f"frontmatter name {name!r} does not match folder {base.name!r} in {display_path(skill_md)}", issues)
    elif len(name) > 64 or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        fail(f"invalid frontmatter name {name!r} in {display_path(skill_md)}", issues)

    description = data.get("description")
    if not isinstance(description, str) or not description.strip():
        fail(f"missing string frontmatter description in {display_path(skill_md)}", issues)
    elif len(description.strip()) > 200:
        fail(f"description too long ({len(description.strip())}) in {display_path(skill_md)}", issues)

    license_value = data.get("license")
    if "license" in data and (not isinstance(license_value, str) or not license_value.strip()):
        fail(f"frontmatter license must be a non-empty string in {display_path(skill_md)}", issues)

    compatibility = data.get("compatibility")
    if "compatibility" in data:
        if not isinstance(compatibility, str) or not compatibility.strip():
            fail(f"frontmatter compatibility must be a non-empty string in {display_path(skill_md)}", issues)
        elif len(compatibility.strip()) > 500:
            fail(f"frontmatter compatibility exceeds 500 characters in {display_path(skill_md)}", issues)

    allowed_tools = data.get("allowed-tools")
    if "allowed-tools" in data and (not isinstance(allowed_tools, str) or not allowed_tools.strip()):
        fail(f"frontmatter allowed-tools must be a non-empty string in {display_path(skill_md)}", issues)

    metadata = data.get("metadata")
    if "metadata" in data and not isinstance(metadata, dict):
        fail(f"frontmatter metadata must be a mapping in {display_path(skill_md)}", issues)


def validate_openai_yaml(base: Path, issues: list[str]) -> None:
    openai_yaml = base / "agents" / "openai.yaml"
    if not openai_yaml.exists():
        fail(f"missing {display_path(openai_yaml)}", issues)
        return

    text = openai_yaml.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        fail(f"invalid openai yaml in {display_path(openai_yaml)}: {exc}", issues)
        return

    if not isinstance(data, dict):
        fail(f"openai yaml must be a mapping in {display_path(openai_yaml)}", issues)
        return

    interface = data.get("interface")
    if not isinstance(interface, dict):
        fail(f"missing interface block in {display_path(openai_yaml)}", issues)
        interface = {}

    for key in ("display_name", "short_description", "default_prompt"):
        if not isinstance(interface.get(key), str) or not interface.get(key, "").strip():
            fail(f"missing string interface.{key} in {display_path(openai_yaml)}", issues)

    short_description = interface.get("short_description")
    if isinstance(short_description, str) and not 25 <= len(short_description) <= 64:
        fail(
            f"openai short_description length {len(short_description)} outside 25-64 in {display_path(openai_yaml)}",
            issues,
        )

    default_prompt = interface.get("default_prompt")
    required_skill = f"${base.name}"
    if isinstance(default_prompt, str) and required_skill not in default_prompt:
        fail(f"openai default_prompt must mention {required_skill} in {display_path(openai_yaml)}", issues)


def validate_reference_structure(base: Path, issues: list[str]) -> None:
    skill_md = base / "SKILL.md"
    if skill_md.exists():
        for ref in referenced_markdown(skill_md):
            rel_ref = Path(ref)
            local_reference = not rel_ref.is_absolute() and len(rel_ref.parts) == 2 and rel_ref.parts[0] == "references"
            shared_reference = (
                not rel_ref.is_absolute()
                and len(rel_ref.parts) == 3
                and rel_ref.parts[0] == ".."
                and rel_ref.parts[1] == "boring-backend-common"
            )
            if not (local_reference or shared_reference):
                fail(f"unsupported reference path: {display_path(skill_md)} -> {ref}", issues)
                continue

            target = (base / ref).resolve()
            if local_reference:
                try:
                    target.relative_to(base.resolve())
                except ValueError:
                    fail(f"reference leaves skill folder: {display_path(skill_md)} -> {ref}", issues)
                    continue
            else:
                try:
                    target.relative_to(base.parent.resolve() / "boring-backend-common")
                except ValueError:
                    fail(f"shared reference must stay under sibling boring-backend-common: {display_path(skill_md)} -> {ref}", issues)
                    continue
            if not target.exists():
                fail(f"missing reference: {display_path(skill_md)} -> {ref}", issues)

    references = base / "references"
    if references.exists():
        for ref_file in references.rglob("*.md"):
            rel_ref = ref_file.relative_to(references)
            if len(rel_ref.parts) != 1:
                fail(f"nested reference file: {display_path(ref_file)}", issues)

            ref_text = ref_file.read_text(encoding="utf-8")
            if re.search(r"\]\([^)]*\.md\)", ref_text):
                fail(f"nested markdown reference in {display_path(ref_file)}", issues)
            if len(ref_text.splitlines()) > 100:
                fail(f"reference exceeds 100 lines: {display_path(ref_file)}", issues)


def validate_boring_backend_semantics(base: Path, issues: list[str]) -> None:
    """Apply lexical contract guards; behavioral correctness requires external evaluation."""
    if base.name not in SKILLS:
        return

    skill_md = base / "SKILL.md"
    references = base / "references"
    corpus_parts: list[str] = []
    if skill_md.exists():
        skill_text = skill_md.read_text(encoding="utf-8")
        skill_lower = skill_text.lower()
        corpus_parts.append(skill_text)
        frontmatter = skill_frontmatter(skill_md, [])
        description = frontmatter.get("description", "") if frontmatter else ""
        description_lower = description.lower() if isinstance(description, str) else ""
        description_terms = (
            "concurrenc",
            "dependenc",
            "migration",
            "compatib",
            "docs",
            "contract",
        )
        has_ui_boundary = re.search(r"\bui\b", description_lower) is not None
        has_negative_boundary = any(
            marker in description_lower for marker in ("not for", "not ui", "non-contract", "exclud")
        )
        if (
            any(term not in description_lower for term in description_terms)
            or not has_ui_boundary
            or not has_negative_boundary
        ):
            fail(
                f"selection description must cover dependencies/migrations/compatibility and exclude UI/docs-only edits in {display_path(skill_md)}",
                issues,
            )
        for line in skill_text.splitlines():
            if "operations-guard-catalog.md" in line and re.search(
                r"\bfor\b.*(?:\bcompatibility\b|backup/restore)", line
            ):
                fail(f"operations route overlaps dedicated catalogs in {display_path(skill_md)}", issues)
        if "Operational escalation:" not in skill_text:
            fail(f"missing operational escalation rule in {display_path(skill_md)}", issues)
        if "core-guard-routing.md" not in skill_text:
            fail(f"missing core-guard-routing.md route in {display_path(skill_md)}", issues)
        if "handoff-reporting.md" not in skill_text:
            fail(f"missing handoff-reporting.md route in {display_path(skill_md)}", issues)
        if "experiment-reporting.md" in skill_text:
            fail(f"stale experiment-reporting.md route in {display_path(skill_md)}", issues)
        if "subagent-delegation.md" not in skill_text:
            fail(f"missing subagent-delegation.md route in {display_path(skill_md)}", issues)
        subagent_route = any(
            "subagent-delegation.md" in line and "ordinary subagent delegation" in line.lower()
            for line in skill_text.splitlines()
        )
        if not subagent_route:
            fail(f"missing ordinary subagent route to subagent-delegation.md in {display_path(skill_md)}", issues)
        if any("handoff-reporting.md" in line and "subagent" in line.lower() for line in skill_text.splitlines()):
            fail(f"ordinary subagents need a separate subagent delegation reference in {display_path(skill_md)}", issues)
        if "review-only work never edits" not in skill_lower:
            fail(f"missing review-only no-edit rule in {display_path(skill_md)}", issues)
        if re.search(
            r"review-only[^.\n]*(?:may|can|should|must)\s+(?:still\s+)?(?:edit|modify|add|write|patch)",
            skill_lower,
        ):
            fail(f"contradictory review-only edit permission in {display_path(skill_md)}", issues)
        fix_terms = ("authorized fix run", "regression test", "rerun", "failing")
        if any(term not in skill_lower for term in fix_terms):
            fail(f"missing authorized fix regression-test rule in {display_path(skill_md)}", issues)
        output_terms = ("scale output", "task size", "risk", "non-obvious catalog choices")
        if any(term not in skill_lower for term in output_terms):
            fail(f"missing task/risk-scaled output guidance in {display_path(skill_md)}", issues)

    guard_catalog = base / "references" / "core-guard-catalog.md"
    if guard_catalog.exists():
        guard_text = guard_catalog.read_text(encoding="utf-8")
        if "| P3 | Maintainability, package structure, performance/ops risk, or undue complexity |" not in guard_text:
            fail(f"core P3 severity lacks performance/ops risk in {display_path(guard_catalog)}", issues)
        guard_lower = guard_text.lower()
        idempotency_terms = (
            "natural operation",
            "unique constraint",
            "conditional write",
            "durable",
            "request fingerprint",
            "payload",
            "mismatch",
            "contract-final",
            "transient",
            "do not cache",
            "double side effect",
        )
        missing_idempotency = [term for term in idempotency_terms if term not in guard_lower]
        if missing_idempotency:
            fail(
                f"missing idempotency contract {missing_idempotency!r} in {display_path(guard_catalog)}",
                issues,
            )
        p0_lines = [line.lower() for line in guard_text.splitlines() if "| p0 |" in line.lower()]
        if not any("artifact" in line and "defect" in line for line in p0_lines):
            fail(f"missing P0 artifact-defect boundary in {display_path(guard_catalog)}", issues)
        evidence_gap_terms = ("environment", "tool", "credential", "evidence gap", "not p0", "artifact")
        if any(term not in guard_lower for term in evidence_gap_terms):
            fail(f"missing environment evidence-gap boundary in {display_path(guard_catalog)}", issues)
        if "first-run experiments" in guard_lower or "pre-register" in guard_lower:
            fail(f"experiment fairness belongs outside runtime, not {display_path(guard_catalog)}", issues)

    core_routing = base / "references" / "core-guard-routing.md"
    if core_routing.exists():
        routing_text = core_routing.read_text(encoding="utf-8")
        if "core-guard-catalog.md" not in routing_text:
            fail(f"core routing must point to core-guard-catalog.md in {display_path(core_routing)}", issues)
        routing_lower = routing_text.lower()
        production_terms = ("production-evidence mode", "explicit", "environment-specific", "l4")
        if any(term not in routing_lower for term in production_terms) or any(
            "production-evidence" in line.lower() and "actual db" in line.lower()
            for line in routing_text.splitlines()
        ):
            fail(f"missing environment-specific L4 production-evidence boundary in {display_path(core_routing)}", issues)
        l2_lines = [line.lower() for line in routing_text.splitlines() if "l2 integration" in line.lower()]
        if not any("real db" in line for line in l2_lines):
            fail(f"missing real DB integration at L2 in {display_path(core_routing)}", issues)
        l4_lines = [line.lower() for line in routing_text.splitlines() if "l4 production-readiness" in line.lower()]
        if not any("environment-specific" in line for line in l4_lines):
            fail(f"missing environment-specific L4 evidence definition in {display_path(core_routing)}", issues)
        security_route_terms = (
            "security-guard-catalog.md",
            "field binding",
            "cors/tls",
            "third-party responses",
        )
        missing_security_terms = [term for term in security_route_terms if term not in routing_lower]
        if missing_security_terms:
            fail(
                f"missing security route coverage {missing_security_terms!r} in {display_path(core_routing)}",
                issues,
            )
        for label in ("L0 Static", "L1 Unit/domain", "L2 Integration", "L3 Risk-specific", "L4 Production-readiness"):
            if label not in routing_text:
                fail(f"missing evidence level {label!r} in {display_path(core_routing)}", issues)

    security_catalog = base / "references" / "security-guard-catalog.md"
    if security_catalog.exists():
        security_lower = security_catalog.read_text(encoding="utf-8").lower()
        if "trusted server-side boundary" not in security_lower:
            fail(f"missing trusted authorization boundary in {display_path(security_catalog)}", issues)
        if not all(term in security_lower for term in ("scop", "read", "list")):
            fail(f"missing scoped read/list authorization in {display_path(security_catalog)}", issues)

    handoff_reporting = base / "references" / "handoff-reporting.md"
    if handoff_reporting.exists():
        reporting_text = handoff_reporting.read_text(encoding="utf-8")
        reporting_lower = reporting_text.lower()
        required_groups = {
            "handoff index": ("handoff index",),
            "handoff destination": (
                "only when requested",
                "writes are allowed",
                "user",
                "workspace",
                "designated",
                "path",
            ),
            "handoff identity": (
                "task_id",
                "scope",
                "source_revision",
                "clean/dirty",
                "digest",
                "path_base",
                "claims",
            ),
            "handoff claim evidence": (
                "claim_id",
                "claim_summary",
                "file:line",
                "command",
                "exit",
                "evidence",
                "gaps",
            ),
            "handoff path portability": ("relative to", "path_base"),
            "handoff validation": (
                "validate",
                "task_id",
                "scope",
                "source_revision",
                "dirty-state digest",
                "path_base",
                "current",
            ),
            "material-claim fallback": (
                "handoff-first",
                "fuller evidence",
                "unresolved material claims",
                "priorit",
                "p0-p2",
            ),
            "delta output": ("delta", "claim_id"),
        }
        for group, terms in required_groups.items():
            missing = [term for term in terms if term not in reporting_lower]
            if missing:
                fail(
                    f"missing handoff reporting {group}: {missing!r} in {display_path(handoff_reporting)}",
                    issues,
                )
        if "subagent prompt boundary" in reporting_lower or (
            "subagent" in reporting_lower and "allowed catalogs" in reporting_lower
        ):
            fail(
                f"subagent prompt boundaries belong in subagent-delegation.md, not {display_path(handoff_reporting)}",
                issues,
            )
    else:
        fail(f"missing {display_path(handoff_reporting)}", issues)

    subagent_delegation = base / "references" / "subagent-delegation.md"
    if subagent_delegation.exists():
        subagent_text = subagent_delegation.read_text(encoding="utf-8")
        subagent_lower = subagent_text.lower()
        boundary_terms = (
            "user request",
            "repository instructions",
            "scope",
            "paths",
            "skill path",
            "mode",
            "evidence constraints",
            "handoff",
            "file:line",
            "commands",
            "exits",
            "evidence",
            "gaps",
        )
        missing = [term for term in boundary_terms if term not in subagent_lower]
        if missing:
            fail(
                f"missing subagent delegation boundaries {missing!r} in {display_path(subagent_delegation)}",
                issues,
            )
        if "route catalogs" not in subagent_lower or "intentionally narrow" not in subagent_lower:
            fail(f"missing subagent catalog autonomy in {display_path(subagent_delegation)}", issues)
        independent_terms = ("independent validation", "raw artifacts", "no prior conclusions")
        if any(term not in subagent_lower for term in independent_terms):
            fail(f"missing independent validation inputs in {display_path(subagent_delegation)}", issues)
        if "full logs" not in subagent_lower or "only when needed" not in subagent_lower:
            fail(f"missing full logs only when needed rule in {display_path(subagent_delegation)}", issues)
        if len(subagent_text.split()) > 90:
            fail(f"subagent delegation reference exceeds 90 words: {display_path(subagent_delegation)}", issues)
    else:
        fail(f"missing {display_path(subagent_delegation)}", issues)

    if references.exists():
        if not core_routing.exists():
            fail(f"missing {display_path(core_routing)}", issues)
        for ref_file in references.glob("*.md"):
            ref_text = ref_file.read_text(encoding="utf-8")
            corpus_parts.append(ref_text)
            direct_ref = f"references/{ref_file.name}"
            if skill_md.exists() and direct_ref not in skill_text:
                fail(f"reference must be linked directly from {display_path(skill_md)}: {direct_ref}", issues)
            if "Learning Feedback Lens" in ref_text:
                fail(f"runtime catalog contains Learning Feedback Lens in {display_path(ref_file)}", issues)
            if "Learning Feedback Prompt" in ref_text:
                fail(f"Learning Feedback Prompt must not be in runtime references: {display_path(ref_file)}", issues)
            ref_lower = ref_text.lower()
            if any(term in ref_lower for term in ("first-run experiments", "postmortem traps", "pre-register")):
                fail(f"experiment fairness belongs outside runtime, not {display_path(ref_file)}", issues)

    runtime_forward = base / "references" / "forward-test-prompts.md"
    if runtime_forward.exists():
        fail(f"forward-test-prompts.md belongs outside runtime references: {display_path(runtime_forward)}", issues)
    runtime_experiment = base / "references" / "experiment-reporting.md"
    if runtime_experiment.exists():
        fail(f"experiment-reporting.md belongs outside runtime references: {display_path(runtime_experiment)}", issues)
    runtime_fairness = base / "references" / "experiment-fairness.md"
    if runtime_fairness.exists():
        fail(f"experiment-fairness.md belongs outside runtime references: {display_path(runtime_fairness)}", issues)

    corpus = "\n".join(corpus_parts)
    corpus_lower = corpus.lower()
    if "production-evidence mode" not in corpus_lower:
        fail(f"missing production-evidence mode guidance in {display_path(base)}", issues)
    if "catalog_route" in corpus_lower:
        fail(f"runtime requires synthetic catalog_route output in {display_path(base)}", issues)
    if "guarded-run comparison" in corpus_lower:
        fail(f"guarded-run comparison phrase belongs outside runtime in {display_path(base)}", issues)
    if re.search(r"reports[\\/]", corpus_lower):
        fail(f"hardcoded handoff path belongs outside runtime in {display_path(base)}", issues)
    for term in (
        "token telemetry",
        "token_usage",
        "cached_input_tokens",
        "cache_write_tokens",
        "noncached_input_tokens",
        "reasoning_output_tokens",
    ):
        if term in corpus:
            fail(
                f"runtime token accounting {term!r} belongs in external evaluation tooling, not {display_path(base)}",
                issues,
            )
    if "handoff-first" not in corpus_lower:
        fail(f"missing handoff-first review guidance in {display_path(base)}", issues)


def check_skill_package(base: Path, issues: list[str]) -> None:
    skill_md = base / "SKILL.md"
    if not skill_md.exists():
        fail(f"missing {display_path(skill_md)}", issues)
        return

    validate_skill_frontmatter(base, issues)
    for file_path in rel_files(base):
        text = (base / file_path).read_text(encoding="utf-8")
        for pattern in STALE_PATTERNS:
            if pattern in text:
                fail(f"stale pattern {pattern!r} in {display_path(base / file_path)}", issues)

    validate_openai_yaml(base, issues)
    validate_reference_structure(base, issues)
    validate_boring_backend_semantics(base, issues)


def check_mirror(source: Path, mirror: Path, issues: list[str]) -> None:
    if not mirror.exists():
        fail(f"missing mirror {display_path(mirror)}", issues)
        return

    source_files = rel_files(source)
    mirror_files = rel_files(mirror)
    if source_files != mirror_files:
        fail(
            f"file set mismatch: {display_path(source)} vs {display_path(mirror)}",
            issues,
        )
        return

    for rel in source_files:
        source_file = source / rel
        mirror_file = mirror / rel
        if sha256(source_file) != sha256(mirror_file):
            fail(f"mirror drift: {display_path(mirror_file)}", issues)


def main() -> int:
    issues: list[str] = []

    for skill in SKILLS:
        source = SOURCE_ROOT / skill
        check_skill_package(source, issues)
        for mirror_root in MIRROR_ROOTS:
            mirror = mirror_root / skill
            check_skill_package(mirror, issues)
            check_mirror(source, mirror, issues)

    if issues:
        print("boring-backend skill mirror verification failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("boring-backend skill mirror verification passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

