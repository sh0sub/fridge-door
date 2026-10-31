"""Issue #13-#16 (S1-S4): Should features described in SKILL.md as docs/plan.md §05 says."""

from __future__ import annotations

from tests.skill_helpers import delegates, section, skill_text


def subsection(title: str) -> str:
    step5 = section("Step 5", 2)
    start = step5.index(f"### {title}")
    rest = step5[start + 4:]
    end = rest.find("### ")
    return rest if end == -1 else rest[:end]


# ---- #13 S1 translation ---------------------------------------------------

def test_s1_translate_summary_only() -> None:
    part = subsection("Translation")
    (d,) = delegates(part)
    assert d.target == "document-agent"
    assert "{parent_language}" in d.instruction and "{notice_summary}" in d.instruction
    assert "{ocr_text}" not in d.instruction  # summaries only, never the full text
    assert "Keep dates, amounts and names unchanged" in d.instruction
    assert "translate only its short summary, never the full text" in part


def test_s1_preview_row_and_failure() -> None:
    part = subsection("Translation")
    assert "original key line, translated summary, due date, action" in part
    assert "`waiting_approval`" in part
    assert "keep the original summary and say so in the digest" in part


# ---- #14 S2 archive (off by default) --------------------------------------

def test_s2_archive_is_off_by_default() -> None:
    req = section("Required input")
    assert "`{archive_past}`: off. Turn it on only when the user explicitly asks" in req
    step = section("Step 10", 2)
    assert "(optional, off by default)" in skill_text()
    assert "only when `{archive_past}` is on" in step and "without an explicit request it never runs" in step
    assert "`{source_folder}/Fridge Door/Archive {year-month}`" in step


def test_s2_archive_moves_past_notices_after_approval() -> None:
    (d,) = delegates(section("Step 10", 2))
    assert d.target == "file-agent"
    assert "{archive_folder}" in d.instruction and "{past_notice_paths}" in d.instruction
    assert "do not delete anything" in d.instruction and "Do not overwrite" in d.instruction
    step = section("Step 10", 2)
    assert "`waiting_user`" in step and "`waiting_approval`" in step


def test_s2_safety_text_keeps_originals_principle() -> None:
    safety = section("Completion and failure").split("Safety:")[1]
    assert "never renamed or deleted" in safety and "moved only by the optional archive step" in safety


# ---- #15 S3 child fallback ------------------------------------------------

def test_s3_people_album_fallback() -> None:
    part = subsection("Child fallback")
    (d,) = delegates(part)
    assert d.target == "photo-agent"
    assert "people albums that have a name" in d.instruction and "{children}" in d.instruction
    assert "{unknown_artwork}" in d.instruction and "face indexing is not finished" in d.instruction
    assert "Only read" in d.instruction


def test_s3_only_fills_gaps_then_asks() -> None:
    part = subsection("Child fallback")
    assert "Only when `{unknown_artwork}` is not empty" in part
    assert "`waiting_user`" in part and "only fills gaps" in part


# ---- #16 S4 weekly carry-over ---------------------------------------------

def test_s4_reads_previous_digest() -> None:
    part = subsection("Carry over open items")
    (d,) = delegates(part)
    assert d.target == "file-agent"
    assert "{output_folder}" in d.instruction and "starts with Fridge Door" in d.instruction
    assert "return its full text exactly as stored" in d.instruction and "Only read" in d.instruction


def test_s4_checked_items_are_done() -> None:
    part = subsection("Carry over open items")
    assert "(`- [ ]`)" in part and "`- [x]` count as done" in part and '"carried over"' in part
    assert "An empty result means there is nothing to carry over" in part


def test_gallery_preview_card_lists_every_counted_artwork() -> None:
    import re
    from pathlib import Path

    html = (Path(__file__).resolve().parent.parent / "docs/submission/gallery/00-chat.html").read_text()
    card = html.split("2 &middot; COMPLETION")[0]
    block = card.split("Artwork (2)")[1].split("Not related")[0]
    assert len(re.findall(r"IMG_\d{4}\.jpg", block)) == 2
    assert "Not related / unreadable (1)</div>" in card
    assert "tag handled photos" in card
