"""End-to-end dry runs of the v1.0.0 workflow against simulated expert answers.

Covers the newest digest first (creation time, translated copies and journals left out) and the
default period it gives, batches of 12 with "continue", narrowing when more than 60 photos match,
the tag as "handled once" (unrelated and unreadable photos too, failed ones never), copy then read
the keepsake folder, album from the real folder path and id, save to the real output folder path,
"Next run starts from", carried deadlines and upcoming events, a child's own words, the artwork
journal and its fallback, questions about saved digests, refused approvals (the resumed terminal
state comes from the fixture), Done / Partly done and the 16-photo test kit. Fixtures live in
tests/fixtures/dryrun/; variants are derived here.
"""

from __future__ import annotations

import copy
import json
import shlex
from pathlib import Path
from typing import Any

import pytest

from scripts.check import DELEGATE_CHAINING, EXTRA_FLAG
from scripts.dryrun import WRITE_KEYS, DryRunError, Outcome, digest_sections, load_templates, main, render, run_fixture

ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES = ROOT / "tests" / "fixtures" / "dryrun"
README = ROOT / "fridge-door" / "references" / "README.md"
DIGEST_FORMAT = ROOT / "fridge-door" / "references" / "digest-format.md"
P = "Photos/PhoneBackup/2026-11/"
K = "Photos/PhoneBackup/Kit/"
OUT = "Photos/PhoneBackup/Fridge Door"
KOUT = "Photos/PhoneBackup/Kit/Fridge Door"
REAL = "/volume1/homes/mom/Photos/PhoneBackup/Fridge Door"


