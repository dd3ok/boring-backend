#!/usr/bin/env python3
"""Verify the source skill package and byte-identical vendor-local mirrors."""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path, PurePosixPath

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "boring-backend"
SOURCE = ROOT / "skills" / SKILL_NAME
MIRRORS = (
    ROOT / ".agents" / "skills" / SKILL_NAME,
    ROOT / ".claude" / "skills" / SKILL_NAME,
)

REQUIRED_REFERENCES = (
    "core-guard-catalog.md",
    "security-guard-catalog.md",
    "data-lifecycle-guard-catalog.md",
    "performance-guard-catalog.md",
    "resilience-guard-catalog.md",
    "operations-guard-catalog.md",
    "compatibility-governance-guard-catalog.md",
    "production-evidence.md",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def rel_files(base: Path) -> list[Path]:
    return sorted(path.relative_to(base) for path in base.rglob("*") if path.is_file())


def without_html_comments(line: str, in_comment: bool) -> tuple[str, bool]:
    visible: list[str] = []
    position = 0
    while position < len(line):
        if in_comment:
            end = line.find("-->", position)
            if end < 0:
                return "".join(visible), True
            in_comment = False
            position = end + 3
            continue

        start = line.find("<!--", position)
        if start < 0:
            visible.append(line[position:])
            break
        visible.append(line[position:start])
        in_comment = True
        position = start + 4
    return "".join(visible), in_comment


def markdown_prose(text: str) -> str:
    prose: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    in_comment = False
    for line in text.splitlines():
        if fence_character is not None:
            closing_fence = re.match(
                rf"^\s{{0,3}}{re.escape(fence_character)}{{{fence_length},}}[ \t]*$",
                line,
            )
            if closing_fence:
                fence_character = None
                fence_length = 0
            continue

        visible, in_comment = without_html_comments(line, in_comment)
        opening_fence = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", visible)
        if opening_fence:
            marker = opening_fence.group(1)
            info = opening_fence.group(2)
            if marker[0] == "`" and "`" in info:
                prose.append(visible)
                continue
            fence_character = marker[0]
            fence_length = len(marker)
            continue
        prose.append(visible)
    return "\n".join(prose)


def referenced_markdown(skill_md: Path) -> list[str]:
    text = markdown_prose(skill_md.read_text(encoding="utf-8"))
    references = set(re.findall(r"`([^`\r\n]+\.md(?:#[^`\r\n]+)?)`", text))
    references.update(
        re.findall(r"\[[^\]]+\]\(<?([^)>\s]+\.md(?:#[^)>\s]+)?)>?\)", text)
    )
    return sorted(reference.split("#", 1)[0] for reference in references)


def fail(message: str, issues: list[str]) -> None:
    issues.append(message)


def validate_openai_yaml(base: Path, issues: list[str]) -> None:
    openai_yaml = base / "agents" / "openai.yaml"
    if not openai_yaml.is_file():
        fail(f"missing {display_path(openai_yaml)}", issues)
        return

    try:
        data = yaml.safe_load(openai_yaml.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        fail(f"invalid YAML in {display_path(openai_yaml)}: {exc}", issues)
        return

    if not isinstance(data, dict) or not isinstance(data.get("interface"), dict):
        fail(f"missing interface mapping in {display_path(openai_yaml)}", issues)
        return

    interface = data["interface"]
    for key in ("display_name", "short_description", "default_prompt"):
        value = interface.get(key)
        if not isinstance(value, str) or not value.strip():
            fail(f"missing non-empty interface.{key} in {display_path(openai_yaml)}", issues)

    short_description = interface.get("short_description")
    if isinstance(short_description, str) and not 25 <= len(short_description) <= 64:
        fail(
            f"interface.short_description must be 25-64 characters in {display_path(openai_yaml)}",
            issues,
        )

    default_prompt = interface.get("default_prompt")
    if isinstance(default_prompt, str) and f"${base.name}" not in default_prompt:
        fail(f"interface.default_prompt must select ${base.name} in {display_path(openai_yaml)}", issues)


def validate_reference_structure(base: Path, issues: list[str]) -> None:
    skill_md = base / "SKILL.md"
    references_dir = base / "references"
    if not references_dir.is_dir():
        fail(f"missing {display_path(references_dir)}", issues)
        return

    reference_files = sorted(path for path in references_dir.rglob("*") if path.is_file())
    for path in reference_files:
        if path.parent != references_dir or path.suffix.lower() != ".md":
            fail(f"references must be flat Markdown files: {display_path(path)}", issues)

    linked_paths: set[str] = set()
    for raw_reference in referenced_markdown(skill_md):
        if "\\" in raw_reference:
            fail(f"non-portable source reference: {display_path(skill_md)} -> {raw_reference}", issues)
            continue
        reference = PurePosixPath(raw_reference)
        if reference.is_absolute() or len(reference.parts) != 2 or reference.parts[0] != "references":
            fail(f"unsupported source reference: {display_path(skill_md)} -> {raw_reference}", issues)
            continue
        linked_paths.add(reference.as_posix())
        target = base.joinpath(*reference.parts)
        if not target.is_file():
            fail(f"missing source reference: {display_path(skill_md)} -> {raw_reference}", issues)

    actual_names = {path.name for path in reference_files if path.parent == references_dir}
    for name in REQUIRED_REFERENCES:
        if name not in actual_names:
            fail(f"missing required reference {display_path(references_dir / name)}", issues)

    for path in reference_files:
        if path.parent == references_dir:
            relative = f"references/{path.name}"
            if relative not in linked_paths:
                fail(f"reference is not linked directly from {display_path(skill_md)}: {relative}", issues)


def validate_runtime_license(base: Path, root: Path, issues: list[str]) -> None:
    root_license = root / "LICENSE"
    runtime_license = base / "LICENSE"
    if not root_license.is_file():
        fail(f"missing {display_path(root_license)}", issues)
        return
    if not runtime_license.is_file():
        fail(f"missing runtime license {display_path(runtime_license)}", issues)
        return
    if root_license.read_text(encoding="utf-8") != runtime_license.read_text(encoding="utf-8"):
        fail(f"runtime license differs from {display_path(root_license)}: {display_path(runtime_license)}", issues)


def check_source_package(base: Path, issues: list[str], root: Path = ROOT) -> None:
    skill_md = base / "SKILL.md"
    if not skill_md.is_file():
        fail(f"missing {display_path(skill_md)}", issues)
        return

    validate_openai_yaml(base, issues)
    validate_reference_structure(base, issues)
    validate_runtime_license(base, root, issues)


def check_mirror(source: Path, mirror: Path, issues: list[str]) -> None:
    if not mirror.is_dir():
        fail(f"missing mirror {display_path(mirror)}", issues)
        return

    source_files = rel_files(source)
    mirror_files = rel_files(mirror)
    if source_files != mirror_files:
        fail(f"file set mismatch: {display_path(source)} vs {display_path(mirror)}", issues)
        return

    for relative in source_files:
        if sha256(source / relative) != sha256(mirror / relative):
            fail(f"mirror drift: {display_path(mirror / relative)}", issues)


def main(root: Path = ROOT, source: Path = SOURCE, mirrors: tuple[Path, ...] = MIRRORS) -> int:
    issues: list[str] = []

    check_source_package(source, issues, root)
    for mirror in mirrors:
        check_mirror(source, mirror, issues)

    if issues:
        print("boring-backend skill verification failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("boring-backend source and mirror verification passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
