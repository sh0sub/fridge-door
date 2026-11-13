"""SKILL.md core workflow (v1.0.0, kit 0.7.7): each step says what the redesign spec asks for."""

from __future__ import annotations

import re

from tests.skill_helpers import check_errors, delegates, delegates_in, section, skill_text

STATUS_LABEL = re.compile(r"\(`waiting_(?:user|approval)`\)")


def test_skill_has_no_checker_errors_besides_missing_references() -> None:
    assert check_errors(ignore_missing_references=True) == []


# ---- input collection ------------------------------------------------------

def test_inputs_with_defaults() -> None:
    req = section("Required input")
    for name in ("source_folder", "period", "children", "parent_language", "output_folder", "archive_past", "copy_language", "today"):
        assert f"`{{{name}}}`" in req, name
    assert "last 7 days" in req and "2026-11-23 to 2026-11-29" in req
    assert "Default: a subfolder named Fridge Door inside `{source_folder}`" in req
    assert "Default: the language the user is speaking" in req


def test_read_back_is_a_chat_question_not_a_waiting_state() -> None:
    req = section("Required input")
    assert "ask the user in the chat and wait for the answer" in req
    assert "Shall I go ahead?" in req and "Mina and Jun" in req
    assert "never fill it with a guess" in req
    assert not STATUS_LABEL.search(req)  # questions the Skill asks itself carry no waiting_* label


def test_quote_escape_rule_matches_check_lib() -> None:
    req = section("Required input")
    assert "'\"'\"'" in req and "'\\''" not in skill_text()


def test_keepsake_and_album_names_use_ascii_hyphen() -> None:
    text = skill_text()
    assert "`{output_folder}/Artwork - {child}`" in text and "`Artwork - {child}`" in text
    assert "–" not in text.replace("Fridge Door –", "")  # no en dash in names
    assert "School notices {" not in text and "album School notices" not in text  # notice album removed


def test_no_delegate_in_input_collection() -> None:
    assert delegates(section("Required input")) == []


# ---- Step 1: newest digest first (default period) ---------------------------

def test_step1_find_by_creation_time_then_read() -> None:
    find, read = delegates_in("Step 1")
    assert find.target == read.target == "file-agent"
    assert "starts with fridge-door-digest" in find.instruction and "{output_folder}" in find.instruction
    assert "choose by the timestamp in the file name; if the names carry none, by the time the file was created" in find.instruction
    assert "never by modification time" in find.instruction
    assert "Leave out translated copies" in find.instruction and ".en.md" in find.instruction
    assert "starts with fridge-door-journal" in find.instruction
    assert "real full NAS path of the folder {output_folder}" in find.instruction
    assert "say clearly which of the two is the case" in find.instruction
    assert "Read the file at exactly {previous_digest_path}" in read.instruction
    assert "complete or was cut short" in read.instruction and "Only read" in read.instruction
    assert "cat " not in read.instruction


def test_step1_sets_next_start_and_default_period() -> None:
    step = section("Step 1", 2)
    assert '"Next run starts from:"' in step and "`{next_start}`" in step
    assert "does not say that none exists" in step and "use the 7-day default period" in step
    assert "If the content was cut short, carry nothing over, use the 7-day default period" in step
    assert "If it has no such date, use the 7-day default period and say so" in step
    req = section("Required input")
    assert "Default: from `{next_start}` to `{today}`" in req and "last 7 days including `{today}`" in req
    assert "if `{next_start}` is later than `{today}`, from `{today}` to `{today}`" in req
    assert "longer than 31 days, ask the user for a period" in req


def test_inputs_order_folder_children_language_then_digest_then_read_back() -> None:
    req = section("Required input")
    assert "Collect values 1 to 4 first, then run Step 1. Then read every value back in one sentence, including the period" in req
    assert "(where the last digest stopped)" in req


def test_question_and_journal_modes_need_only_the_output_folder() -> None:
    req = section("Required input")
    assert "Questions about saved digests and the artwork journal need only `{output_folder}`" in req
    assert "do not ask for the other values there" in req


def test_school_folder_is_recommended() -> None:
    req = section("Required input")
    assert "A folder that mostly holds school photos is recommended" in req and "School album" in req


# ---- Step 2-3: inventory and batches ---------------------------------------

