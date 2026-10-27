"""Issue #3-#12 (M1-M10): SKILL.md content matches the acceptance criteria in docs/plan.md §05."""

from __future__ import annotations

import re

from tests.skill_helpers import check_errors, delegates, delegates_in, section, skill_text


def test_skill_has_no_checker_errors_besides_missing_references() -> None:
    assert check_errors(ignore_missing_references=True) == []


# ---- #3 M1 input collection ------------------------------------------------

def test_m1_five_inputs_with_defaults() -> None:
    req = section("Required input")
    for name in ("source_folder", "period", "children", "parent_language", "output_folder"):
        assert f"`{{{name}}}`" in req, name
    assert "last 7 days" in req
    assert "Default: a subfolder named Fridge Door inside `{source_folder}`" in req
    assert "Default: the language the user is speaking" in req  # flow B: English request -> English summaries


def test_m1_missing_value_asks_and_reads_back() -> None:
    req = section("Required input")
    assert "`waiting_user`" in req
    assert "do not guess" in req and "never fill it with a guess" in req
    assert "Shall I go ahead?" in req and "Photos/PhoneBackup" in req and "Mina and Jun" in req


def test_m1_no_delegate_in_input_collection() -> None:
    assert delegates(section("Required input")) == []


# ---- #4 M2 inventory ------------------------------------------------------

def test_m2_inventory_delegate() -> None:
    d = delegates_in("Step 1")
    assert [x.target for x in d] == ["file-agent", "photo-agent"]
    first = d[0].instruction
    for phrase in ("image files", "{period}", "depth 2", "full path, size and modification time", "at most 12 files",
                   "how many files match in total", "Only read", "return an empty list"):
        assert phrase in first, phrase


def test_m2_limit_empty_and_fallback() -> None:
    step = section("Step 1", 2)
    assert "More than 12 matching photos" in step and "narrow `{period}`" in step and "`waiting_user`" in step
    assert "no results" in step and "Do not search other folders or widen the period" in step
    assert "finish as `completed` with nothing created" in step
    assert "Only if this step ends as `failed`" in step  # fallback is search by folder in Photos (risk R2)
    assert "{source_folder}" in delegates_in("Step 1")[1].instruction


# ---- #5 M3 processing history ---------------------------------------------

def test_m3_tag_lookup_read_only() -> None:
    (d,) = delegates_in("Step 2")
    assert d.target == "file-agent"
    assert "fridge-door-done" in d.instruction and "{photo_list}" in d.instruction
    assert "Only read; do not create or change tags" in d.instruction
    assert "return an empty list" in d.instruction


def test_m3_new_only_and_nothing_new_ends() -> None:
    step = section("Step 2", 2)
    assert "`{new_photos}`" in step and "already done" in step
    assert "nothing new in this period" in step and "finish as `completed` with nothing created" in step


# ---- #6 M4 OCR ------------------------------------------------------------

def test_m4_ocr_per_photo() -> None:
    (d,) = delegates_in("Step 3")
    assert d.target == "photo-agent"
    assert "OCR" in d.instruction and "{photo_path}" in d.instruction
    assert "do not add text that is not in the image" in d.instruction
    assert "return an empty result" in d.instruction


def test_m4_three_way_sort_and_unreadable() -> None:
    step = section("Step 3", 2)
    assert "`{notice_items}`" in step and "candidate artwork" in step and "`{unrelated_items}`" in step
    assert "receipt" in step and "`{unreadable_items}`" in step and "Never guess" in step
    assert "real OCR result" in step  # described as real result, no guessed JSON field names
    assert not re.search(r"\b(?:ocr_result|\.text|json)\b", step, re.I)


# ---- #7 M5 notice structuring ---------------------------------------------

def test_m5_fields_quotes_and_flags() -> None:
    step = section("Step 5", 2).split("### ")[0]
    for phrase in ("title", "sender (school and class)", "due, event, payment", "reply slip, item to bring, payment, event",
                   "amount", "the child it concerns", "source file name", "Quote the original date text",
                   '"needs check"', "earlier than `{today}` as past"):
        assert phrase in step, phrase


