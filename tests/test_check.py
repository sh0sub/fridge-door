"""Unit tests for scripts/check.py: one case per checker trap listed in docs/plan.md §01."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from scripts.check import CATALOG_VERSION, FULL_PROFILE_CLI_AGENTS, check_skill, main, validate_catalog

MINIMAL = """---
name: demo-skill
description: A weekly list of new photos in one folder. Use when a user says "list my new photos".
---

# Goal

List new photos. For the guide, read [references/README.md](references/README.md).

# Required input

1. `{folder}`: the folder.

# Generation-time capability evidence

- `ug-filesystem` → `file-agent`

# Workflow

`delegate --target file-agent --instruction 'List image files in {folder}. If nothing matches, return an empty list.'`

Use only the real result from the step before (upstream). If there are no results, say so and stop.

# Completion and failure

Handle completed, failed, cancelled, waiting_user and waiting_approval.
"""


def make_skill(tmp_path: Path, skill: str = MINIMAL, name: str = "demo-skill",
               refs: dict[str, str] | None = None) -> Path:
    root = tmp_path / name
    (root / "references").mkdir(parents=True)
    (root / "SKILL.md").write_text(skill, encoding="utf-8")
    for rel, text in (refs if refs is not None else {"README.md": "# Guide\n\nHow to use it.\n"}).items():
        (root / "references" / rel).write_text(text, encoding="utf-8")
    return root


def codes(result: dict[str, Any], severity: str | None = None) -> set[str]:
    return {d["code"] for d in result["diagnostics"] if severity is None or d["severity"] == severity}


def official(root: Path) -> dict[str, Any]:
    return check_skill(root, plan=False)


def test_minimal_skill_passes_official(tmp_path: Path) -> None:
    result = official(make_skill(tmp_path))
    assert result["status"] == "static-pass", result["diagnostics"]


def test_root_readme_is_rejected(tmp_path: Path) -> None:
    root = make_skill(tmp_path)
    (root / "README.md").write_text("x", encoding="utf-8")
    assert "RESOURCE_UNSUPPORTED" in codes(official(root), "error")


def test_frontmatter_extra_key(tmp_path: Path) -> None:
    root = make_skill(tmp_path, MINIMAL.replace("name: demo-skill", "name: demo-skill\nversion: 1"))
    assert "SKILL_FRONTMATTER_INVALID" in codes(official(root), "error")


def test_name_must_match_directory(tmp_path: Path) -> None:
    root = make_skill(tmp_path, name="other-dir")
    assert "SKILL_NAME_MISMATCH" in codes(official(root), "error")


def test_description_without_trigger_warns(tmp_path: Path) -> None:
    root = make_skill(tmp_path, MINIMAL.replace(' Use when a user says "list my new photos".', ""))
    assert "DESCRIPTION_TRIGGER_MISSING" in codes(official(root), "warning")


def test_ascii_arrow_is_not_evidence(tmp_path: Path) -> None:
    root = make_skill(tmp_path, MINIMAL.replace("→", "->"))
    assert "CAPABILITY_EVIDENCE_MISSING" in codes(official(root), "error")


def test_evidence_agent_mismatch(tmp_path: Path) -> None:
    root = make_skill(tmp_path, MINIMAL.replace("`ug-filesystem` → `file-agent`", "`ug-filesystem` → `photo-agent`"))
    assert "CAPABILITY_EVIDENCE_AGENT_MISMATCH" in codes(official(root), "error")


def test_delegate_double_quotes_and_pipe(tmp_path: Path) -> None:
    bad = MINIMAL.replace("'List image files in {folder}. If nothing matches, return an empty list.'",
                          '"List image files"')
    assert "DELEGATE_FORMAT_INVALID" in codes(official(make_skill(tmp_path, bad)), "error")
    piped = MINIMAL.replace("empty list.'`", "empty list.' | sort`")
    assert "DELEGATE_FORMAT_INVALID" in codes(official(make_skill(tmp_path / "p", piped)), "error")


def test_delegate_unknown_target(tmp_path: Path) -> None:
    root = make_skill(tmp_path, MINIMAL.replace("--target file-agent", "--target files-agent"))
    assert {"DELEGATE_TARGET_UNKNOWN", "SECURITY_UNREGISTERED_AGENT"} <= codes(official(root), "error")


def test_missing_status_token(tmp_path: Path) -> None:
    root = make_skill(tmp_path, MINIMAL.replace(" and waiting_approval", ""))
    assert "DELEGATION_RESULT_HANDLING_MISSING" in codes(official(root), "error")


def test_missing_empty_result_warns(tmp_path: Path) -> None:
    text = MINIMAL.replace(" If nothing matches, return an empty list.", "").replace(
        " If there are no results, say so and stop.", "")
    assert "EMPTY_RESULT_HANDLING_MISSING" in codes(official(make_skill(tmp_path, text)), "warning")


def test_angle_placeholder_in_instruction_warns(tmp_path: Path) -> None:
    root = make_skill(tmp_path, MINIMAL.replace("in {folder}.", "in <folder>."))
    assert "DELEGATE_DYNAMIC_VALUE_UNRESOLVED" in codes(official(root), "warning")


def test_nas_path_outside_delegate(tmp_path: Path) -> None:
    root = make_skill(tmp_path, MINIMAL.replace("List new photos.", "List new photos in /volume1/photos."))
    assert "SECURITY_DIRECT_FILE_ACCESS" in codes(official(root), "error")


def test_hardcoded_home_warns(tmp_path: Path) -> None:
    root = make_skill(tmp_path, MINIMAL.replace("in {folder}.", "in /home/alice/photos."))
    assert "DELEGATE_HARDCODED_HOME_PATH" in codes(official(root), "warning")


@pytest.mark.parametrize("phrase,code", [
    ("Never use curl here.", "SECURITY_REMOTE_DOWNLOAD"),
    ("A cat sat on the mat.", "SECURITY_DIRECT_FILE_ACCESS"),
    ("Mention the request-id.", "SECURITY_INTERNAL_CAPABILITY"),
    ("You may bypass the approval step.", "SECURITY_GATEWAY_BYPASS"),
    ("Run cli.invoke yourself.", "RUNTIME_DIRECT_CLI_INVOKE"),
    ("password = \"hunter2\"", "SECURITY_CREDENTIAL_LITERAL"),
    ("TODO finish", "SKILL_PLACEHOLDER_REMAINS"),
])
def test_forbidden_phrases(tmp_path: Path, phrase: str, code: str) -> None:
    root = make_skill(tmp_path, MINIMAL.replace("List new photos.", "List new photos. " + phrase))
    assert code in codes(official(root), "error")


def test_negated_cli_invoke_is_allowed(tmp_path: Path) -> None:
    root = make_skill(tmp_path, MINIMAL.replace("List new photos.", "The Skill never runs `cli.invoke` itself."))
    assert "RUNTIME_DIRECT_CLI_INVOKE" not in codes(official(root))


def test_runtime_fence_in_reference(tmp_path: Path) -> None:
    root = make_skill(tmp_path, refs={"README.md": "```bash\nls\n```\n"})
    assert "SECURITY_SCRIPT_EXECUTION_UNSUPPORTED" in codes(official(root), "error")


def test_unlinked_reference_warns_and_script_rejected(tmp_path: Path) -> None:
    root = make_skill(tmp_path, refs={"README.md": "ok\n", "extra.md": "ok\n", "run.sh": "ls\n"})
    result = official(root)
    assert "RESOURCE_UNREFERENCED" in codes(result, "warning")
    assert "RESOURCE_UNSUPPORTED" in codes(result, "error")


def test_missing_required_section(tmp_path: Path) -> None:
    root = make_skill(tmp_path, MINIMAL.replace("# Completion and failure", "# Wrap up"))
    assert "SKILL_REQUIRED_SECTION_MISSING" in codes(official(root), "error")


def test_symlink_in_references(tmp_path: Path) -> None:
    root = make_skill(tmp_path)
    (root / "references" / "link.md").symlink_to(root / "references" / "README.md")
    assert "RESOURCE_PATH_INVALID" in codes(official(root), "error")


# ---- plan layer -----------------------------------------------------------

def test_plan_forbidden_literal_grep(tmp_path: Path) -> None:
    root = make_skill(tmp_path, MINIMAL.replace("List new photos.", "Please confirm the folder."))
    result = check_skill(root)
    hits = [d for d in result["diagnostics"] if d["code"] == "PLAN_FORBIDDEN_TERM"]
    assert hits and hits[0]["line"] == 8


def test_plan_value_lint(tmp_path: Path) -> None:
    text = MINIMAL.replace("in {folder}.", "in {folder} for {period}.")
    result = check_skill(make_skill(tmp_path, text))
    assert "PLAN_VALUE_UNDECLARED" in codes(result, "error")
    unused = MINIMAL.replace("1. `{folder}`: the folder.", "1. `{folder}`: the folder.\n2. `{spare}`: unused.")
    assert "PLAN_VALUE_UNUSED" in codes(check_skill(make_skill(tmp_path / "u", unused)), "warning")


def test_plan_quote_escape(tmp_path: Path) -> None:
    ok = MINIMAL.replace("List image files", "List the child'\"'\"'s image files")
    assert "PLAN_QUOTE_UNESCAPED" not in codes(check_skill(make_skill(tmp_path, ok)))
    assert "DELEGATE_FORMAT_INVALID" not in codes(check_skill(make_skill(tmp_path / "o", ok)))
    # check-lib.mjs 0.7.7 only knows the '"'"' sequence; '\'' cuts its instruction short, so the plan layer rejects it
    old = MINIMAL.replace("List image files", "List the child'\\''s image files")
    assert "PLAN_QUOTE_UNESCAPED" in codes(check_skill(make_skill(tmp_path / "q", old)), "error")


def test_plan_vague_reference(tmp_path: Path) -> None:
    text = MINIMAL.replace("List image files in {folder}.", "List image files in {folder} and that folder.")
    assert "PLAN_VAGUE_REFERENCE" in codes(check_skill(make_skill(tmp_path, text)), "warning")


def test_plan_reference_set_and_evidence_set(tmp_path: Path) -> None:
    result = check_skill(make_skill(tmp_path))
    assert "PLAN_REFERENCE_MISSING" in codes(result, "warning")
    assert "PLAN_EVIDENCE_SET" in codes(result, "warning")


def test_cli_exit_codes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(make_skill(tmp_path)), "--official", "--summary"]) == 0
    bad = make_skill(tmp_path / "b", MINIMAL.replace(" and waiting_approval", ""))
    assert main([str(bad), "--official"]) == 1
    assert "not-uploadable" in capsys.readouterr().out


# ---- capability catalog (kit 0.7.7, structure 2.2.0) ----------------------

def synthetic_catalog(tmp_path: Path, version: str = "2.2.0", clis: list[dict[str, str]] | None = None) -> Path:
    """A minimal stand-in with the same CLI -> agent ownership; the kit's catalog itself is not copied here."""
    path = tmp_path / "catalog.json"
    items = clis if clis is not None else [{"name": n, "agent": a} for n, a in FULL_PROFILE_CLI_AGENTS.items()]
    path.write_text(json.dumps({"catalogVersion": version, "clis": items}), encoding="utf-8")
    return path


