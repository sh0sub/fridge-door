"""Issue #20 (checker 0 error / 0 warning) and #22 (package structure, references 4 files, ZIP limits)."""

from __future__ import annotations

import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from scripts.build_zip import BuildError, build
from scripts.check import PLAN_FORBIDDEN, check_skill
from tests.skill_helpers import ROOT, SKILL_DIR, SKILL_MD, skill_text

REFS = ("README.md", "digest-format.md", "disclosures.md", "test-plan.md")


def package_sources() -> dict[str, str]:
    return {p.relative_to(SKILL_DIR).as_posix(): p.read_text(encoding="utf-8") for p in SKILL_DIR.rglob("*.md")}


# ---- #20 ------------------------------------------------------------------

def test_20_checker_zero_errors_zero_warnings() -> None:
    result = check_skill(SKILL_DIR)
    assert result["diagnostics"] == []
    assert result["status"] == "static-pass"


def test_20_official_layer_alone_passes() -> None:
    assert check_skill(SKILL_DIR, plan=False)["status"] == "static-pass"


def test_20_plan_grep_zero_hits_everywhere() -> None:
    hits = [(f, i) for f, s in package_sources().items() for i, line in enumerate(s.splitlines(), 1) if PLAN_FORBIDDEN.search(line)]
    assert hits == []


def test_20_frontmatter_and_description() -> None:
    text = skill_text()
    front = text.split("---")[1].strip().splitlines()
    assert [line.split(":")[0] for line in front] == ["name", "description"]
    assert front[0] == "name: fridge-door" and SKILL_DIR.name == "fridge-door"
    desc = front[1].split(":", 1)[1].strip()
    assert len(desc) <= 1024 and "Use when" in desc
    assert not re.search(r"\bbest\b", text, re.I)  # S3: no superlatives


def test_20_body_line_target_and_fences() -> None:
    body = skill_text().split("---", 2)[2]
    assert len(body.strip().splitlines()) <= 300
    for source in package_sources().values():
        assert not re.search(r"^```\s*\w", source, re.M)  # no language-tagged fences at all


def test_20_all_delegates_single_line_single_quoted() -> None:
    for line in skill_text().splitlines():
        if "delegate --" in line:
            assert line.startswith("`delegate --target ") and line.endswith("'`"), line
            assert line.count("--instruction") == 1 and line.count("--target") == 1


def test_20_cli_entry_point(tmp_path: Path) -> None:
    out = subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "check.py"), str(SKILL_DIR), "--summary"],
                         capture_output=True, text=True, check=False)
    assert out.returncode == 0 and "static-pass: 0 error, 0 warning" in out.stdout


# ---- #22 ------------------------------------------------------------------

def test_22_root_has_only_skill_and_references() -> None:
    assert sorted(p.name for p in SKILL_DIR.iterdir()) == ["SKILL.md", "references"]
    assert sorted(p.name for p in (SKILL_DIR / "references").iterdir()) == sorted(REFS)


def test_22_every_reference_linked_from_skill() -> None:
    text = SKILL_MD.read_text(encoding="utf-8")
    for name in REFS:
        assert f"[references/{name}](references/{name})" in text


def test_22_readme_contents() -> None:
    text = (SKILL_DIR / "references" / "README.md").read_text(encoding="utf-8")
    for heading in ("## Who it is for", "## Install", "## What it reads and writes", "## Example requests", "## Weekly use",
                    "## Remove", "## Version history"):
        assert heading in text
    examples = text.split("## Example requests")[1].split("##")[0]
    lines = [line for line in examples.splitlines() if line.startswith("- ")]
    assert len(lines) == 6
    assert sum(bool(re.search(r"[가-힣]", line)) for line in lines) == 3  # 3 EN + 3 KO
    assert "0.9.0" in text and "not an official UGREEN product" in text


def test_22_digest_format_has_seven_sections_and_example() -> None:
    text = (SKILL_DIR / "references" / "digest-format.md").read_text(encoding="utf-8")
    layout = text.split("## Fixed layout")[1].split("```")[1]
    sections = [line[3:] for line in layout.splitlines() if line.startswith("## ")]
    assert len(sections) == 7
    example = text.split("## Example")[1].split("```")[1]
    assert [line[3:] for line in example.splitlines() if line.startswith("## ")] == sections
    assert "- [ ] 2026-10-31" in example


def test_22_disclosures_contents() -> None:
    text = (SKILL_DIR / "references" / "disclosures.md").read_text(encoding="utf-8")
    for agent, cli in (("file-agent", "ug-filesystem"), ("file-agent", "ug-filemgr"), ("photo-agent", "ug-photo"),
                       ("document-agent", "ug-document"), ("knowledge-agent", "ug-knowledge")):
        assert f"| {agent} | {cli} |" in text
    assert "## Third-party components\n\nNone." in text
    assert "Claude Code" in text and "uliya-skill-kit 0.7.3" in text and "## Developed during the hackathon" in text


def test_22_test_plan_contents() -> None:
    text = (SKILL_DIR / "references" / "test-plan.md").read_text(encoding="utf-8")
    for heading in ("## Timebox", "## Core 1", "## Core 2", "## Edge", "## Fallback table", "## Expected results"):
        assert heading in text
    assert text.count("| 17:00 |") == 1 and "| 03:00 |" in text


def test_22_zip_build_and_limits(tmp_path: Path) -> None:
    out = tmp_path / "fridge-door.zip"
    info = build(SKILL_DIR, out)
    assert info["files"] == 5 and info["zip_bytes"] < 60 * 1024 and info["warnings"] == 0
    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
        assert all(n.startswith("fridge-door/") for n in names)
        assert not any("__MACOSX" in n or "/." in n for n in names)
        assert all(i.file_size <= 1024 * 1024 for i in zf.infolist())
    again = tmp_path / "again.zip"
    build(SKILL_DIR, again)
    assert again.read_bytes() == out.read_bytes()  # reproducible


def test_22_zip_refuses_broken_package(tmp_path: Path) -> None:
    broken = tmp_path / "fridge-door"
    (broken / "references").mkdir(parents=True)
    (broken / "SKILL.md").write_text("no frontmatter\n", encoding="utf-8")
    with pytest.raises(BuildError):
        build(broken, tmp_path / "x.zip")