def test_step2_listing() -> None:
    d = delegates_in("Step 2")
    assert [x.target for x in d] == ["file-agent", "photo-agent", "photo-agent"]
    first = d[0].instruction
    for phrase in ("image files", "{period}", "depth 2", "Leave out everything inside the folder {output_folder}", "oldest first",
                   "at most 60 files", "how many files match in total", "Only read", "say clearly that none was found"):
        assert phrase in first, phrase
    assert "{output_folder}" in d[2].instruction and "say clearly that none was found" in d[2].instruction


def test_step2_narrowing_branch_over_sixty() -> None:
    narrow = delegates_in("Step 2")[1].instruction
    assert "look like a paper document with printed or handwritten text" in narrow and "drawing or craft made by hand" in narrow
    assert "recognition results the photo library already has" in narrow
    assert "has not finished recognising these photos" in narrow and "return no list" in narrow
    step = section("Step 2", 2)
    assert "More than 60 matching photos" in step and "Only if the user agrees, ask once" in step
    assert "narrowing did not work and continue with the oldest 60" in step


def test_step2_empty_fallback_and_short_list() -> None:
    step = section("Step 2", 2)
    assert "no results" in step and "Do not search other folders or widen the period" in step
    assert "Only if the listing ends as `failed`" in step and "no file paths, stop" in step
    assert "fewer paths than the total it reports, say so" in step


def test_step3_tags_and_batches() -> None:
    (d,) = delegates_in("Step 3")
    assert d.target == "file-agent" and "fridge-door-done" in d.instruction and "{photo_list}" in d.instruction
    assert "If the tag exists but none of these files carry it, say clearly that none of them carry it" in d.instruction
    assert "say clearly that it does not exist" in d.instruction and "Only read" in d.instruction
    step = section("Step 3", 2)
    assert "oldest 12 photos of `{new_photos}` as `{batch}`" in step and "`{remaining_count}`" in step
    assert "Do not start the next batch on your own" in step and '"continue"' in step
    assert "every photo is new" in step


def test_step3_failed_lookup_asks_before_continuing() -> None:
    step = section("Step 3", 2)
    assert "photos handled before may appear again, ask in the chat whether to continue and wait" in step
    assert "If the user says no, finish with nothing created" in step


def test_step3_nothing_new_creates_no_digest() -> None:
    step = section("Step 3", 2)
    assert "If `{new_photos}` is empty" in step and "has open items, say how many unticked deadlines and how many upcoming events" in step
    assert "If `{new_photos}` is empty and more photos matched than were listed, say so and offer the period from the date of the newest listed photo" in step
    assert "if that batch saved no verified digest, keep the `{previous_digest}` read in Step 1" in step
    assert "do not save a new digest" in step


# ---- Step 4-6: reading -----------------------------------------------------

def test_step4_text_reading() -> None:
    (d,) = delegates_in("Step 4")
    assert d.target == "photo-agent" and "{photo_path}" in d.instruction
    assert "Read all printed and handwritten text" in d.instruction and "do not add or correct text" in d.instruction
    assert "say clearly that no text was found" in d.instruction
    step = section("Step 4", 2)
    assert "`{notice_items}`" in step and "candidate artwork" in step and "`{unrelated_items}`" in step
    assert "Never guess" in step and "real result `{ocr_text}`" in step


def test_step5_artwork_check_unreadable_and_failed() -> None:
    (d,) = delegates_in("Step 5")
    assert d.target == "photo-agent"
    assert "YES if it shows a drawing, painting or craft made by a child, otherwise NO" in d.instruction
    assert "Do not guess the name or age" in d.instruction
    step = section("Step 5", 2)
    assert "NO: add to `{unrelated_items}`" in step and "contains a name from `{children}`" in step
    assert "`{unknown_artwork}`" in step and "parent chooses the child at the preview" in step
    assert "cannot see the image clearly" in step and "`{unreadable_items}`" in step
    assert "If Step 4 found no readable text but the sentence describes a paper document" in step
    assert "ends as `failed`: add the file name to `{failed_items}`" in step and "next run tries them again" in step


def test_step6_structuring_is_done_by_uliya_not_delegated() -> None:
    step = section("Step 6", 2)
    assert delegates(step) == [] and "there is no delegation" in step
    for phrase in ("title", "sender (school and class)", "due, event, payment", "amount", "source file name",
                   "Quote the original date text", '"needs check"', "earlier than `{today}` as past"):
        assert phrase in step, phrase
    assert "translate only this summary line" in step and "keep dates, amounts and names exactly as written" in step
    assert "Write only what the notice says" in step and "document-agent" not in step


