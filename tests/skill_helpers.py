"""Helpers for reading fridge-door/SKILL.md in tests."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.check import check_skill, delegate_commands, full_instruction

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "fridge-door"
SKILL_MD = SKILL_DIR / "SKILL.md"


def skill_text() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def section(title: str, level: int = 1) -> str:
    """Text under a heading such as '# Required input' or '## Step 1: ...' (prefix match on the title)."""
    text = skill_text()
    hashes = "#" * level
    m = re.search(rf"^{hashes} {re.escape(title)}.*$", text, re.M)
    assert m, f"heading not found: {hashes} {title}"
    rest = text[m.end():]
    nxt = re.search(rf"^#{{1,{level}}} ", rest, re.M)
    return rest if nxt is None else rest[: nxt.start()]


@dataclass
class Delegate:
    target: str
    instruction: str
    line: int


def delegates(text: str | None = None) -> list[Delegate]:
    source = skill_text() if text is None else text
    out = []
    for line, command in delegate_commands(source):
        target = command.split("--target", 1)[1].split()[0]
        out.append(Delegate(target, full_instruction(command)[1:-1], line))
    return out


def delegates_in(title: str, level: int = 2) -> list[Delegate]:
    return delegates(section(title, level))


def check_errors(ignore_missing_references: bool = False) -> list[dict[str, Any]]:
    result = check_skill(SKILL_DIR)
    errors = [d for d in result["diagnostics"] if d["severity"] == "error"]
    if ignore_missing_references:
        errors = [d for d in errors if d["code"] != "RESOURCE_PATH_INVALID"]
    return errors