def test_catalog_version_is_220(tmp_path: Path) -> None:
    assert CATALOG_VERSION == "2.2.0"
    result = check_skill(make_skill(tmp_path), plan=False, catalog=synthetic_catalog(tmp_path))
    assert result["catalog"] == {"checkedVersion": "2.2.0"} and result["status"] == "static-pass"
    assert check_skill(make_skill(tmp_path / "n"), plan=False)["catalog"] == {"checkedVersion": "2.2.0"}


@pytest.mark.parametrize("version,clis,message", [
    ("2.0.0", None, "version must be 2.2.0"),
    ("2.2.0", [{"name": "ug-photo", "agent": "photo-agent"}], "incomplete"),
    ("2.2.0", [{"name": "ug-photo", "agent": "file-agent"}], "invalid full-profile CLI ownership mapping"),
    ("2.2.0", [{"name": "ug-photo", "agent": "ghost-agent"}], "unsupported full-profile subagent"),
    ("2.2.0", [{"name": "ug-photo"}], "invalid CLI ownership contract"),
    ("2.2.0", [{"name": "ug-photo", "agent": "photo-agent"}] * 2, "duplicate CLI names"),
])
def test_catalog_contract_errors(tmp_path: Path, version: str, clis: list[dict[str, str]] | None, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        validate_catalog(synthetic_catalog(tmp_path, version, clis))


def test_catalog_error_exit_code_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(make_skill(tmp_path)), "--catalog", str(synthetic_catalog(tmp_path, "2.0.0"))]) == 2
    assert "version must be 2.2.0" in capsys.readouterr().err