def load(name: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    return data


def flow_a() -> dict[str, Any]:
    return load("flow-a")


def writes(out: Outcome) -> list[str]:
    return [c.key for c in out.calls if c.key in WRITE_KEYS]


def instruction(out: Outcome, key: str, index: int = -1) -> str:
    return shlex.split(out.calls_for(key)[index].command)[4]


def assert_commands_valid(out: Outcome) -> None:
    for call in out.calls:
        tokens = shlex.split(call.command)
        assert tokens[:3] == ["delegate", "--target", call.target] and tokens[3] == "--instruction" and len(tokens) == 5
        head = call.command.split("--instruction", 1)[0]
        assert not DELEGATE_CHAINING.search(head) and not EXTRA_FLAG.search(head.replace("--target", ""))


def previous_digest(lines: list[str], events: list[str] | None = None, start: str | None = "2026-11-23",
                    artwork: list[str] | None = None) -> str:
    meta = "Source: Photos/PhoneBackup · 5 photos read · Generated on NAS 2026-11-23 20:00" + (f" · Next run starts from: {start}" if start else "")
    return "\n".join(["# Fridge Door – 2026-11-16 to 2026-11-22", meta, "", "## At a glance", "- ...", "", "## Deadlines", *lines,
                      "", "## Events", *(events or ["No events this time."]), "", "## Artwork", *(artwork or ["No artwork this time."]), ""])


# ---- flow A: one batch, first album ----------------------------------------

def test_flow_a_weekly_digest() -> None:
    out = run_fixture(flow_a())
    assert out.status == "completed"
    assert_commands_valid(out)
    assert len(out.calls_for("ocr")) == 7 and len(out.calls_for("vlm")) == 2
    assert out.copied == [f"{OUT}/Artwork - Mina/IMG_0106.jpg", f"{OUT}/Artwork - Mina/IMG_0107.jpg"]
    assert [(a["name"], a["count"]) for a in out.albums] == [("Artwork - Mina", 2)]
    assert sorted(out.tagged) == [f"{P}IMG_010{i}.jpg" for i in range(2, 9)]  # the receipt is tagged too: handled once
    assert out.saved_path == f"{OUT}/fridge-door-digest_20261129_211405.md"
    assert out.report == "Done. 3 deadlines, 1 event, 2 artworks."
    assert out.approvals == ["copy_artwork:Mina", "create_album:Mina", "save_digest:", "tag_add:"]


def test_flow_a_order_digest_first_then_copy_list_album_save_tag() -> None:
    keys = [c.key for c in run_fixture(flow_a()).calls if c.status != "waiting_approval"]
    assert keys[:3] == ["find_digest", "list_photos", "tag_lookup"]
    assert keys[-7:] == ["album_lookup", "ensure_folder", "copy_artwork", "list_keepsake", "create_album", "save_digest", "tag_add"]


def test_flow_a_digest_follows_digest_format() -> None:
    out = run_fixture(flow_a())
    digest = out.digest or ""
    headings = [line[3:] for line in digest.splitlines() if line.startswith("## ")]
    assert headings == digest_sections() and len(headings) == 7
    deadlines = digest.split("## Deadlines")[1].split("\n## ")[0].strip().splitlines()
    assert [line[6:16] for line in deadlines] == ["2026-12-04", "2026-12-05", "2026-12-08"]
    assert all(line.startswith("- [ ] ") and ".jpg" in line for line in deadlines)
    assert '"12월 4일까지 납부"' in deadlines[0]
    assert "- IMG_0106.jpg · Mina · 2026-11-28 · A crayon drawing of a yellow school bus under a rainbow. · " in digest
    assert "name read on the drawing: 김민아 · copied" in digest and "chosen by the parent · copied" in digest
    assert f"Keepsake folder: {OUT}/Artwork - Mina · album Artwork - Mina: created" in digest
    assert "Run status when saved: every step before saving completed." in digest


def test_flow_a_nothing_written_before_preview_agreement() -> None:
    out = run_fixture(flow_a())
    keys = [c.key for c in out.calls]
    first_write = min(keys.index(k) for k in WRITE_KEYS if k in keys)
    assert keys.index("album_lookup") < first_write and keys.index("find_digest") < first_write
    assert out.preview and "nothing is moved or deleted" in out.preview


def test_flow_a_no_text_delegation_and_no_moves() -> None:
    out = run_fixture(flow_a())
    assert not [c for c in out.calls if c.target == "document-agent"]  # summaries are written by Uliya
    assert not out.calls_for("archive") and "Originals were not moved or deleted." in (out.digest or "")
    assert "School Banking" not in (out.digest or "")  # the summary says only what the notice line says


# ---- Step 1: newest digest, default period ----------------------------------

def test_default_period_without_digest_is_last_seven_days() -> None:
    out = run_fixture(flow_a())
    assert out.period == "2026-11-23 to 2026-11-29"
    assert out.questions[0].startswith("Folder Photos/PhoneBackup, 2026-11-23 to 2026-11-29, children Mina and Jun")
    assert "{period}" not in instruction(out, "list_photos") and "inside 2026-11-23 to 2026-11-29" in instruction(out, "list_photos")


def test_default_period_starts_where_the_last_digest_stopped() -> None:
    fx = flow_a()
    fx["nas_files"] = {f"{OUT}/fridge-door-digest_20261124_200000.md": previous_digest([], start="2026-11-24")}
    out = run_fixture(fx)
    assert out.period == "2026-11-24 to 2026-11-29"
    assert "2026-11-24 to 2026-11-29 (where the last digest stopped)" in out.questions[0]
    assert out.calls[0].key == "find_digest" and out.calls[1].key == "read_digest"  # before the read-back and the listing


def test_default_period_longer_than_31_days_asks() -> None:
    fx = flow_a()
    fx["nas_files"] = {f"{OUT}/fridge-door-digest_20261001_200000.md": previous_digest([], start="2026-10-01")}
    out = run_fixture(fx)
    assert out.status == "waiting_user" and "Which period should I look at?" in out.report
    assert not out.calls_for("list_photos") and writes(out) == []


def test_digest_without_start_date_uses_seven_days_and_still_carries() -> None:
    fx = flow_a()
    fx["nas_files"] = {f"{OUT}/fridge-door-digest_20261123_200000.md": previous_digest(
        ['- [ ] 2026-12-02 — Return the library book · Jun · "12월 2일까지" · IMG_0091.jpg'], start=None)}
    out = run_fixture(fx)
    assert out.period == "2026-11-23 to 2026-11-29" and len(out.carried) == 1
    assert "gives no start date, so this run looks at the last 7 days." in (out.digest or "")


def test_explicit_period_is_used_as_given() -> None:
    fx = flow_a()
    fx["inputs"]["period"] = "2026-11-20 to 2026-11-29"
    assert run_fixture(fx).period == "2026-11-20 to 2026-11-29"


def test_newest_digest_by_creation_time_not_translation_or_journal() -> None:
    fx = flow_a()
    older, newer = f"{OUT}/fridge-door-digest_20261116_200000.md", f"{OUT}/fridge-door-digest_20261123_200000.md"
    fx["nas_files"] = {
        older: {"text": previous_digest(['- [x] 2026-11-20 — Old item · Jun · "x" · IMG_0001.jpg'], start="2026-11-16"),
                "created": "2026-11-16 20:00", "modified": "2026-11-29 09:00"},  # the parent ticked a box last
        newer: {"text": previous_digest(['- [ ] 2026-12-02 — Newer item · Jun · "y" · IMG_0091.jpg'], start="2026-11-23"),
                "created": "2026-11-23 20:00", "modified": "2026-11-23 20:00"},
        f"{OUT}/fridge-door-digest_20261123_200000.en.md": {"text": "translated", "created": "2026-11-23 20:05"},
        f"{OUT}/fridge-door-journal_20261124_100000.md": {"text": "journal", "created": "2026-11-24 10:00"},
    }
    out = run_fixture(fx)
    assert f"Read the file at exactly {newer} and" in instruction(out, "read_digest")
    assert [c.split(" · carried over from ")[1] for c in out.carried] == ["fridge-door-digest_20261123_200000.md"]
    find = instruction(out, "find_digest")
    assert "choose by the timestamp in the file name; if the names carry none, by the time the file was created" in find
    assert "never by modification time" in find and ".en.md" in find and "fridge-door-journal" in find


def test_digest_names_without_timestamp_are_chosen_by_creation_time() -> None:
    fx = flow_a()
    older, newer = f"{OUT}/fridge-door-digest-b.md", f"{OUT}/fridge-door-digest-a.md"
    fx["nas_files"] = {older: {"text": previous_digest([], start="2026-11-16"), "created": "2026-11-16 20:00"},
                       newer: {"text": previous_digest([], start="2026-11-23"), "created": "2026-11-23 20:00"}}
    assert f"Read the file at exactly {newer} and" in instruction(run_fixture(fx), "read_digest")


def test_next_start_later_than_today_gives_today_alone() -> None:
    fx = flow_a()
    fx["nas_files"] = {f"{OUT}/fridge-door-digest_20261123_200000.md": previous_digest([], start="2026-12-05")}
    assert run_fixture(fx).period == "2026-11-29 to 2026-11-29"


# ---- batches and listing ------------------------------------------------------

def test_batches_of_twelve_wait_for_continue() -> None:
    fx = load("testkit")
    fx["user"]["continue"] = 0
    out = run_fixture(fx)
    assert len(out.batches) == 1 and len(out.batch.photos) == 12 and out.batch.remaining == 4
    assert "12 in this batch · 4 left for later" in (out.preview or "")
    assert "continue" not in out.questions and len(out.calls_for("ocr")) == 12
    assert "4 left for later" in out.completion_card


def test_continue_reads_only_the_rest() -> None:
    out = run_fixture(load("testkit"))
    assert [len(b.photos) for b in out.batches] == [12, 4]
    assert [p.rsplit("/", 1)[1] for p in out.batches[1].photos] == ["KIT_D03.jpg", "KIT_D04.jpg", "KIT_D05.jpg", "KIT_D06.jpg"]
    assert len(out.calls_for("tag_lookup")) == 1 and len(out.calls_for("list_photos")) == 1
    assert len(out.calls_for("ocr")) == 16  # nothing read twice
    assert len(out.calls_for("find_digest")) == 1  # batch 2 carries over from the digest batch 1 saved


def over_sixty(fx: dict[str, Any]) -> dict[str, Any]:
    fx["experts"]["list_photos"]["result"]["total"] = 75
    return fx


def test_listing_over_sixty_offers_narrowing_and_continues_when_declined() -> None:
    out = run_fixture(over_sixty(flow_a()))
    assert any(m.startswith("75 photos match; one run looks at 60. A folder that mostly holds school photos") for m in out.messages)
    assert "Shall I narrow the list to papers and drawings?" in out.questions and not out.calls_for("narrow_photos")
    assert "Next run starts from: 2026-11-29" in (out.digest or "")  # newest listed date, because the listing was cut


def test_narrowing_replaces_the_list() -> None:
    fx = over_sixty(flow_a())
    fx["user"]["narrow"] = True
    files = fx["experts"]["list_photos"]["result"]["files"]
    fx["experts"]["narrow_photos"] = {"status": "completed", "result": {"total": 3, "files": [files[i] for i in (2, 4, 6)]}}
    out = run_fixture(fx)
    (call,) = out.calls_for("narrow_photos")
    assert call.target == "photo-agent" and "paper document with printed or handwritten text" in shlex.split(call.command)[4]
    assert out.photos_found == 3 and [p.rsplit("/", 1)[1] for p in out.batch.photos] == ["IMG_0102.jpg", "IMG_0104.jpg", "IMG_0106.jpg"]
    assert "Narrowed to 3 paper or drawings." in out.messages


def test_narrowing_failure_continues_with_oldest_sixty() -> None:
    fx = over_sixty(flow_a())
    fx["user"]["narrow"] = True
    fx["experts"]["narrow_photos"] = {"status": "completed", "result": {"summary": "The library has not finished recognising these photos."}}
    out = run_fixture(fx)
    assert "Narrowing did not work, so this run continues with the oldest 60." in out.messages
    assert out.status == "completed" and len(out.batch.photos) == 7


def test_listing_must_leave_out_the_output_folder() -> None:
    fx = flow_a()
    fx["experts"]["list_photos"]["result"]["files"].append({"path": f"{OUT}/Artwork - Mina/IMG_0050.jpg"})
    with pytest.raises(DryRunError, match="output folder"):
        run_fixture(fx)


def test_fallback_listing_says_when_fewer_paths_than_total() -> None:
    fx = flow_a()
    fx["experts"]["list_photos_fallback"] = copy.deepcopy(fx["experts"]["list_photos"])
    fx["experts"]["list_photos_fallback"]["result"]["total"] = 25
    fx["experts"]["list_photos"] = {"status": "failed", "result": {"reason": "folder is a library view"}}
    out = run_fixture(fx)
    assert "The photo expert returned 9 paths of 25 matching photos." in out.messages


# ---- Step 3: tags --------------------------------------------------------------

def test_tag_exists_but_no_listed_file_carries_it() -> None:
    fx = flow_a()
    fx["experts"]["tag_lookup"] = {"status": "completed", "result": {"tag_exists": True, "none_carry": True,
                                                                     "summary": "None of these files carry fridge-door-done."}}
    for name in ("IMG_0100.jpg", "IMG_0101.jpg"):
        fx["experts"]["ocr"][name] = {"status": "completed", "result": {"text": "편의점\n물 1,000\n합계 1,000\n카드\n승인"}}
    out = run_fixture(fx)
    assert out.already_done == [] and len(out.calls_for("ocr")) == 9
    assert not any("may appear again" in q for q in out.questions + out.messages)


@pytest.mark.parametrize("answer", [{"status": "failed", "result": {"reason": "tag service down"}}, {"status": "completed", "result": {}}])
def test_tag_lookup_failure_or_unclear_asks_then_continues(answer: dict[str, Any]) -> None:
    fx = flow_a()
    fx["experts"]["tag_lookup"] = answer
    for name in ("IMG_0100.jpg", "IMG_0101.jpg"):
        fx["experts"]["ocr"][name] = {"status": "completed", "result": {"text": "편의점\n물 1,000\n합계 1,000\n카드\n승인"}}
    out = run_fixture(fx)
    assert any("photos handled before may appear again. Continue?" in q for q in out.questions)
    assert out.status == "completed" and len(out.calls_for("ocr")) == 9


def test_tag_lookup_failure_and_user_stops() -> None:
    fx = flow_a()
    fx["experts"]["tag_lookup"] = {"status": "failed", "result": {"reason": "tag service down"}}
    fx["user"]["continue_without_tags"] = False
    out = run_fixture(fx)
    assert out.status == "cancelled" and not out.calls_for("ocr") and writes(out) == []


def test_tag_does_not_exist_yet() -> None:
    out = run_fixture(load("testkit"))
    assert out.already_done == [] and not any("may appear again" in m for m in out.messages)


def test_everything_already_done_saves_no_digest_and_reports_open_items() -> None:
    fx = flow_a()
    fx["nas_files"] = {f"{OUT}/fridge-door-digest_20261123_200000.md": previous_digest(
        ['- [ ] 2026-12-02 — Return the library book · Jun · "12월 2일까지" · IMG_0091.jpg',
         '- [x] 2026-11-26 — Sign the photo consent · Mina · "11월 26일까지" · IMG_0090.jpg'])}
    fx["experts"]["tag_lookup"]["result"]["tagged"] = [f["path"] for f in fx["experts"]["list_photos"]["result"]["files"]]
    out = run_fixture(fx)
    assert out.status == "completed" and "Nothing new" in out.report and writes(out) == []
    assert "fridge-door-digest_20261123_200000.md still has 1 unticked deadline and 0 upcoming events." in out.report


def test_cut_listing_with_every_listed_photo_tagged_offers_the_newer_period() -> None:
    fx = over_sixty(flow_a())
    fx["experts"]["tag_lookup"]["result"]["tagged"] = [f["path"] for f in fx["experts"]["list_photos"]["result"]["files"]]
    out = run_fixture(fx)
    assert "All 9 listed photos were already handled, but 75 matched. Shall I look at the period from 2026-11-29?" in out.report
    assert "Nothing new" not in out.report and writes(out) == []


# ---- keepsake folder, copy and album ------------------------------------------------

def test_album_created_once_then_followed() -> None:
    out = run_fixture(load("testkit"))
    first, second = out.batches
    assert [a["name"] for a in first.albums] == ["Artwork - Mina", "Artwork - Jun"] and second.albums == []
    assert len([c for c in out.calls_for("create_album") if c.status == "completed"]) == 2
    assert "already existed, new copies appear in it after indexing" in (second.digest or "")


def test_album_gets_real_folder_path_and_id() -> None:
    fx = flow_a()
    fx["real_paths"] = {f"{OUT}/Artwork - Mina": f"{REAL}/Artwork - Mina"}
    out = run_fixture(fx)
    create = instruction(out, "create_album")
    assert f"every photo in the folder {REAL}/Artwork - Mina (folder file id fid-mina, storage type personal)" in create
    assert f"into the folder {OUT}/Artwork - Mina," in instruction(out, "copy_artwork")  # the real output folder path from Step 9
    assert f"- 2 copies in {REAL}/Artwork - Mina" in out.completion_card.splitlines()


def test_missing_folder_id_means_no_album() -> None:
    fx = flow_a()
    fx["experts"]["list_keepsake"] = {"Mina": {"status": "completed", "result": {
        "folder_path": f"{OUT}/Artwork - Mina",
        "files": [{"name": "IMG_0106.jpg", "path": f"{OUT}/Artwork - Mina/IMG_0106.jpg"},
                  {"name": "IMG_0107.jpg", "path": f"{OUT}/Artwork - Mina/IMG_0107.jpg"}]}}}
    out = run_fixture(fx)
    assert not out.calls_for("create_album") and len(out.copied) == 2
    assert "album Artwork - Mina: not created, the folder path, id or storage type was not returned" in (out.digest or "")
    assert out.completion_card.startswith("Partly done.") and "album Artwork - Mina" in out.completion_card


def test_copy_with_counts_only_is_judged_by_the_folder_listing() -> None:
    fx = flow_a()
    fx["experts"]["copy_artwork"]["Mina"]["then"] = {"status": "completed", "result": {"operation": "copy", "succeeded": 1, "failed": 1}}
    fx["experts"]["list_keepsake"] = {"Mina": {"status": "completed", "result": {
        "folder_path": f"{OUT}/Artwork - Mina", "folder_id": "fid-mina",
        "files": [{"name": "IMG_0106.jpg", "path": f"{OUT}/Artwork - Mina/IMG_0106.jpg"}]}}}
    out = run_fixture(fx)
    assert out.copied == [f"{OUT}/Artwork - Mina/IMG_0106.jpg"]
    assert f"{P}IMG_0107.jpg" not in out.tagged and f"{P}IMG_0106.jpg" in out.tagged
    assert "IMG_0107.jpg · Mina · 2026-11-28 · A paper-cup robot craft, silver and red. · chosen by the parent · not copied" in (out.digest or "")
    assert out.completion_card.startswith("Partly done.") and "copy IMG_0107.jpg (missing value)" in out.completion_card
    assert "Next run starts from: 2026-11-28" in (out.digest or "")  # the drawing that was not copied comes back


def test_same_name_drawing_counts_as_handled() -> None:
    fx = flow_a()
    fx["keepsake_existing"] = {"Mina": ["IMG_0107.jpg"]}
    fx["experts"]["copy_artwork"]["Mina"] = {"status": "completed", "result": {
        "copied": [{"src": f"{P}IMG_0106.jpg", "copy": f"{OUT}/Artwork - Mina/IMG_0106.jpg"}],
        "not_copied": [{"src": f"{P}IMG_0107.jpg", "reason": "a file with this name already exists"}]}}
    out = run_fixture(fx)
    assert len(out.calls_for("copy_artwork")) == 1  # reported, not retried
    assert "· chosen by the parent · already in the folder (same name), not copied" in (out.digest or "")
    assert f"{P}IMG_0107.jpg" in out.tagged and out.completion_card.startswith("Done.")


def test_existing_album_skips_creation() -> None:
    fx = flow_a()
    fx["experts"]["album_lookup"]["Mina"] = {"status": "completed", "result": {"albums": [{"name": "Artwork - Mina", "count": 4}]}}
    out = run_fixture(fx)
    assert not out.calls_for("create_album") and out.albums == [] and out.completion_card.startswith("Done.")
    assert len(out.copied) == 2


def test_unclear_album_lookup_never_creates() -> None:
    fx = flow_a()
    fx["experts"]["album_lookup"]["Mina"] = {"status": "completed", "result": {}}
    out = run_fixture(fx)
    assert not out.calls_for("create_album")
    assert "could not check, so I will not create one" in (out.preview or "")
    assert out.completion_card.startswith("Partly done.") and "album Artwork - Mina" in out.completion_card


def test_album_rule_unsupported_is_reported() -> None:
    fx = flow_a()
    fx["experts"]["create_album"]["Mina"] = {"status": "completed", "result": {"summary": "The folder cannot be used as a rule."}}
    out = run_fixture(fx)
    assert out.albums == [] and "the folder could not be used as the album rule" in (out.digest or "")
    assert out.completion_card.startswith("Partly done.")


def test_no_album_without_copies() -> None:
    fx = flow_a()
    fx["experts"]["copy_artwork"]["Mina"] = {"status": "failed", "result": {"reason": "disk full"}}
    out = run_fixture(fx)
    assert not out.calls_for("create_album") and not out.calls_for("list_keepsake") and out.copied == []
    # notices and the receipt are tagged; drawings come back next run
    assert sorted(out.tagged) == [f"{P}IMG_010{i}.jpg" for i in (2, 3, 4, 5, 8)]
    assert "- Not run because an earlier step did not complete: album Artwork - Mina" in out.completion_card.splitlines()


def test_unknown_child_is_not_copied_or_tagged() -> None:
    fx = flow_a()
    fx["user"]["child_choice"] = {}
    out = run_fixture(fx)
    assert "Check needed · IMG_0107.jpg:" in (out.preview or "") and "unknown, please tell me" in (out.preview or "")
    assert "### Child not chosen" in (out.digest or "") and out.copied == [f"{OUT}/Artwork - Mina/IMG_0106.jpg"]
    assert f"{P}IMG_0107.jpg" not in out.tagged and "Next run starts from: 2026-11-28" in (out.digest or "")


def test_album_check_runs_for_a_child_chosen_at_the_preview() -> None:
    fx = flow_a()
    fx["user"]["child_choice"] = {"IMG_0107.jpg": "Jun"}
    fx["experts"]["album_lookup"]["Jun"] = {"status": "completed", "result": {"none": True}}
    fx["experts"]["copy_artwork"]["Jun"] = copy.deepcopy(fx["experts"]["copy_artwork"]["Mina"])
    fx["experts"]["create_album"]["Jun"] = {"status": "completed", "result": {"album_id": "a1f0c2d4-0003", "count": 1}}
    out = run_fixture(fx)
    keys = [c.key for c in out.calls]
    assert [c.item for c in out.calls_for("album_lookup")] == ["Mina", "Jun"] and keys.index("album_lookup") < keys.index("ensure_folder")
    assert "Artwork - Jun" not in (out.preview or "") and "Will create: album Artwork - Jun" in (out.batch.preview_again or "")
    assert [a["name"] for a in out.albums] == ["Artwork - Mina", "Artwork - Jun"]


def test_no_album_when_the_check_after_the_preview_did_not_complete() -> None:
    fx = flow_a()
    fx["user"]["child_choice"] = {"IMG_0107.jpg": "Jun"}
    fx["experts"]["album_lookup"]["Jun"] = {"status": "failed", "result": {"reason": "photo service busy"}}
    fx["experts"]["copy_artwork"]["Jun"] = copy.deepcopy(fx["experts"]["copy_artwork"]["Mina"])
    out = run_fixture(fx)
    assert {c.item for c in out.calls_for("create_album")} == {"Mina"} and f"{OUT}/Artwork - Jun/IMG_0107.jpg" in out.copied
    assert "album Artwork - Jun: not created, could not check whether it exists" in (out.digest or "")


def test_paper_document_without_readable_text_is_unreadable_not_unrelated() -> None:
    fx = flow_a()
    fx["experts"]["ocr"]["IMG_0107.jpg"] = {"status": "completed", "result": {"text": ""}}
    fx["experts"]["vlm"]["IMG_0107.jpg"] = {"status": "completed", "result": {"answer": "NO. A printed paper notice, too dark to read."}}
    out = run_fixture(fx)
    assert [u["path"] for u in out.unreadable] == [f"{P}IMG_0107.jpg"] and all(u["path"] != f"{P}IMG_0107.jpg" for u in out.unrelated)


def test_preview_shows_unknown_child_until_the_parent_answers() -> None:
    out = run_fixture(flow_a())
    assert "- IMG_0107.jpg · unknown, please tell me · A paper-cup robot craft, silver and red." in (out.preview or "")
    assert "Which child made IMG_0107.jpg?" in out.questions
    assert "IMG_0107.jpg · Mina · 2026-11-28 · A paper-cup robot craft, silver and red. · chosen by the parent · copied" in (out.digest or "")


# ---- tagging: handled once -----------------------------------------------------------

def test_unreadable_photo_is_listed_tagged_and_still_done() -> None:
    fx = flow_a()
    fx["experts"]["ocr"]["IMG_0107.jpg"] = {"status": "completed", "result": {"text": ""}}
    fx["experts"]["vlm"]["IMG_0107.jpg"] = {"status": "completed", "result": {"answer": "I cannot see the image clearly enough to answer."}}
    out = run_fixture(fx)
    assert [u["path"] for u in out.unreadable] == [f"{P}IMG_0107.jpg"] and f"{P}IMG_0107.jpg" in out.tagged
    assert "- IMG_0107.jpg: could not be read" in (out.digest or "") and out.report.startswith("Done.")


def test_failed_photo_is_never_tagged_and_makes_partly_done() -> None:
    fx = flow_a()
    fx["experts"]["ocr"]["IMG_0107.jpg"] = {"status": "failed", "result": {"reason": "service busy"}}
    fx["experts"]["vlm"]["IMG_0107.jpg"] = {"status": "failed", "result": {"reason": "service busy"}}
    out = run_fixture(fx)
    assert [u["path"] for u in out.failed] == [f"{P}IMG_0107.jpg"] and f"{P}IMG_0107.jpg" not in out.tagged
    assert "IMG_0107.jpg: the expert failed (service busy); it will be read again next run" in (out.digest or "")
    assert "Next run starts from: 2026-11-28" in (out.digest or "")
    assert out.report.startswith("Partly done.") and "read IMG_0107.jpg (failed)" in out.completion_card


def test_unrelated_photos_are_tagged_only_after_a_verified_save() -> None:
    fx = flow_a()
    assert f"{P}IMG_0108.jpg" in run_fixture(fx).tagged
    fx["experts"]["save_digest"] = {"status": "failed", "result": {"reason": "disk full"}}
    out = run_fixture(fx)
    assert out.tagged == [] and not out.calls_for("tag_add")  # without a verified save nothing is tagged, not even the copies


def test_partial_tagging_is_partly_done() -> None:
    fx = flow_a()
    fx["experts"]["tag_add"]["then"] = {"status": "completed", "result": {"tagged": [f"{P}IMG_0102.jpg"]}}
    out = run_fixture(fx)
    assert out.report.startswith("Partly done.") and "tag (missing value)" in out.completion_card


def test_tagging_failure_says_where_to_start_next() -> None:
    fx = flow_a()
    fx["experts"]["tag_add"] = {"status": "failed", "result": {"reason": "tag service down"}}
    out = run_fixture(fx)
    assert any(m.startswith("Not tagged: IMG_0102.jpg, ") and "The saved digest already starts the next run after them; "
               "if you rerun this period explicitly, these photos will be read again." in m for m in out.messages)
    assert not any("first day" in m for m in out.messages) and out.report.startswith("Partly done.")


def test_unrelated_only_batch_saves_a_short_digest() -> None:
    fx = flow_a()
    files = fx["experts"]["list_photos"]["result"]["files"]
    fx["experts"]["list_photos"]["result"] = {"total": 1, "files": [files[-1]]}
    fx["experts"]["tag_lookup"] = {"status": "completed", "result": {"tag_exists": False}}
    out = run_fixture(fx)
    assert out.saved_path and out.tagged == [f"{P}IMG_0108.jpg"] and not out.calls_for("copy_artwork")
    fx["user"]["approve_preview"] = False
    out = run_fixture(fx)
    assert writes(out) == [] and "Nothing to save in this batch" in out.report


# ---- Next run starts from ---------------------------------------------------------------

def test_next_run_starts_from_in_the_test_kit() -> None:
    first, second = run_fixture(load("testkit")).batches
    assert (first.digest or "").splitlines()[1].endswith("Next run starts from: 2026-11-27")  # oldest photo left for batch 2 (D03)
    assert (second.digest or "").splitlines()[1].endswith("Next run starts from: 2026-11-30")  # the last day of the period


def test_same_day_rerun_and_a_photo_added_later_that_day() -> None:
    first = DryRunStore.run(flow_a())
    assert "Next run starts from: 2026-11-29" in next(iter(t["text"] for t in first["files"].values()))
    fx = flow_a()
    fx["nas_files"] = first["files"]
    files = fx["experts"]["list_photos"]["result"]["files"]
    fx["experts"]["list_photos"]["result"] = {"total": 1, "files": [files[-1]]}  # IMG_0108, the only photo of 2026-11-29
    fx["experts"]["tag_lookup"] = {"status": "completed", "result": {"tagged": first["tagged"]}}
    out = run_fixture(fx)
    assert out.period == "2026-11-29 to 2026-11-29" and "Nothing new" in out.report and writes(out) == []
    later = {"path": f"{P}IMG_0109.jpg", "mtime": "2026-11-29T22:40:00"}
    fx["experts"]["list_photos"]["result"] = {"total": 2, "files": [files[-1], later]}
    fx["experts"]["ocr"]["IMG_0109.jpg"] = fx["experts"]["ocr"]["IMG_0102.jpg"]
    fx["parent_llm"]["notices"]["IMG_0109.jpg"] = fx["parent_llm"]["notices"]["IMG_0102.jpg"]
    fx["experts"]["save_digest"]["then"]["result"]["path"] = f"{OUT}/fridge-door-digest_20261129_224500.md"
    out = run_fixture(fx)
    assert [p.rsplit("/", 1)[1] for p in out.batch.photos] == ["IMG_0109.jpg"] and out.tagged == [f"{P}IMG_0109.jpg"]


def test_untagged_photo_of_an_earlier_batch_sets_the_next_start() -> None:
    fx = load("testkit")
    fx["experts"]["ocr"]["KIT_D01.jpg"] = {"status": "failed", "result": {"reason": "service busy"}}
    fx["experts"]["vlm"]["KIT_D01.jpg"] = {"status": "failed", "result": {"reason": "service busy"}}
    first, second = run_fixture(fx).batches
    assert "Next run starts from: 2026-11-26" in (first.digest or "") and "Next run starts from: 2026-11-26" in (second.digest or "")


def test_continue_after_an_unsaved_digest_keeps_the_step1_digest() -> None:
    fx = load("testkit")
    kout = "Photos/PhoneBackup/Kit/Fridge Door"
    fx["nas_files"] = {f"{kout}/fridge-door-digest_20261122_200000.md": previous_digest(
        ['- [ ] 2026-12-02 — Return the library book · Jun · "12월 2일까지" · IMG_0091.jpg'], start="2026-11-23")}
    fx["experts"]["save_digest"][0] = {"status": "failed", "result": {"reason": "disk full"}}
    out = run_fixture(fx)
    first, second = out.batches
    assert first.tagged == [] and second.previous_digest == "fridge-door-digest_20261122_200000.md"
    assert any("IMG_0091.jpg" in c for c in second.carried)
    assert "Next run starts from: 2026-11-23" in (second.digest or "")  # batch 1 was not tagged, so it comes back


# ---- carry-over -------------------------------------------------------------------------

def test_carry_over_reads_the_exact_found_path() -> None:
    fx = flow_a()
    old = f"{OUT}/fridge-door-digest_20261123_200000.md"
    fx["nas_files"] = {old: previous_digest([
        '- [ ] 2026-11-28 — Return the library book · Jun · "11월 28일까지 반납" · IMG_0091.jpg',
        '- [x] 2026-11-26 — Sign the photo consent · Mina · "11월 26일까지" · IMG_0090.jpg',
        '- [ ] 2026-12-04 — Pay the field-trip fee, KRW 12,000 · Mina · "12월 4일까지 납부" · IMG_0104.jpg'])}
    out = run_fixture(fx)
    assert f"Read the file at exactly {old} and" in instruction(out, "read_digest")
    assert out.carried == ['2026-11-28 — Return the library book · Jun · "11월 28일까지 반납" · IMG_0091.jpg · '
                           "carried over from fridge-door-digest_20261123_200000.md"]
    deadlines = (out.digest or "").split("## Deadlines")[1].split("\n## ")[0]
    assert "- [ ] ⚠ 2026-11-28 — Return the library book" in deadlines  # past on 11-30, still open
    assert "IMG_0090.jpg" not in deadlines and deadlines.count("IMG_0104.jpg") == 1


def test_upcoming_events_carry_over_and_past_events_do_not() -> None:
    fx = flow_a()
    fx["nas_files"] = {f"{OUT}/fridge-door-digest_20261123_200000.md": previous_digest([], events=[
        '- 2026-11-27 10:00 — Open class · all children · "11월 27일" · IMG_0092.jpg',
        '- 2026-12-15 18:00 — Winter concert · Mina · "12월 15일 오후 6시" · IMG_0093.jpg · carried over from fridge-door-digest_20261116_200000.md'])}
    out = run_fixture(fx)
    events = (out.digest or "").split("## Events")[1].split("\n## ")[0]
    assert "IMG_0092.jpg" not in events
    assert ('- 2026-12-15 18:00 — Winter concert · Mina · "12월 15일 오후 6시" · IMG_0093.jpg · '
            "carried over from fridge-door-digest_20261123_200000.md") in events
    assert "Carried over (1)" in (out.preview or "") and out.report == "Done. 3 deadlines, 2 events, 2 artworks."


def test_explicit_none_means_nothing_to_carry() -> None:
    out = run_fixture(flow_a())
    assert not out.calls_for("read_digest") and out.carried == [] and out.completion_card.startswith("Done.")


def test_empty_find_result_is_not_proof_of_none() -> None:
    fx = flow_a()
    fx["experts"]["find_digest"] = {"status": "completed", "result": {}}
    out = run_fixture(fx)
    assert not out.calls_for("read_digest") and out.period == "2026-11-23 to 2026-11-29"
    assert "I could not check for an earlier digest, so nothing was carried over." in (out.digest or "")
    assert out.completion_card.startswith("Partly done.")


def test_cut_short_read_carries_nothing() -> None:
    fx = flow_a()
    fx["experts"]["find_digest"] = {"status": "completed", "result": {"path": f"{OUT}/fridge-door-digest_20261123_200000.md"}}
    fx["experts"]["read_digest"] = {"status": "completed", "result": {"complete": False, "text": previous_digest(
        ['- [ ] 2026-12-01 — Return the library book · Jun · "12월 1일까지" · IMG_0091.jpg'], start="2026-11-20")}}
    out = run_fixture(fx)
    assert out.carried == [] and "was cut short when read, so nothing was carried over." in (out.digest or "")
    assert out.period == "2026-11-23 to 2026-11-29"  # the 7-day default, not the date in the cut-short text


def test_item_called_done_at_preview_is_ticked() -> None:
    fx = flow_a()
    fx["user"]["done_items"] = ["IMG_0104.jpg"]
    out = run_fixture(fx)
    assert "- [x] 2026-12-04 — Pay the field-trip fee" in (out.digest or "")
    assert out.report == "Done. 2 deadlines, 1 event, 2 artworks."


# ---- a child's own words ------------------------------------------------------------------

def test_child_note_is_kept_word_for_word() -> None:
    fx = flow_a()
    fx["user"]["child_notes"] = {"IMG_0106.jpg": "민아: 이건 우리 학교 버스야, it's going home!"}
    out = run_fixture(fx)
    assert 'A crayon drawing of a yellow school bus under a rainbow. · Said: "민아: 이건 우리 학교 버스야, it\'s going home!" · ' in (out.digest or "")
    save = out.calls_for("save_digest")[-1].command
    assert "it'\"'\"'s going home" in save and "it's going home" in shlex.split(save)[4]
    assert out.questions.count("If your child said something about a drawing, tell me and I will keep it with the picture (optional).") == 1


def test_no_child_note_means_no_said_part() -> None:
    fx = flow_a()
    fx["user"].pop("child_notes")
    assert "Said:" not in (run_fixture(fx).digest or "")


# ---- artwork journal ----------------------------------------------------------------------

def journal_fixture(lines_by_digest: dict[str, list[str]]) -> dict[str, Any]:
    fx = flow_a()
    fx["mode"] = "journal"
    fx["inputs"] = {"output_folder": OUT, "child": "Mina"}  # no source folder, period or children needed
    fx["nas_files"] = {f"{OUT}/{name}": {"text": previous_digest([], artwork=lines), "created": name[19:32]}
                       for name, lines in lines_by_digest.items()}
    return fx


JOURNAL_DIGESTS = {
    "fridge-door-digest_20261123_200000.md": [
        "### Mina",
        '- IMG_0050.jpg · Mina · 2026-11-20 · A pencil cat. · Said: "This is Nabi." · chosen by the parent · copied',
        "- IMG_0051.jpg · Jun · 2026-11-21 · A red car. · chosen by the parent · copied"],
    "fridge-door-digest_20261129_211405.md": [
        "- IMG_0106.jpg · Mina · 2026-11-28 · A crayon drawing of a yellow school bus under a rainbow. · name read on the drawing: 김민아 · copied"],
}


def test_journal_from_verbatim_lines() -> None:
    out = run_fixture(journal_fixture(JOURNAL_DIGESTS))
    assert [c.key for c in out.calls] == ["find_digest", "journal_query"] and writes(out) == []
    assert out.calls_for("journal_query")[0].target == "document-agent"
    lines = out.journal.splitlines()
    assert lines[:2] == ["# Artwork journal - Mina", "2026-11-20 to 2026-11-28"]
    assert lines[3] == (f'- 2026-11-20 · A pencil cat. · Said: "This is Nabi." · IMG_0050.jpg · {OUT}/Artwork - Mina · '
                        "from fridge-door-digest_20261123_200000.md")
    assert "IMG_0051.jpg" not in out.journal and len(lines) == 5


def test_journal_saved_only_on_request() -> None:
    fx = journal_fixture(JOURNAL_DIGESTS)
    fx["real_paths"] = {OUT: REAL}  # the digests sit at the real path the folder look-up returns
    fx["nas_files"] = {p.replace(OUT, REAL): v for p, v in fx["nas_files"].items()}
    fx["user"]["save_journal"] = True
    fx["experts"]["journal_save"] = {"status": "waiting_approval", "denied": {"status": "cancelled"},
                                     "then": {"status": "completed", "result": {"path": f"{REAL}/fridge-door-journal_20261130_220000.md", "verified": True}}}
    out = run_fixture(fx)
    save = instruction(out, "journal_save")
    assert f"existing folder {REAL}" in save and "fridge-door-journal" in save and "# Artwork journal - Mina" in save
    assert out.journal_path == f"{REAL}/fridge-door-journal_20261130_220000.md"


def test_journal_fallback_reads_the_eight_newest_digests() -> None:
    digests = {f"fridge-door-digest_202611{d:02d}_200000.md": [f"- IMG_00{d:02d}.jpg · Mina · 2026-11-{d:02d} · Drawing {d}. · chosen by the parent · copied"]
               for d in range(1, 11)}
    fx = journal_fixture(digests)
    fx["experts"]["journal_query"] = {"status": "failed", "result": {"reason": "Markdown is not a supported document type"}}
    out = run_fixture(fx)
    assert "The document expert could not read the digests, so I checked only the 8 most recent digests (at most 8)." in out.messages
    assert len(out.calls_for("read_digest")) == 8 and out.calls_for("journal_find")[0].target == "file-agent"
    assert "Drawing 3." in out.journal and "Drawing 2." not in out.journal and out.journal.splitlines()[1] == "2026-11-03 to 2026-11-10"


def test_journal_names_a_digest_not_read_in_full() -> None:
    fx = journal_fixture(JOURNAL_DIGESTS)
    fx["experts"]["journal_query"] = {"status": "completed", "result": {
        "lines": [{"line": JOURNAL_DIGESTS["fridge-door-digest_20261129_211405.md"][0], "file": "fridge-door-digest_20261129_211405.md"}],
        "not_read_in_full": ["fridge-door-digest_20261123_200000.md"]}}
    out = run_fixture(fx)
    assert "fridge-door-digest_20261123_200000.md was not read in full, so its lines may be missing." in out.messages


def test_journal_with_no_lines_creates_nothing() -> None:
    out = run_fixture(journal_fixture({"fridge-door-digest_20261123_200000.md": ["No artwork this time."]}))
    assert out.journal == "" and "No artwork lines for Mina" in out.report and writes(out) == []


# ---- questions about saved digests ---------------------------------------------

def question(text: str, keywords: list[str]) -> dict[str, Any]:
    fx = flow_a()
    fx["mode"], fx["question"] = "question", text
    fx["parent_llm"]["question_keywords"] = keywords
    return fx


def test_question_answered_from_newest_digest() -> None:
    fx = question("When is the field trip fee due?", ["fee"])
    fx["nas_files"] = {f"{OUT}/fridge-door-digest_20261129_211405.md": run_fixture(flow_a()).digest}
    out = run_fixture(fx)
    assert [c.key for c in out.calls] == ["find_digest", "read_digest"] and writes(out) == []
    assert out.answer.startswith("From fridge-door-digest_20261129_211405.md:")
    assert "2026-12-04 — Pay the field-trip fee, KRW 12,000" in out.answer and "IMG_0104.jpg" in out.answer


def test_question_needs_only_the_output_folder() -> None:
    fx = question("When is the field trip fee due?", ["fee"])
    fx["inputs"] = {"output_folder": OUT}
    fx["nas_files"] = {f"{OUT}/fridge-door-digest_20261129_211405.md": run_fixture(flow_a()).digest}
    out = run_fixture(fx)
    assert out.answer.startswith("From fridge-door-digest_20261129_211405.md:") and out.questions == []


def test_question_without_digest_says_so() -> None:
    out = run_fixture(question("What do we still owe the school?", ["pay"]))
    assert out.answer == f"I found no saved digest in {OUT}. Shall I sort this week's photos?"
    assert not out.calls_for("ocr") and writes(out) == []


def test_question_on_cut_short_digest_says_incomplete() -> None:
    fx = question("When is the field trip fee due?", ["fee"])
    fx["experts"]["find_digest"] = {"status": "completed", "result": {"path": f"{OUT}/fridge-door-digest_x.md"}}
    fx["experts"]["read_digest"] = {"status": "completed", "result": {"complete": False, "text": previous_digest(
        ['- [ ] 2026-12-04 — Pay the field-trip fee · Mina · "12월 4일까지" · IMG_0104.jpg'])}}
    out = run_fixture(fx)
    assert "IMG_0104.jpg" in out.answer and "cut short" in out.answer


# ---- refused approvals, real paths and Partly done ------------------------------------------

def test_save_goes_to_the_real_folder_path() -> None:
    fx = flow_a()
    fx["experts"]["ensure_folder"] = {"status": "completed", "result": {"path": REAL}}
    out = run_fixture(fx)
    save = instruction(out, "save_digest")
    assert save.startswith(f"Save the following Markdown text as one new file in the existing folder {REAL}, using")
    assert f"existing folder {OUT}," not in save


def test_folder_check_without_path_blocks_save() -> None:
    fx = flow_a()
    fx["experts"]["ensure_folder"] = {"status": "completed", "result": {"exists": True}}
    out = run_fixture(fx)
    assert not out.calls_for("save_digest") and out.digest_shown_in_conversation
    assert "output folder (missing value)" in out.completion_card


def test_refused_copy_approval_follows_resumed_state() -> None:
    fx = flow_a()
    fx["approvals"]["copy_artwork:Mina"] = False
    out = run_fixture(fx)
    assert out.status == "completed" and out.copied == [] and not out.calls_for("create_album")
    assert out.saved_path is not None and all("IMG_0106" not in p and "IMG_0107" not in p for p in out.tagged)
    card = out.completion_card.splitlines()
    assert card[0] == "Partly done. 3 deadlines, 1 event, 2 artworks."
    assert "- Failed or cancelled: copy drawings for Mina (cancelled)" in card
    assert "Partly done before saving: copy drawings for Mina (cancelled); album Artwork - Mina (not run)." in (out.digest or "")


def test_refused_approval_state_is_not_predicted() -> None:
    fx = flow_a()
    fx["approvals"]["create_album:Mina"] = False
    fx["experts"]["create_album"]["Mina"]["denied"] = {"status": "failed", "result": {"reason": "approval rejected"}}
    out = run_fixture(fx)
    assert out.albums == [] and "- Failed or cancelled: album Artwork - Mina (failed)" in out.completion_card.splitlines()
    del fx["experts"]["create_album"]["Mina"]["denied"]
    with pytest.raises(DryRunError, match="does not say what the resumed delegation returned"):
        run_fixture(fx)


def test_save_failed_shows_digest_and_keeps_notices_untagged() -> None:
    fx = flow_a()
    fx["experts"]["save_digest"] = {"status": "failed", "result": {"reason": "disk full"}}
    out = run_fixture(fx)
    assert out.saved_path is None and out.digest_shown_in_conversation
    assert out.tagged == []  # nothing is tagged; the copies come back next run as same-name items
    assert "Digest was not saved; its text is shown above" in out.completion_card and out.report.startswith("Partly done.")


def test_save_without_verified_path_is_not_a_save() -> None:
    fx = flow_a()
    fx["experts"]["save_digest"] = {"status": "completed", "result": {"summary": "Saved."}}
    out = run_fixture(fx)
    assert out.saved_path is None and "Saved digest" not in out.completion_card
    assert "- Failed or cancelled: save digest (missing value)" in out.completion_card.splitlines()


def test_folder_check_failure_blocks_save() -> None:
    fx = flow_a()
    fx["experts"]["ensure_folder"] = {"status": "failed", "result": {"reason": "permission denied"}}
    out = run_fixture(fx)
    assert not out.calls_for("save_digest") and not out.calls_for("copy_artwork") and out.tagged == []
    assert out.digest_shown_in_conversation
    assert ("- Not run because an earlier step did not complete: copy drawings for Mina, album Artwork - Mina, save digest, tag"
            in out.completion_card.splitlines())


# ---- empty results and stops ----------------------------------------------------

def test_empty_period_no_results() -> None:
    fx = flow_a()
    fx["experts"]["list_photos"] = {"status": "completed", "result": {"none": True, "total": 0, "files": []}}
    out = run_fixture(fx)
    assert out.status == "completed" and [c.key for c in out.calls] == ["find_digest", "list_photos"]
    assert "(no results)" in out.report and "Nothing was created" in out.report


def test_empty_listing_without_statement_stops() -> None:
    fx = flow_a()
    fx["experts"]["list_photos"] = {"status": "completed", "result": {}}
    out = run_fixture(fx)
    assert out.status == "failed" and "did not say that nothing matched" in out.report and len(out.calls) == 2


def test_preview_declined_shows_digest_and_creates_nothing() -> None:
    fx = flow_a()
    fx["user"]["approve_preview"] = False
    out = run_fixture(fx)
    assert out.status == "cancelled" and writes(out) == []
    assert out.digest_shown_in_conversation and out.digest and "## Deadlines" in out.digest


def test_user_declines_read_back() -> None:
    fx = flow_a()
    fx["user"]["proceed"] = False
    out = run_fixture(fx)
    assert out.status == "cancelled" and [c.key for c in out.calls] == ["find_digest"] and writes(out) == []


def test_missing_source_folder_asks() -> None:
    fx = flow_a()
    del fx["inputs"]["source_folder"]
    out = run_fixture(fx)
    assert out.status == "waiting_user" and out.calls == [] and "Which NAS folder" in out.report


def test_expert_cancelled_stops_workflow() -> None:
    fx = flow_a()
    fx["experts"]["ocr"]["IMG_0105.jpg"] = {"status": "cancelled"}
    out = run_fixture(fx)
    assert out.status == "cancelled" and writes(out) == [] and "Nothing was created" in out.report


def test_expert_waiting_user_resumes_same_delegation() -> None:
    fx = flow_a()
    fx["experts"]["save_digest"] = {"status": "waiting_user", "question": "Which folder should I save to?",
                                    "then": fx["experts"]["save_digest"]}
    out = run_fixture(fx)
    assert out.status == "completed" and "Which folder should I save to?" in out.questions
    assert [c.status for c in out.calls_for("save_digest")] == ["waiting_user", "waiting_approval", "completed"]


def test_listing_fallback_to_photo_agent() -> None:
    fx = flow_a()
    fx["experts"]["list_photos_fallback"] = fx["experts"]["list_photos"]
    fx["experts"]["list_photos"] = {"status": "failed", "result": {"reason": "folder is a library view"}}
    out = run_fixture(fx)
    (call,) = out.calls_for("list_photos_fallback")
    assert out.status == "completed" and call.target == "photo-agent"


def test_listing_and_fallback_fail() -> None:
    fx = flow_a()
    fx["experts"]["list_photos"] = {"status": "failed"}
    out = run_fixture(fx)
    assert out.status == "failed" and "Step 2 failed" in out.report and len(out.calls) == 3


def test_missing_value_stops_dependent_step() -> None:
    template = load_templates()["save_digest"]
    with pytest.raises(DryRunError, match=r"value \{output_folder_path\} is missing"):
        render(template, {"digest_text": "x"})


def test_single_quote_in_value_uses_check_lib_escape() -> None:
    fx = flow_a()
    fx["inputs"]["source_folder"] = "Photos/Mom's Phone"
    fx["inputs"]["output_folder"] = "Photos/Mom's Phone/Fridge Door"
    out = run_fixture(fx)
    first = out.calls_for("list_photos")[0].command
    assert "Mom'\"'\"'s Phone" in first and "In the folder Photos/Mom's Phone and" in shlex.split(first)[4]
    assert_commands_valid(out)


# ---- optional steps ---------------------------------------------------------------

def test_archive_off_by_default_and_on_request() -> None:
    fx = flow_a()
    fx["today"] = "2026-12-06"
    fx["inputs"]["period"] = "2026-11-23 to 2026-11-29"
    assert not run_fixture(fx).calls_for("archive")
    fx["inputs"]["archive_past"] = True
    fx["user"]["archive_yes"] = True
    fx["experts"]["archive"] = {"status": "waiting_approval", "denied": {"status": "cancelled"},
                                "then": {"status": "completed", "result": {"moved": [f"{OUT}/Archive 2026-12/IMG_0102.jpg"]}}}
    out = run_fixture(fx)
    (call,) = [c for c in out.calls_for("archive") if c.status == "completed"]
    assert f"{OUT}/Archive 2026-12" in call.command
    assert "IMG_0102.jpg" in call.command and "IMG_0104.jpg" in call.command and "IMG_0103.jpg" not in call.command
    assert "To be moved after approval: " in (out.digest or "") and "Moved 1 past notice photo" in out.completion_card


def test_translated_copy_on_request() -> None:
    fx = flow_a()
    fx["inputs"]["copy_language"] = "Korean"
    fx["experts"]["translate_copy"] = {"status": "waiting_approval", "denied": {"status": "cancelled"},
                                       "then": {"status": "completed", "result": {"path": f"{OUT}/fridge-door-digest_20261129_211405.ko.md"}}}
    out = run_fixture(fx)
    (call,) = [c for c in out.calls_for("translate_copy") if c.status == "completed"]
    assert call.target == "document-agent" and f"at exactly {OUT}/fridge-door-digest_20261129_211405.md into Korean" in call.command
    assert "- Translated copy · " in out.completion_card and out.report.startswith("Done.")


def test_translated_copy_failure_is_partly_done() -> None:
    fx = flow_a()
    fx["inputs"]["copy_language"] = "Korean"
    fx["experts"]["translate_copy"] = {"status": "completed", "result": {"summary": "No copy was written."}}
    out = run_fixture(fx)
    assert out.report.startswith("Partly done.") and "translated copy (missing value)" in out.completion_card


def test_translated_copy_not_run_without_saved_digest() -> None:
    fx = flow_a()
    fx["inputs"]["copy_language"] = "Korean"
    fx["experts"]["save_digest"] = {"status": "failed"}
    out = run_fixture(fx)
    assert not out.calls_for("translate_copy") and "translated copy" in out.completion_card


# ---- 16-photo test kit (test-plan.md) ---------------------------------------------

def test_testkit_core1_first_batch() -> None:
    first = run_fixture(load("testkit")).batches[0]
    assert first.completion_card.splitlines()[0] == "Done. 6 deadlines, 2 events, 2 artworks."
    digest = first.digest or ""
    assert "6 deadlines (1 past), 2 events, 2 artworks (Mina 1, Jun 1)" in digest and "- [ ] ⚠ 2026-09-23" in digest
    assert sorted(u["reason"] for u in first.unrelated) == ["receipt", "screenshot"]
    assert len(first.tagged) == 12 and f"{K}KIT_R01.jpg" in first.tagged and len(first.albums) == 2
    assert sum("name read on the drawing" in a["how"] for a in first.artwork) == 2


def test_testkit_core2_continue_d06_unreadable() -> None:
    out = run_fixture(load("testkit"))
    second = out.batches[1]
    assert len(second.carried) == 6 and all("carried over from fridge-door-digest_20261130_182000.md" in c for c in second.carried)
    assert len(second.carried_events) == 2
    assert [u["path"].rsplit("/", 1)[1] for u in second.unreadable] == ["KIT_D06.jpg"]
    assert len(second.tagged) == 4 and second.albums == []
    assert len(out.tagged) == 16 and len(out.copied) == 5 and f"{K}KIT_D06.jpg" in out.tagged
    assert second.completion_card.startswith("Done. 6 deadlines, 2 events, 3 artworks.")


def test_testkit_core2_d06_answered_yes() -> None:
    fx = load("testkit")
    fx["experts"]["vlm"]["KIT_D06.jpg"] = {"status": "completed", "result": {"answer": "YES. A smudged drawing of a blue shape."}}
    fx["user"]["child_choice"]["KIT_D06.jpg"] = "Mina"
    out = run_fixture(fx)
    second = out.batches[1]
    assert "Which child made KIT_D06.jpg?" in out.questions and second.unreadable == []
    assert len(second.tagged) == 4 and len(out.tagged) == 16 and len(out.copied) == 6
    assert second.completion_card.startswith("Done. 6 deadlines, 2 events, 4 artworks.")


def test_testkit_rerun_same_period_creates_nothing() -> None:
    first_run = DryRunStore.run(load("testkit"))
    fx = load("testkit")
    fx["inputs"]["period"] = "2026-11-23 to 2026-11-30"
    fx["nas_files"] = first_run["files"]
    fx["experts"]["tag_lookup"] = {"status": "completed", "result": {"tagged": first_run["tagged"]}}
    out = run_fixture(fx)
    assert len(out.already_done) == 16 and writes(out) == [] and not out.calls_for("ocr")
    assert "fridge-door-digest_20261130_183500.md still has 6 unticked deadlines and 2 upcoming events." in out.report
    assert "Nothing was created" in out.report


def test_testkit_refused_approval_edge_sora_and_tae() -> None:
    fx = load("testkit")
    fx["inputs"] = {**fx["inputs"], "source_folder": "Photos/PhoneBackup/Kit2", "children": [{"name": "Sora"}, {"name": "Tae"}]}
    for f in fx["experts"]["list_photos"]["result"]["files"]:
        f["path"] = f["path"].replace("/Kit/", "/Kit2/")
    fx["user"] = {"proceed": True, "approve_preview": True, "continue": 0, "child_choice": {"KIT_D01.jpg": "Sora", "KIT_D02.jpg": "Tae"}}
    none = {"status": "completed", "result": {"none": True}}
    fx["experts"]["album_lookup"] = {"Sora": none, "Tae": none}
    approve = fx["experts"]["copy_artwork"]["Mina"][0]
    fx["experts"]["copy_artwork"] = {"Sora": approve, "Tae": copy.deepcopy(approve)}
    fx["experts"]["create_album"] = {"Sora": fx["experts"]["create_album"]["Mina"], "Tae": fx["experts"]["create_album"]["Jun"]}
    fx["approvals"] = {"copy_artwork:Tae": False}
    out = run_fixture(fx)
    first = out.batch
    assert [a["name"] for a in first.albums] == ["Artwork - Sora"] and len(out.copied) == 1
    assert len(first.tagged) == 11 and "Photos/PhoneBackup/Kit2/KIT_D02.jpg" not in first.tagged
    assert first.completion_card.startswith("Partly done. 6 deadlines, 2 events, 2 artworks.")
    assert "copy drawings for Tae (cancelled)" in first.completion_card
    assert "Next run starts from: 2026-11-26" in (first.digest or "")  # D02 was not copied, so it comes back


def test_testkit_summaries_keep_dates_and_amounts_as_written() -> None:
    digest = run_fixture(load("testkit")).batches[0].digest or ""
    assert "$12.00" in digest and "12달러" not in digest and "Thursday, December 10, 2026 at 6:00 pm" in digest


class DryRunStore:
    """Runs a fixture and returns what it left on the simulated NAS (digests and tagged photos)."""

    @staticmethod
    def run(fx: dict[str, Any]) -> dict[str, Any]:
        from scripts.dryrun import DryRun

        run = DryRun(fx)
        out = run.run()
        files = {p: {"text": t, "created": run.created[p]} for p, t in run.store.items()}
        return {"files": files, "tagged": out.tagged}


# ---- coverage of the SKILL.md delegates ----------------------------------------------

def test_all_skill_delegates_are_exercised() -> None:
    seen: set[str] = set()
    for fx in (flow_a(), load("testkit"), journal_fixture(JOURNAL_DIGESTS)):
        seen |= {c.key for c in run_fixture(fx).calls}
    extra = flow_a()
    extra["experts"]["list_photos_fallback"] = copy.deepcopy(extra["experts"]["list_photos"])
    extra["experts"]["list_photos_fallback"]["result"]["total"] = 75
    extra["experts"]["list_photos"] = {"status": "failed"}
    extra["user"]["narrow"] = True
    extra["experts"]["narrow_photos"] = {"status": "completed", "result": {"summary": "Indexing has not finished."}}
    extra["experts"]["find_digest"] = {"status": "completed", "result": {"path": f"{OUT}/fridge-door-digest_old.md"}}
    extra["experts"]["read_digest"] = {"status": "completed", "result": {"complete": True, "text": previous_digest([])}}
    extra["today"] = "2026-12-06"
    extra["inputs"]["period"] = "2026-11-23 to 2026-11-29"
    extra["inputs"]["archive_past"] = True
    extra["inputs"]["copy_language"] = "Korean"
    extra["user"]["archive_yes"] = True
    extra["experts"]["archive"] = {"status": "completed", "result": {"moved": []}}
    extra["experts"]["translate_copy"] = {"status": "completed", "result": {"path": f"{OUT}/copy.md"}}
    seen |= {c.key for c in run_fixture(extra).calls}
    journal = journal_fixture(JOURNAL_DIGESTS)
    journal["experts"]["journal_query"] = {"status": "failed"}
    journal["user"]["save_journal"] = True
    journal["experts"]["journal_save"] = {"status": "completed", "result": {"path": f"{OUT}/fridge-door-journal_x.md", "verified": True}}
    seen |= {c.key for c in run_fixture(journal).calls}
    assert seen == set(load_templates())


def test_cli_prints_transcript(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(FIXTURES / "flow-a.json")]) == 0
    printed = capsys.readouterr().out
    assert printed.startswith("status: completed") and "## Digest" in printed and "## Completion card" in printed


