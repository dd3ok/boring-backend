#!/usr/bin/env python3
"""Verify RDD skill source packages and vendor-local mirrors stay in sync."""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("rdd-design", "rdd-implementation", "rdd-review")
SOURCE_ROOT = ROOT / "skills"
MIRROR_ROOTS = (ROOT / ".agents" / "skills", ROOT / ".claude" / "skills")
STALE_PATTERNS = ("../rdd-common", "guarded-pragmatic", "Guarded Pragmatic")


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

    allowed_keys = {"name", "description", "license", "allowed-tools", "metadata"}
    extra_keys = sorted(set(data) - allowed_keys)
    if extra_keys:
        fail(f"extra frontmatter keys {extra_keys!r} in {display_path(skill_md)}", issues)

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        fail(f"missing string frontmatter name in {display_path(skill_md)}", issues)
    elif name != base.name:
        fail(f"frontmatter name {name!r} does not match folder {base.name!r} in {display_path(skill_md)}", issues)
    elif not re.fullmatch(r"[a-z0-9-]+", name):
        fail(f"invalid frontmatter name {name!r} in {display_path(skill_md)}", issues)

    description = data.get("description")
    if not isinstance(description, str) or not description.strip():
        fail(f"missing string frontmatter description in {display_path(skill_md)}", issues)
    elif len(description.strip()) > 200:
        fail(f"description too long ({len(description.strip())}) in {display_path(skill_md)}", issues)


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
            if rel_ref.is_absolute() or len(rel_ref.parts) != 2 or rel_ref.parts[0] != "references":
                fail(f"reference must be a one-level references file: {display_path(skill_md)} -> {ref}", issues)

            target = (base / ref).resolve()
            try:
                target.relative_to(base.resolve())
            except ValueError:
                fail(f"reference leaves skill folder: {display_path(skill_md)} -> {ref}", issues)
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


def validate_rdd_semantics(base: Path, issues: list[str]) -> None:
    if base.name not in SKILLS:
        return

    skill_md = base / "SKILL.md"
    if skill_md.exists():
        skill_text = skill_md.read_text(encoding="utf-8")
        for line in skill_text.splitlines():
            if "operations-guard-catalog.md" in line and re.search(r"\bcompatibility\b|backup/restore", line):
                fail(f"operations route overlaps dedicated catalogs in {display_path(skill_md)}", issues)
        if base.name == "rdd-review" and "Operational escalation:" not in skill_text:
            fail(f"missing operational escalation rule in {display_path(skill_md)}", issues)

    guard_catalog = base / "references" / "guard-catalog.md"
    if guard_catalog.exists():
        guard_text = guard_catalog.read_text(encoding="utf-8")
        if "| P3 | Maintainability, package structure, performance/ops risk, or undue complexity |" not in guard_text:
            fail(f"core P3 severity lacks performance/ops risk in {display_path(guard_catalog)}", issues)
        guard_lower = guard_text.lower()
        if "first-run experiments" not in guard_lower or "pre-register" not in guard_lower:
            fail(f"guard fairness wording missing in {display_path(guard_catalog)}", issues)

    evidence_strength = base / "references" / "evidence-strength.md"
    if evidence_strength.exists():
        evidence_text = evidence_strength.read_text(encoding="utf-8")
        for label in ("L0 Static", "L1 Unit/domain", "L2 Integration", "L3 Risk-specific", "L4 Production-readiness"):
            if label not in evidence_text:
                fail(f"missing evidence level {label!r} in {display_path(evidence_strength)}", issues)

    learning_prompt_found = False
    references = base / "references"
    if references.exists():
        for ref_file in references.glob("*.md"):
            ref_text = ref_file.read_text(encoding="utf-8")
            if "Learning Feedback Lens" in ref_text:
                fail(f"runtime catalog contains Learning Feedback Lens in {display_path(ref_file)}", issues)
            if "Learning Feedback Prompt" in ref_text:
                if ref_file.name != "forward-test-prompts.md":
                    fail(f"Learning Feedback Prompt belongs in forward-test-prompts.md: {display_path(ref_file)}", issues)
                else:
                    learning_prompt_found = True

    if not learning_prompt_found:
        fail(f"missing Learning Feedback Prompt in {display_path(base / 'references' / 'forward-test-prompts.md')}", issues)


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
    validate_rdd_semantics(base, issues)


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
        print("RDD skill mirror verification failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("RDD skill mirror verification passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