def test_file_workflow_evidence_line(tmp_path: Path) -> None:
    text = MINIMAL.replace("- `ug-filesystem` → `file-agent`", "- `ug-filesystem` → `file-agent`\n- `file-workflow` → `file-agent`")
    result = check_skill(make_skill(tmp_path, text), plan=False, catalog=synthetic_catalog(tmp_path))
    assert result["status"] == "static-pass"
    bad = MINIMAL.replace("- `ug-filesystem` → `file-agent`", "- `ug-filesystem` → `file-agent`\n- `file-workflow` → `photo-agent`")
    assert "CAPABILITY_EVIDENCE_AGENT_MISMATCH" in codes(official(make_skill(tmp_path / "b", bad)), "error")


@pytest.mark.skipif(not os.environ.get("FRIDGE_DOOR_KIT_CATALOG"), reason="set FRIDGE_DOOR_KIT_CATALOG to the kit's data/capability-catalog.json")
def test_real_kit_catalog_validates() -> None:
    from tests.skill_helpers import SKILL_DIR

    result = check_skill(SKILL_DIR, catalog=Path(os.environ["FRIDGE_DOOR_KIT_CATALOG"]))
    assert result["status"] == "static-pass" and result["diagnostics"] == []


# ---- JS whitespace (check-lib.mjs regexes see NBSP, U+2000-U+200A, U+3000 and BOM as \s) ----