# ---- Step 7: carry over (no delegation) -------------------------------------

def test_step7_carries_open_deadlines_and_upcoming_events() -> None:
    step = section("Step 7", 2)
    assert delegates(step) == [] and "There is no delegation" in step
    assert "deadline line that is still unticked (`- [ ]`)" in step and "event line dated `{today}` or later" in step
    assert "past events are dropped" in step and "`- [x]` are done" in step and '"carried over from"' in step
    assert "already done, write it as `- [x]`" in step


# ---- Step 8: preview ----------------------------------------------------------

def test_step8_album_lookup_and_preview() -> None:
    (d,) = delegates_in("Step 8")
    assert d.target == "photo-agent" and "name is exactly {album_name}" in d.instruction and "Only read" in d.instruction
    assert "the folder it follows" in d.instruction
    step = section("Step 8", 2)
    assert "An album with this name counts as existing" in step
    assert "follow a folder other than `{keepsake_folder}`" in step and "ask for a new album name" in step
    assert "N in this batch · N left for later" in step
    assert "the same drawing can show twice in UGREEN Photos" in step
    assert "nothing is moved or deleted. Proceed?" in step and "the fee is already paid" in step
    assert "If the user declines, show the digest text in the chat instead and finish with nothing created" in step
    assert "offer to save a short digest that lists the photos" in step
    assert ("Run the album check for every child who has artwork after the parent's corrections, including children assigned at the preview, "
            "and show the preview again.") in step


def test_step8_child_note_kept_word_for_word() -> None:
    step = section("Step 8", 2)
    assert "If your child said something about a drawing, tell me and I will keep it with the picture (optional)." in step
    assert "keep those words exactly as `{child_note}`" in step and "without correcting them" in step
    assert "If the parent does not answer that line, do not ask again" in step


# ---- Steps 9-10: keepsake folder and living album ----------------------------

def test_step9_folder_check_then_copy_then_read_the_folder() -> None:
    folder, copy_d, listing = delegates_in("Step 9")
    assert folder.target == copy_d.target == listing.target == "file-agent"
    assert "Check whether the folder {output_folder} exists" in folder.instruction
    assert "In both cases return the real full NAS path of the folder" in folder.instruction
    assert "Copy these image files into the folder {output_folder_path}/Artwork - {child}" in copy_d.instruction
    assert "{child_artwork_paths}" in copy_d.instruction and "{keepsake_folder}" not in copy_d.instruction
    assert "do not move, rename, change or delete the original files" in copy_d.instruction and "Never overwrite" in copy_d.instruction
    assert "one approval" not in copy_d.instruction and "or the counts if that is all you have" in copy_d.instruction
    assert "List the files directly inside the folder {output_folder_path}/Artwork - {child}" in listing.instruction
    assert "real full NAS path of the folder, the file id of the folder, the storage type of the folder" in listing.instruction
    assert "Only read" in listing.instruction
    step = section("Step 9", 2)
    assert "never pass the folder name the user sees" in step and "tag nothing" in step
    assert "separately, for creating the keepsake folder (`waiting_approval`)" in step
    assert "`{copied_paths}` holds the listed paths whose file name matches" in step
    assert "`{same_name_items}`. Both count as handled" in step and "`{keepsake_folder_id}`" in step and "`{keepsake_storage_type}`" in step


def test_step10_album_gets_real_folder_path_and_id() -> None:
    (d,) = delegates_in("Step 10")
    assert d.target == "photo-agent"
    assert ("every photo in the folder {keepsake_folder_path} (folder file id {keepsake_folder_id}, storage type {keepsake_storage_type})"
            in d.instruction)
    assert "including photos added to this folder later" in d.instruction
    assert "create no album and say so clearly" in d.instruction and "real album identifier" in d.instruction
    step = section("Step 10", 2)
    assert "Run the album step only for a child whose check completed and found no album" in step
    assert "at least one path in `{copied_paths}`" in step and "If the check did not complete, create nothing" in step
    assert "If the check found the album, create nothing" in step and "after the NAS indexes them" in step
    assert "If `{keepsake_folder_path}`, `{keepsake_folder_id}` or `{keepsake_storage_type}` is missing, do not run this step" in step


# ---- Steps 11-12: save and tag ------------------------------------------------