# ---- chat card formats -------------------------------------------------------------

def test_preview_card_parts_in_order() -> None:
    preview = run_fixture(flow_a()).preview or ""
    lines = preview.splitlines()
    assert lines[0] == "7 photos read. Please check before I save anything."
    assert lines[1] == "9 photos found · 2 already done · 7 in this batch · 0 left for later"
    assert lines[2] == "Photos/PhoneBackup · 2026-11-23 to 2026-11-29"
    assert lines[3].startswith("Check needed · IMG_0107.jpg:")
    order = ["School notices (4)", "Artwork (2)", "If your child said something", "Not related / unreadable (1)", "Will copy:",
             "Will create:", "Will save:", "Originals stay where they are; nothing is moved or deleted. Proceed?"]
    positions = [next(i for i, line in enumerate(lines) if line.startswith(t)) for t in order]
    assert positions == sorted(positions)
    assert "- IMG_0104.jpg · Field-trip fee · 2026-12-04 · Pay the field-trip fee, KRW 12,000 · Mina" in lines
    assert "can show twice in UGREEN Photos" in preview and "tag the photos it lists fridge-door-done" in preview


def test_preview_flags_past_due_and_carried_items() -> None:
    kit = run_fixture(load("testkit"))
    first, second = kit.batches
    assert "⚠ 2026-09-23 (past)" in (first.preview or "")
    assert "Carried over (8)" in (second.preview or "") and "- ⚠ 2026-09-23 — Complete the online generative AI survey" in (second.preview or "")