@pytest.mark.parametrize("space", [" ", " ", "　", " ", "﻿"])
def test_unicode_space_counts_as_whitespace_like_js(tmp_path: Path, space: str) -> None:
    # a direct file command hidden behind a non-ASCII space is still caught
    root = make_skill(tmp_path, MINIMAL.replace("List new photos.", f"List new photos. Then run cat{space}notes.txt."))
    assert "SECURITY_DIRECT_FILE_ACCESS" in codes(official(root), "error")
    # an evidence line written with a non-ASCII space still counts as evidence
    spaced = MINIMAL.replace("- `ug-filesystem` → `file-agent`", f"-{space}`ug-filesystem`{space}→{space}`file-agent`")
    assert official(make_skill(tmp_path / "e", spaced))["status"] == "static-pass"


def test_unicode_space_before_extra_flag_is_rejected(tmp_path: Path) -> None:
    bad = MINIMAL.replace("--target file-agent --instruction", "--target file-agent --verbose --instruction")
    assert "DELEGATE_FORMAT_INVALID" in codes(official(make_skill(tmp_path, bad)), "error")


def test_js_pattern_keeps_any_char_class_and_ascii_word_boundaries() -> None:
    import re

    from scripts.check import JS_WHITESPACE_CHARS, js_pattern, js_re, js_trim

    assert js_re(r"^\s+$").match("　  \t") and not js_re(r"^\s+$").match("\x1c")  # \x1c is \s in Python, not in JS
    assert js_re(r"^\S+$").match("a\x85b")  # NEL is not JS whitespace
    assert js_re(r"[\s\S]+", re.S).fullmatch("a\nb　c")
    assert js_re(r"\bcat\b", re.ASCII).search("écat")  # ASCII \b like JS without the u flag: é is not a word character
    assert js_pattern(r"[^)\s]") == "[^)" + js_pattern(r"\s")[1:-1] + "]"
    assert js_trim("﻿ value　") == "value" and "\x85" not in JS_WHITESPACE_CHARS
    with pytest.raises(ValueError):
        js_pattern(r"[a\S]")
