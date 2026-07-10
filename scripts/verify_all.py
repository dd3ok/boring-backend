#!/usr/bin/env python3
"""Run all boring-backend repository verification checks."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import NamedTuple


ROOT = Path(__file__).resolve().parents[1]


class Command(NamedTuple):
    label: str
    args: list[str]


def build_commands(root: Path = ROOT) -> list[Command]:
    python = sys.executable
    return [
        Command(
            "skill mirror verification",
            [python, str(root / "scripts" / "verify_boring_backend_skill_mirrors.py")],
        ),
        Command(
            "repository tests",
            [python, "-m", "unittest", "discover", "-s", str(root / "tests")],
        ),
        Command(
            "forward-test implementation tests",
            [
                python,
                "-B",
                "-m",
                "unittest",
                "discover",
                "-s",
                str(root / "reports" / "boring-backend-forward-test-implementation"),
                "-p",
                "test_*.py",
            ],
        ),
    ]


def main() -> int:
    for command in build_commands(ROOT):
        print(f"==> {command.label}", flush=True)
        result = subprocess.run(command.args, cwd=ROOT, shell=False)
        if result.returncode != 0:
            return result.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