def test_m5_condense_long_text() -> None:
    (d,) = delegates(section("Step 5", 2).split("### ")[0])
    assert d.target == "document-agent"
    assert "Condense" in d.instruction and "word for word" in d.instruction and "do not save any file" in d.instruction
    assert "400 words" in section("Step 5", 2)


# ---- #8 M6 artwork check --------------------------------------------------

def test_m6_vlm_yes_no_caption() -> None:
    (d,) = delegates_in("Step 4")
    assert d.target == "photo-agent"
    assert "YES if it shows a drawing, painting or craft made by a child, otherwise NO" in d.instruction
    assert "one sentence naming the main subject and colours" in d.instruction
    assert "Do not guess the name or age" in d.instruction


def test_m6_no_is_unrelated_and_name_matching() -> None:
    step = section("Step 4", 2)
    assert "NO: add to `{unrelated_items}`" in step
    assert "contains a name from `{children}`" in step
    assert "`{unknown_artwork}`" in step and "`waiting_user`" in step


# ---- #9 M7 albums ---------------------------------------------------------

def test_m7_album_names_and_lookup_first() -> None:
    (lookup,) = delegates_in("Step 6")
    assert lookup.target == "photo-agent" and "albums whose name contains {album_name}" in lookup.instruction
    preview = section("Step 6", 2)
    assert '"School notices {year-month}"' in preview and '"Artwork – {child} {year}"' in preview
    assert "ask whether to add the photos to it" in preview


def test_m7_create_after_approval_with_fallback() -> None:
    create, fallback = delegates_in("Step 7")
    assert create.target == fallback.target == "photo-agent"
    assert "{album_paths}" in create.instruction and "real album identifier" in create.instruction
    assert "Do not move, copy or delete any file" in create.instruction
    step = section("Step 7", 2)
    assert "`waiting_approval`" in step and "counts as `cancelled`" in step and "saving the digest only" in step
    assert "{source_folder}" in fallback.instruction and "{period}" in fallback.instruction
    assert "ask first (`waiting_user`)" in step


# ---- #10 M8 digest --------------------------------------------------------

def test_m8_save_digest() -> None:
    (d,) = delegates_in("Step 8")
    assert d.target == "knowledge-agent"
    assert "Fridge Door – {period}" in d.instruction and "{output_folder}" in d.instruction
    assert "Do not overwrite an existing file" in d.instruction and "{digest_text}" in d.instruction
    step = section("Step 8", 2)
    assert "[references/digest-format.md](references/digest-format.md)" in step
    assert "seven sections in fixed order" in step
    assert "only after the expert returns `completed`" in step


# ---- #11 M9 tags ----------------------------------------------------------

def test_m9_tag_only_completed() -> None:
    (d,) = delegates_in("Step 9")
    assert d.target == "file-agent" and "fridge-door-done" in d.instruction and "{handled_paths}" in d.instruction
    assert "Do not remove any other tag" in d.instruction
    step = section("Step 9", 2)
    assert "album that ended `completed`" in step and "digest saved as `completed`" in step
    assert "Unrelated, unreadable and failed photos are never tagged" in step


# ---- #12 M10 report and states -------------------------------------------

def test_m10_all_five_states_handled() -> None:
    done = section("Completion and failure")
    for token in ("completed", "failed", "cancelled", "waiting_user", "waiting_approval"):
        assert f"- `{token}`:" in done, token


def test_m10_empty_partial_and_report() -> None:
    done = section("Completion and failure")
    assert "Empty and partial results" in done and "list the rest by file name" in done
    assert "Never say an album exists or a file was saved unless" in done
    report = section("Step 11", 2)
    assert "Report only real results" in report and "could not be read" in report
    assert "1 receipt was left untouched" in report


def test_mvp_delegates_use_only_planned_agents() -> None:
    assert {d.target for d in delegates()} <= {"file-agent", "photo-agent", "document-agent", "knowledge-agent"}
    assert "never runs `cli.invoke` itself" in skill_text()
