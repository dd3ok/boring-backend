#!/usr/bin/env python3
"""Verify RDD skill source packages and vendor-local mirrors stay in sync."""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ("rdd-design", "rdd-implementation", "rdd-review")
SOURCE_ROOT = ROOT / "skills"
MIRROR_ROOTS = (ROOT / ".agents" / "skills", ROOT / ".claude" / "skills")
STALE_PATTERNS = ("../rdd-common", "guarded-pragmatic", "Guarded Pragmatic")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel_files(base: Path) -> list[Path]:
    return sorted(p.relative_to(base) for p in base.rglob("*") if p.is_file())


def description_length(skill_md: Path) -> int:
    text = skill_md.read_text(encoding="utf-8")
    match = re.search(r"(?m)^description:\s*(.+)$", text)
    if not match:
        return -1
    return len(match.group(1).strip().strip('"').strip("'"))


def referenced_markdown(skill_md: Path) -> list[str]:
    text = skill_md.read_text(encoding="utf-8")
    return re.findall(r"`([^`]+\.md)`", text)


def fail(message: str, issues: list[str]) -> None:
    issues.append(message)


def check_skill_package(base: Path, issues: list[str]) -> None:
    skill_md = base / "SKILL.md"
    if not skill_md.exists():
        fail(f"missing {skill_md.relative_to(ROOT)}", issues)
        return

    desc_len = description_length(skill_md)
    if desc_len < 0:
        fail(f"missing description in {skill_md.relative_to(ROOT)}", issues)
    elif desc_len > 200:
        fail(f"description too long ({desc_len}) in {skill_md.relative_to(ROOT)}", issues)

    for file_path in rel_files(base):
        text = (base / file_path).read_text(encoding="utf-8")
        for pattern in STALE_PATTERNS:
            if pattern in text:
                fail(f"stale pattern {pattern!r} in {(base / file_path).relative_to(ROOT)}", issues)

    for ref in referenced_markdown(skill_md):
        target = (base / ref).resolve()
        try:
            target.relative_to(base.resolve())
        except ValueError:
            fail(f"reference leaves skill folder: {skill_md.relative_to(ROOT)} -> {ref}", issues)
            continue
        if not target.exists():
            fail(f"missing reference: {skill_md.relative_to(ROOT)} -> {ref}", issues)

    references = base / "references"
    if references.exists():
        for ref_file in references.rglob("*.md"):
            ref_text = ref_file.read_text(encoding="utf-8")
            if re.search(r"\]\([^)]*\.md\)", ref_text):
                fail(f"nested markdown reference in {ref_file.relative_to(ROOT)}", issues)
            if len(ref_text.splitlines()) > 100:
                fail(f"reference exceeds 100 lines: {ref_file.relative_to(ROOT)}", issues)


def check_mirror(source: Path, mirror: Path, issues: list[str]) -> None:
    if not mirror.exists():
        fail(f"missing mirror {mirror.relative_to(ROOT)}", issues)
        return

    source_files = rel_files(source)
    mirror_files = rel_files(mirror)
    if source_files != mirror_files:
        fail(
            f"file set mismatch: {source.relative_to(ROOT)} vs {mirror.relative_to(ROOT)}",
            issues,
        )
        return

    for rel in source_files:
        source_file = source / rel
        mirror_file = mirror / rel
        if sha256(source_file) != sha256(mirror_file):
            fail(f"mirror drift: {mirror_file.relative_to(ROOT)}", issues)


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
