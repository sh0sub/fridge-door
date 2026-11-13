"""SKILL.md optional and secondary features: archive, translated copy, questions about saved digests, artwork journal, safety text."""

from __future__ import annotations

from tests.skill_helpers import SKILL_MD, delegates, section, skill_text

# ---- archive (off by default) ---------------------------------------------

def test_archive_is_off_by_default() -> None:
    req = section("Required input")
    assert "`{archive_past}`: off. Turn it on only when the user explicitly asks" in req
    step = section("Step 13", 2)
    assert "(optional, off by default)" in skill_text()
    assert "only when `{archive_past}` is on" in step and "without an explicit request it never runs" in step
    assert "`{output_folder}/Archive {year-month}`" in step


def test_archive_moves_past_notices_after_approval() -> None:
    (d,) = delegates(section("Step 13", 2))
    assert d.target == "file-agent"
    assert "{archive_folder}" in d.instruction and "{past_notice_paths}" in d.instruction
    assert "do not delete anything" in d.instruction and "Do not overwrite" in d.instruction
    step = section("Step 13", 2)
    assert "ask the user in the chat and wait for a yes" in step and "`waiting_approval`" in step


def test_safety_text_keeps_originals_principle() -> None:
    safety = section("Completion and failure").split("Safety:")[1]
    assert "original photos are read only" in safety and "moved only by the optional archive step" in safety
    assert "calls no outside service" in safety


# ---- translated copy (off by default) -------------------------------------

def test_translated_copy_only_on_request_from_saved_path() -> None:
    req = section("Required input")
    assert "`{copy_language}`: none. Set it only when the user explicitly asks" in req
    (d,) = delegates(section("Step 14", 2))
    assert d.target == "document-agent"
    assert "Translate the document at exactly {saved_path} into {copy_language}" in d.instruction
    assert "Leave the original file unchanged" in d.instruction and "say so clearly" in d.instruction
    step = section("Step 14", 2)
    assert "`{saved_path}` is a verified save" in step and "no translated copy was made" in step


def test_summaries_are_never_delegated_for_translation() -> None:
    docs = [d for d in delegates() if d.target == "document-agent"]
    assert len(docs) == 2  # the translated copy and the artwork journal, both reading real saved files
    for d in docs:
        assert "{saved_path}" in d.instruction or "{output_folder_path}" in d.instruction  # real saved files, never free text
        assert "{notice_summary}" not in d.instruction and "{ocr_text}" not in d.instruction and "{digest_text}" not in d.instruction


# ---- questions about saved digests ----------------------------------------

def test_questions_section_reuses_step1_and_cites_sources() -> None:
    part = section("Questions about saved digests", 2)
    assert delegates(part) == []
    assert "do not read the photos again" in part and "Run the two delegations of Step 1" in part
    assert "name the digest file and the source photo file" in part
    assert "no digest exists, say so and offer to sort" in part and "nothing is created" in part


def test_description_mentions_questions_and_journal() -> None:
    desc = skill_text().split("---")[1]
    assert "asks about a saved digest" in desc and "when is the field trip fee due?" in desc
    assert "asks to make an art journal" in desc and "make Mina's art journal" in desc
    assert len(desc.split("description:", 1)[1].strip()) <= 1024


# ---- artwork journal (on request) -------------------------------------------

def test_journal_asks_document_agent_for_verbatim_lines() -> None:
    query, fallback, save = delegates(section("Artwork journal", 2))
    assert query.target == "document-agent" and "{output_folder_path}" in query.instruction and "{child}" in query.instruction
    for phrase in ("starts with fridge-door-digest", "leaving out translated copies", "every line in the Artwork section that names {child}",
                   "exactly as written, in date order", "file name of the digest it came from", "Do not summarise, rewrite",
                   "Only read", "Name any document you could not read", "say clearly that none was found"):
        assert phrase in query.instruction, phrase
    assert fallback.target == "file-agent" and "8 created most recently" in fallback.instruction and "Only read" in fallback.instruction
    assert save.target == "knowledge-agent" and "file name hint fridge-door-journal" in save.instruction
    assert "{journal_text}" in save.instruction and "{output_folder_path}" in save.instruction


def test_journal_uses_only_returned_lines_and_saves_on_request() -> None:
    part = section("Artwork journal", 2)
    assert "Run the first delegation of Step 1 to get `{output_folder_path}`" in part
    assert "say that only the N most recent digests (at most 8) were checked" in part and "read delegation of Step 1" in part
    assert 'the title "Artwork journal - {child}"' in part and "Add nothing that is not in `{journal_lines}`" in part
    assert "If there are none, say so and create nothing" in part
    assert "Only if the user wants it saved" in part and "`waiting_approval`" in part and "only the real path" in part


def test_digest_artwork_line_carries_child_words() -> None:
    fmt = (SKILL_MD.parent / "references" / "digest-format.md").read_text(encoding="utf-8")
    assert 'Said: "{child_note}"' in fmt and "only when the parent told you" in fmt


def test_gallery_cards_match_package() -> None:
    import re
    from pathlib import Path

    gal = Path(__file__).resolve().parent.parent / "docs/submission/gallery"
    html = (gal / "00-chat.html").read_text()
    preview, done = html.split("2 &middot; COMPLETION")
    block = preview.split("Artwork (2)")[1].split("Not related")[0]
    assert len(re.findall(r"IMG_\d{4}\.jpg", block)) == 2
    assert "Not related / unreadable (1)</div>" in preview
    assert "unknown, please tell me" in preview and "which child made IMG_0107.jpg?" in preview
    assert "If your child said something about a drawing" in preview
    assert "tag the 7 photos it lists" in preview and "0 left for later" in preview
    assert "1 drawing into Photos/PhoneBackup/Fridge Door/Artwork - Mina" in preview
    assert "album Artwork - Mina, which follows its keepsake folder" in preview and "Artwork - Jun" not in html
    assert "IMG_0107 is Mina&#x27;s" in html or "IMG_0107 is Mina's" in html
    assert "Done. 3 deadlines, 1 event, 2 artworks." in done
    assert "2 copies in Photos/PhoneBackup/Fridge Door/Artwork - Mina" in done
    assert "Album 'Artwork - Mina' &middot; 2 photos" in done and "Tagged 7 photos" in done
    assert "It goes to the rainbow!" in done
    # 4 notices + 2 drawings + 1 receipt = 7 photos read = 7 tagged
    assert "7 photos read" in preview
    assert "This Skill asked only the NAS experts; the AI model they use is the one the NAS owner set up" in done
    for name in ("00-chat", "02-digest"):
        assert "Simulated dry run, not a device screenshot" in (gal / f"{name}.html").read_text()
    for card in gal.glob("*.html"):
        text = card.read_text()
        assert "Nothing leaves" not in text and "entirely on the device" not in text
        assert "stayed on this NAS" not in text and "create-album<" not in text
        assert "School notices 2026" not in text
        sizes = [float(s) for s in re.findall(r"font-size:(\d+(?:\.\d+)?)px", text)]
        assert all(s >= 12 for s in sizes), (card.name, min(sizes))
