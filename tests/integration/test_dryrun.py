"""End-to-end dry runs: inventory -> OCR -> structuring -> albums and digest, against simulated expert answers.

Covers plan.md §06 flows A, B and C, every delegation state, the Should features, and the
planned test kit (#28: batch A notices, batch B drawings, second run). Fixtures live in
tests/fixtures/dryrun/; variants are derived here so each test shows only what it changes.
"""

from __future__ import annotations

import copy
import json
import shlex
from pathlib import Path
from typing import Any

import pytest

from scripts.check import DELEGATE_CHAINING, EXTRA_FLAG
from scripts.dryrun import DryRunError, Outcome, digest_sections, load_templates, main, run_fixture

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "dryrun"
WRITE_KEYS = {"create_album", "create_album_fallback", "save_digest", "tag_add", "archive"}
P = "Photos/PhoneBackup/2026-10/"


def load(name: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    return data


def flow_a() -> dict[str, Any]:
    return load("flow-a")


def writes(out: Outcome) -> list[str]:
    return [c.key for c in out.calls if c.key in WRITE_KEYS]


def assert_commands_valid(out: Outcome) -> None:
    for call in out.calls:
        tokens = shlex.split(call.command)
        assert tokens[:3] == ["delegate", "--target", call.target] and tokens[3] == "--instruction" and len(tokens) == 5
        assert "{" not in tokens[4] or "{" in json.dumps(call.item)  # every value filled
        assert not DELEGATE_CHAINING.search(call.command.split("--instruction", 1)[0])
        assert not EXTRA_FLAG.search(call.command.split("--instruction", 1)[0].replace("--target", ""))


# ---- flow A ----------------------------------------------------------------

def test_flow_a_weekly_digest() -> None:
    out = run_fixture(flow_a())
    assert out.status == "completed"
    assert_commands_valid(out)
    assert len(out.calls_for("ocr")) == 7 and len(out.calls_for("vlm")) == 2 and not out.calls_for("translate")
    assert [a["name"] for a in out.albums] == ["School notices 2026-10", "Artwork – Mina 2026"]
    assert [a["count"] for a in out.albums] == [4, 2]
    assert sorted(out.tagged) == [f"{P}IMG_010{i}.jpg" for i in range(2, 8)]  # receipt never tagged
    assert out.saved_path and out.saved_path.endswith("Fridge Door – 2026-10-19 to 2026-10-25.md")
    assert out.report.startswith("3 deadlines (earliest: field-trip fee, 10/31), 1 event, 2 artworks (Mina).")
    assert "1 photo left untouched (receipt)" in out.report and "2 already done" in out.report
    assert out.approvals == ["create_album:School notices 2026-10", "create_album:Artwork – Mina 2026"]


def test_flow_a_digest_follows_digest_format() -> None:
    out = run_fixture(flow_a())
    assert out.digest is not None
    headings = [line[3:] for line in out.digest.splitlines() if line.startswith("## ")]
    assert headings == digest_sections() and len(headings) == 7
    deadlines = out.digest.split("## Deadlines")[1].split("\n## ")[0].strip().splitlines()
    assert [line[6:16] for line in deadlines] == ["2026-10-31", "2026-11-01", "2026-11-04"]
    assert all(line.startswith("- [ ] ") and ".jpg" in line for line in deadlines)  # every item names its source
    assert '"10월 31일까지 납부"' in deadlines[0]  # original date text quoted
    assert "name read on the drawing: 김민아" in out.digest and "chosen by the parent" in out.digest


def test_flow_a_nothing_written_before_preview_agreement() -> None:
    out = run_fixture(flow_a())
    keys = [c.key for c in out.calls]
    first_write = min(keys.index(k) for k in WRITE_KEYS if k in keys)
    assert all(k not in WRITE_KEYS for k in keys[:first_write])
    assert keys.index("album_lookup") < first_write
    assert out.preview and "Nothing will be moved or deleted." in out.preview


def test_flow_a_original_photos_never_moved() -> None:
    out = run_fixture(flow_a())
    assert not out.calls_for("archive") and "Originals were not moved or deleted." in (out.digest or "")


# ---- flow B: translation (S1) ---------------------------------------------

def flow_b() -> dict[str, Any]:
    fx = flow_a()
    fx["inputs"]["parent_language"] = "en"
    fx["experts"]["translate"] = {
        "IMG_0102.jpg": {"status": "completed", "result": {"text": "Museum field trip: return the signed consent slip by Nov 1."}},
        "IMG_0103.jpg": {"status": "completed", "result": {"text": "Bring a jump rope to PE on Nov 4."}},
        "IMG_0104.jpg": {"status": "waiting_approval", "then": {"status": "completed", "result": {"text": "Field-trip fee KRW 12,000 by Oct 31."}}},
        "IMG_0105.jpg": {"status": "completed", "result": {"text": "Arts festival in the school hall, Nov 7, 2 pm."}},
    }
    return fx


def test_flow_b_translates_summaries_only() -> None:
    out = run_fixture(flow_b())
    assert out.status == "completed"
    calls = out.calls_for("translate")
    assert len([c for c in calls if c.status == "completed"]) == 4
    for call in calls:
        assert "into en." in call.command
        assert "스쿨뱅킹" not in call.command and "가정통신문" not in call.command  # never the full OCR text
    assert "translate:IMG_0104.jpg" in out.approvals


def test_flow_b_preview_shows_original_translation_due_action() -> None:
    out = run_fixture(flow_b())
    assert out.preview is not None
    assert "[현장체험학습비 12,000원을 10월 31일까지 납부해 주세요. / Field-trip fee KRW 12,000 by Oct 31. / 2026-10-31 / field-trip fee]" \
        in out.preview
    assert "| Field-trip fee KRW 12,000 by Oct 31. |" in (out.digest or "")


def test_flow_b_translation_failure_keeps_original() -> None:
    fx = flow_b()
    fx["experts"]["translate"]["IMG_0103.jpg"] = {"status": "failed", "result": {"reason": "model busy"}}
    fx["approvals"]["translate:IMG_0104.jpg"] = False
    out = run_fixture(fx)
    assert out.status == "completed"
    digest = out.digest or ""
    assert digest.lower().count("translation unavailable") == 4  # 2 table rows + 2 run-detail lines
    assert "| 11월 4일 체육 시간에 줄넘기 준비. (translation unavailable) |" in digest  # original summary kept
    assert any("IMG_0103.jpg" in m and "unavailable" in m for m in out.messages)


# ---- flow C: empty and edge results ---------------------------------------

def test_flow_c_empty_period_no_results() -> None:
    fx = flow_a()
    fx["experts"]["list_photos"] = {"status": "completed", "result": {"total": 0, "files": []}}
    out = run_fixture(fx)
    assert out.status == "completed" and len(out.calls) == 1
    assert "(no results)" in out.report and "Nothing was created" in out.report


def test_flow_c_unreadable_photos_listed_not_guessed() -> None:
    fx = flow_a()
    fx["experts"]["ocr"]["IMG_0107.jpg"] = {"status": "failed", "result": {"reason": "blurred"}}
    fx["experts"]["vlm"]["IMG_0107.jpg"] = {"status": "failed", "result": {"reason": "blurred"}}
    out = run_fixture(fx)
    assert out.status == "completed"
    assert [u["path"] for u in out.unreadable] == [f"{P}IMG_0107.jpg"]
    assert "- IMG_0107.jpg: could not be read" in (out.digest or "")
    assert f"{P}IMG_0107.jpg" not in out.tagged
    assert [a["count"] for a in out.albums] == [4, 2]  # fixture counts; plan says 1 artwork
    assert [len(a["paths"]) for a in out.albums] == [4, 1]
    assert "Could not read: IMG_0107.jpg." in out.report


def test_flow_c_album_approval_denied_is_partial_success() -> None:
    fx = flow_a()
    fx["approvals"]["create_album:Artwork – Mina 2026"] = False
    out = run_fixture(fx)
    assert out.status == "completed"
    assert [a["name"] for a in out.albums] == ["School notices 2026-10"]
    assert "The album was not created. Continue with saving the digest only?" in out.questions
    assert out.saved_path is not None
    assert "Approval denied" in (out.digest or "")


def test_flow_c_album_denied_and_user_stops() -> None:
    fx = flow_a()
    fx["approvals"]["create_album:School notices 2026-10"] = False
    fx["user"]["continue_without_albums"] = False
    out = run_fixture(fx)
    assert out.status == "cancelled" and "Nothing more will be created" in out.report
    assert "save_digest" not in writes(out) and "tag_add" not in writes(out)


# ---- the five states and other edges --------------------------------------

def test_too_many_photos_asks_to_narrow_period() -> None:
    fx = flow_a()
    fx["experts"]["list_photos"]["result"]["total"] = 15
    out = run_fixture(fx)
    assert out.status == "waiting_user" and "shorter period" in out.report and len(out.calls) == 1


def test_everything_already_done() -> None:
    fx = flow_a()
    fx["experts"]["tag_lookup"]["result"]["tagged"] = [f["path"] for f in fx["experts"]["list_photos"]["result"]["files"]]
    out = run_fixture(fx)
    assert out.status == "completed" and "Nothing new" in out.report and writes(out) == []


def test_tag_lookup_failure_continues_with_all_photos() -> None:
    fx = flow_a()
    fx["experts"]["tag_lookup"] = {"status": "failed", "result": {"reason": "tag service down"}}
    for name in ("IMG_0100.jpg", "IMG_0101.jpg"):
        fx["experts"]["ocr"][name] = {"status": "completed", "result": {"text": "편의점\n물 1,000\n합계 1,000\n카드\n승인"}}
    out = run_fixture(fx)
    assert out.status == "completed" and len(out.calls_for("ocr")) == 9
    assert any("may appear again" in m for m in out.messages)


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
    assert out.status == "cancelled" and out.calls == []


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


def test_expert_waiting_user_resumes_same_step() -> None:
    fx = flow_a()
    fx["experts"]["save_digest"] = {"status": "waiting_user", "question": "A file with this name exists. Save as a new copy?",
                                    "then": fx["experts"]["save_digest"]}
    out = run_fixture(fx)
    assert out.status == "completed" and "A file with this name exists. Save as a new copy?" in out.questions
    assert [c.status for c in out.calls_for("save_digest")] == ["waiting_user", "completed"]


def test_save_failed_shows_digest_and_tags_album_photos_only() -> None:
    fx = flow_a()
    fx["experts"]["save_digest"] = {"status": "failed", "result": {"reason": "disk full"}}
    fx["approvals"]["create_album:Artwork – Mina 2026"] = False
    out = run_fixture(fx)
    assert out.status == "completed" and out.saved_path is None and out.digest_shown_in_conversation
    assert sorted(out.tagged) == [f"{P}IMG_010{i}.jpg" for i in range(2, 6)]
    assert "Digest saved" not in out.report and "its text is shown above" in out.report


def test_listing_fallback_to_photo_agent() -> None:
    fx = flow_a()
    fx["experts"]["list_photos_fallback"] = fx["experts"]["list_photos"]
    fx["experts"]["list_photos"] = {"status": "failed", "result": {"reason": "folder is a library view"}}
    out = run_fixture(fx)
    assert out.status == "completed" and out.calls[1].key == "list_photos_fallback" and out.calls[1].target == "photo-agent"


def test_listing_and_fallback_fail() -> None:
    fx = flow_a()
    fx["experts"]["list_photos"] = {"status": "failed"}
    out = run_fixture(fx)
    assert out.status == "failed" and "Step 1 failed" in out.report and len(out.calls) == 2


def test_album_add_by_path_fails_then_folder_fallback_after_agreement() -> None:
    fx = flow_a()
    fx["experts"]["create_album"]["School notices 2026-10"] = {"status": "failed", "result": {"reason": "add-item unsupported"}}
    fx["experts"]["create_album_fallback"] = {"status": "completed", "result": {"album_id": "fb-1", "count": 7}}
    fx["user"]["use_album_fallback"] = True
    out = run_fixture(fx)
    assert [c.key for c in out.calls if c.key.startswith("create_album")][:2] == ["create_album", "create_album_fallback"]
    assert any("fallback album" in q for q in out.questions)


def test_existing_album_add_declined() -> None:
    fx = flow_a()
    fx["experts"]["album_lookup"] = {"status": "completed", "result": {"albums": [{"name": "School notices 2026-10", "count": 3}]}}
    fx["user"]["add_to_existing"] = False
    out = run_fixture(fx)
    assert not [c for c in out.calls_for("create_album")]
    assert any("already exists" in q for q in out.questions)


def test_missing_value_stops_dependent_step() -> None:
    fx = flow_a()
    del fx["inputs"]["period"]
    with pytest.raises((DryRunError, KeyError)):
        run_fixture(fx)


def test_single_quote_in_value_is_escaped() -> None:
    fx = flow_a()
    fx["inputs"]["source_folder"] = "Photos/Mom's Phone"
    fx["inputs"]["output_folder"] = "Photos/Mom's Phone/Fridge Door"
    out = run_fixture(fx)
    first = out.calls[0].command
    assert "Mom'\\''s Phone" in first and "In the folder Photos/Mom's Phone and" in shlex.split(first)[4]
    assert_commands_valid(out)


def test_long_notice_is_condensed_first() -> None:
    fx = flow_a()
    long_text = fx["experts"]["ocr"]["IMG_0102.jpg"]["result"]["text"] + "\n" + " ".join(["안내"] * 420)
    fx["experts"]["ocr"]["IMG_0102.jpg"]["result"]["text"] = long_text
    fx["experts"]["condense"] = {"status": "completed", "result": {"text": "동의서 11월 1일까지 회신."}}
    out = run_fixture(fx)
    assert len(out.calls_for("condense")) == 1 and out.calls_for("condense")[0].target == "document-agent"


# ---- Should: archive (S2), child fallback (S3), carry-over (S4) -----------

def test_s2_past_due_flagged_and_archive_off_by_default() -> None:
    fx = flow_a()
    fx["today"] = "2026-11-02"
    out = run_fixture(fx)
    assert out.report.startswith("3 deadlines (2 past) (earliest: Pack a jump rope for PE, 11/04)")
    assert not out.calls_for("archive") and out.archived == []


def test_s2_archive_runs_only_on_explicit_request() -> None:
    fx = flow_a()
    fx["today"] = "2026-11-02"
    fx["inputs"]["archive_past"] = True
    fx["user"]["archive_yes"] = True
    fx["experts"]["archive"] = {"status": "waiting_approval", "then": {"status": "completed"}}
    out = run_fixture(fx)
    (call,) = [c for c in out.calls_for("archive") if c.status == "completed"]
    assert "Fridge Door/Archive 2026-11" in call.command
    assert sorted(out.archived) == [f"{P}IMG_0102.jpg", f"{P}IMG_0104.jpg"]  # past notices only
    assert "To be moved after approval: " in (out.digest or "") and "archive:" in out.approvals


def test_s3_people_album_assigns_child() -> None:
    fx = flow_a()
    fx["experts"]["figure_lookup"] = {"status": "completed", "result": {"matches": {f"{P}IMG_0107.jpg": "Jun"}}}
    fx["user"].pop("child_choice")
    fx["experts"]["create_album"]["Artwork – Mina 2026"]["then"]["result"]["count"] = 1
    fx["experts"]["create_album"]["Artwork – Jun 2026"] = {"status": "completed", "result": {"album_id": "a1f0c2d4-0003", "count": 1}}
    out = run_fixture(fx)
    assert {a["name"] for a in out.albums} == {"School notices 2026-10", "Artwork – Mina 2026", "Artwork – Jun 2026"}
    assert "Which child made IMG_0107.jpg?" not in out.questions and "(people album)" in (out.digest or "")


def test_s3_no_match_and_no_answer_leaves_child_not_chosen() -> None:
    fx = flow_a()
    fx["user"].pop("child_choice")
    out = run_fixture(fx)
    assert "Which child made IMG_0107.jpg?" in out.questions
    assert "### Child not chosen" in (out.digest or "") and f"{P}IMG_0107.jpg" not in sum((a["paths"] for a in out.albums), [])


def test_s4_open_items_carried_over() -> None:
    fx = flow_a()
    fx["experts"]["previous_digest"] = {"status": "completed", "result": {"text": "\n".join([
        "# Fridge Door – 2026-10-12 to 2026-10-18", "", "## At a glance", "- ...", "", "## Deadlines",
        '- [ ] 2026-10-24 — Return the library book · Jun · "10월 24일까지 반납" · IMG_0091.jpg',
        '- [x] 2026-10-22 — Sign the photo consent · Mina · "10월 22일까지" · IMG_0090.jpg',
        '- [ ] 2026-10-31 — field-trip fee · Mina · "10월 31일까지 납부" · IMG_0104.jpg',
        "", "## Events", "- none"])}}
    out = run_fixture(fx)
    assert out.carried == ['2026-10-24 — Return the library book · Jun · "10월 24일까지 반납" · IMG_0091.jpg · '
                           "carried over from Fridge Door – 2026-10-12 to 2026-10-18"]
    deadlines = (out.digest or "").split("## Deadlines")[1].split("\n## ")[0]
    assert "IMG_0091.jpg · carried over from" in deadlines and "IMG_0090.jpg" not in deadlines


# ---- #28 test kit dry run --------------------------------------------------

def test_testkit_core1_notices() -> None:
    out = run_fixture(load("testkit-a"))
    assert out.status == "completed"
    assert out.report.startswith("5 deadlines (1 past)") and ", 3 events," in out.report
    assert [a["name"] for a in out.albums] == ["School notices 2026-11"] and len(out.albums[0]["paths"]) == 8
    assert len(out.calls_for("translate")) == 4  # 3 English notices; one waited for approval
    assert sorted(u["reason"] for u in out.unrelated) == ["receipt", "screenshot"]
    assert len(out.tagged) == 8
    assert "KIT_N05.jpg · past" in (out.digest or "")


def test_testkit_core2_drawings() -> None:
    out = run_fixture(load("testkit-b"))
    assert out.status == "completed"
    assert {a["name"]: len(a["paths"]) for a in out.albums} == {"Artwork – Mina 2026": 2, "Artwork – Jun 2026": 3}
    assert sum("name read on the drawing" in a["how"] for a in out.artwork) == 2
    assert [u["path"].rsplit("/", 1)[1] for u in out.unreadable] == ["KIT_D06.jpg"]
    assert "Photos/PhoneBackup/Kit-B/KIT_D06.jpg" not in out.tagged and len(out.tagged) == 5


@pytest.mark.parametrize("name", ["testkit-a", "testkit-b"])
def test_testkit_second_run_reports_everything_done(name: str) -> None:
    fx = load(name)
    fx["experts"]["tag_lookup"]["result"]["tagged"] = [f["path"] for f in fx["experts"]["list_photos"]["result"]["files"]]
    out = run_fixture(fx)
    assert out.status == "completed" and writes(out) == [] and "already handled" in out.report


def test_all_skill_delegates_are_exercised() -> None:
    seen: set[str] = set()
    for fx in (flow_a(), flow_b(), load("testkit-a"), load("testkit-b")):
        seen |= {c.key for c in run_fixture(fx).calls}
    extra = flow_a()
    extra["experts"]["list_photos_fallback"] = copy.deepcopy(extra["experts"]["list_photos"])
    extra["experts"]["list_photos"] = {"status": "failed"}
    extra["experts"]["create_album"]["School notices 2026-10"] = {"status": "failed"}
    extra["experts"]["create_album_fallback"] = {"status": "completed", "result": {"album_id": "x", "count": 4}}
    extra["user"]["use_album_fallback"] = True
    extra["today"] = "2026-11-02"
    extra["inputs"]["archive_past"] = True
    extra["user"]["archive_yes"] = True
    extra["experts"]["archive"] = {"status": "completed"}
    long_text = extra["experts"]["ocr"]["IMG_0105.jpg"]["result"]["text"] + " 안내" * 420
    extra["experts"]["ocr"]["IMG_0105.jpg"]["result"]["text"] = long_text
    extra["experts"]["condense"] = {"status": "completed", "result": {"text": "학예회 11월 7일."}}
    seen |= {c.key for c in run_fixture(extra).calls}
    assert seen == set(load_templates())


def test_cli_prints_transcript(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(FIXTURES / "flow-a.json")]) == 0
    printed = capsys.readouterr().out
    assert printed.startswith("status: completed") and "## Digest" in printed and "## Report" in printed