def test_completion_card_with_real_results() -> None:
    out = run_fixture(flow_a())
    lines = out.completion_card.splitlines()
    assert lines[0] == "Done. 3 deadlines, 1 event, 2 artworks."
    assert lines[1] == "Next due: 2026-12-04 · Pay the field-trip fee, KRW 12,000 · Mina · IMG_0104.jpg"
    assert f"- 2 copies in {OUT}/Artwork - Mina" in lines and "- Album 'Artwork - Mina' · 2 photos · id a1f0c2d4-0002" in lines
    assert "- Saved digest · " + (out.saved_path or "?") in lines and "- Tagged 7 photos fridge-door-done" in lines
    assert lines[-1].endswith("This Skill asked only the NAS experts; the AI model they use is the one the NAS owner set up")
    assert "stayed on this NAS" not in out.completion_card and "called no outside service" not in out.completion_card


def test_loading_progress_line_per_photo() -> None:
    assert run_fixture(flow_a()).progress == [f"Reading photos {i}/7" for i in range(1, 8)]


def test_digest_meta_line() -> None:
    digest = run_fixture(flow_a()).digest or ""
    assert digest.splitlines()[1] == ("Source: Photos/PhoneBackup · 7 photos read · Generated on NAS 2026-11-29 21:14 · "
                                      "Next run starts from: 2026-11-29")  # nothing left untagged: the last day of the period


def test_readme_shows_the_same_cards_as_the_dry_run() -> None:
    out = run_fixture(flow_a())
    readme = README.read_text(encoding="utf-8")
    indent = "\n".join(("    " + line) if line else "" for line in (out.preview or "").splitlines())
    assert indent in readme
    assert "\n".join("    " + line for line in out.completion_card.splitlines()) in readme


def test_digest_format_example_is_the_dry_run_digest() -> None:
    example = DIGEST_FORMAT.read_text(encoding="utf-8").split("## Example")[1].split("```")[1]
    assert example.strip() == (run_fixture(flow_a()).digest or "").strip()