def test_step11_save_to_the_real_path_from_step9() -> None:
    (save,) = delegates_in("Step 11")
    assert save.target == "knowledge-agent" and "existing folder {output_folder_path}" in save.instruction
    assert "{output_folder}" not in save.instruction
    assert "file name hint fridge-door-digest" in save.instruction and "{digest_text}" in save.instruction
    assert "Do not overwrite" in save.instruction and "verified" in save.instruction
    step = section("Step 11", 2)
    assert "[references/digest-format.md](references/digest-format.md)" in step and "seven sections in fixed order" in step
    assert "Save to `{output_folder_path}` from Step 9; if Step 9 returned none, do not save" in step
    assert "never build a file name yourself" in step and "does not mean the digest is searchable" in step


def test_step11_next_run_starts_from_rule() -> None:
    step = section("Step 11", 2)
    assert '"Next run starts from:"' in step and "oldest photo of `{photo_list}` that carries no fridge-door-done tag" in step
    assert "that no batch of this conversation tags" in step and "in this batch or an earlier one" in step
    assert "the date of the newest listed photo also counts" in step and "write the last day of `{period}`" in step
    assert "day after" not in step


def test_step12_tag_means_handled_once() -> None:
    (d,) = delegates_in("Step 12")
    assert d.target == "file-agent" and "fridge-door-done" in d.instruction and "{handled_paths}" in d.instruction
    assert "Do not remove or change any other tag" in d.instruction
    step = section("Step 12", 2)
    assert "The tag means Fridge Door has handled the photo once" in step
    assert "`{unrelated_items}` and `{unreadable_items}`" in step and "`{same_name_items}`" in step
    assert "When the save was not verified, tag nothing, not even the drawings" in step
    assert "Photos in `{failed_items}`, drawings that were not copied and drawings whose child was not chosen are never tagged" in step
    assert ("If tagging fails, say which photos are untagged. The saved digest already starts the next run after them; "
            "if the parent reruns this period explicitly, these photos will be read again.") in step
    assert "first day of `{period}`" not in step


# ---- Step 15 and the five states ---------------------------------------------

def test_report_done_or_partly_done() -> None:
    report = section("Step 15", 2)
    assert 'Start with "Done." only when every planned step of this batch ended as `completed` and every planned item came back' in report
    assert "a photo in `{failed_items}` does" in report
    assert '"Partly done."' in report and "steps still waiting" in report and "not run because an earlier step" in report
    assert '"This Skill asked only the NAS experts; the AI model they use is the one the NAS owner set up."' in report
    assert "called no outside service" not in report
    assert "stayed on this NAS" not in skill_text() and "No data leaves" not in skill_text()


def test_five_states_follow_kit_077() -> None:
    done = section("Completion and failure")
    for token in ("completed", "failed", "cancelled", "waiting_user", "waiting_approval"):
        assert f"- `{token}`:" in done, token
    assert "resumes the same delegation" in done and "Do not start a replacement delegation" in done
    assert "the user's yes at the preview is not that approval" in done
    assert "follow the terminal state the resumed delegation actually returns" in done
    assert "Denied approval counts as" not in done
    assert "is not proof of no matches" in done


def test_partial_and_retry_rules() -> None:
    done = section("Completion and failure")
    assert "Partial completion is an assessment, not a state" in done
    assert "Never retry them automatically" in done and "risk of duplicates" in done
    assert "A local static check is not a run on the NAS" in done


def test_delegates_use_only_catalog_agents_and_no_cli_names() -> None:
    assert {d.target for d in delegates()} == {"file-agent", "photo-agent", "document-agent", "knowledge-agent"}
    assert "never runs `cli.invoke` itself" in skill_text()
    actions = ("vision-ocr", "vision-vlm", "create-album", "save-text", "batch-transfer", "tag-add", "cpmv", "mkdir", "translate ",
               "ug-photo", "ug-filesystem", "ug-filemgr", "file-workflow", "ug-knowledge", "ug-document", "--path", "--dir")
    for d in delegates():
        for word in actions:
            assert word not in d.instruction, (word, d.line)


def test_every_instruction_is_self_contained() -> None:
    for d in delegates():
        ins = d.instruction
        assert re.search(r"\b(?:Only read|do not|Do not|Never)\b", ins), d.line  # a negative condition
        assert re.search(r"\b(?:Return|say|Say)\b", ins), d.line  # what to give back
        assert "{" in ins, d.line  # a real value, never "the folder above"


def test_body_length() -> None:
    body = skill_text().split("---", 2)[2]
    assert len(body.strip().splitlines()) <= 270
