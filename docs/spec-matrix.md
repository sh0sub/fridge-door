# Spec matrix (Round 1 audit, 2026-11-01)

> 2026-11-13: the package was rewritten as v1.0.0 for uliya-skill-kit 0.7.7 (catalog structure 2.2.0) and revised the same day ("v1.0.0 second revision" at the end, which supersedes the step numbers, tag rule and counts of "v1.0.0 redesign"). The section "v1.0.0 redesign" supersedes the rows below for M2 (batch size), M7 (albums), S1-S4 (translation, child fallback, carry-over) and every test count, ZIP size and card sample. The rounds below are kept as history.

Source: planning artifact sections ugreen-01..09 and mockups ugreen-s1..s6. Status: match / gap / blocked.
Evidence: scripts/check.py (0 error, 0 warning), pytest 115 passed, ruff and mypy clean, `python3 -m scripts.dryrun tests/fixtures/dryrun/flow-a.json` (completed), dist ZIP identical to fridge-door/ sources.

| id | artifact section | expected | status | evidence |
|---|---|---|---|---|
| M1 | 05 features | Input collection with defaults, waiting_user | match | SKILL.md Required input; dryrun Q1 |
| M2 | 05 | Inventory max 12, depth 2, narrow-period ask | match | SKILL.md Step 1 |
| M3 | 05 | Exclude fridge-door-done tag, "nothing new" exit | match | Step 2; dryrun 2 already done |
| M4 | 05 | OCR + 3-way classify | match | Step 3 |
| M5 | 05 | Structure notice, quoted date, past flag, needs check | match | Step 5; digest example |
| M6 | 05 | VLM artwork check, name match | match | Step 4 |
| M7 | 05 | Albums after confirm, same-name check | match | Steps 6-7 |
| M8 | 05 | Digest saved, fixed sections | match (intended deviation) | digest-format.md; At a glance added and Not processed merged, justified in docs/plan.md:513 |
| M9 | 05 | Tag only handled files | match | Step 9 |
| M10 | 05 | 5 states, empty, partial, unreadable | match | Completion and failure section |
| S1-S4 | 05 | Translate, archive (off), figure fallback, weekly carry-over | match | SKILL.md Step 5 subsections and Step 10 |
| X1-X3 | 05 | Stretch (yearbook, Q&A, voice) | match (roadmap only, not required) | not in SKILL by design |
| FA | 06 flow A | Confirm, find, filter, OCR, VLM, preview, albums, save, tag, report | match | dryrun flow-a |
| FB | 06 flow B | English translation preview per notice | match (text only, no end-to-end fixture) | Step 5 Translation; no dryrun fixture for flow B |
| FC | 06 flow C | Empty period, unreadable list, album denied then digest only | match | Step 1, 7; integration tests |
| S1-strip | mockup S1 | Summary strip 9 found, 2 done, 7 to process | match (spec) | SKILL.md Step 6 item 1; never rendered as sample |
| S1-warn | mockup S1 | Yellow low-OCR warning, asks child | match (spec) | Step 6 item 2 |
| S1-groups | mockup S1 | Notices / Artwork / Not related groups with Due, To do, Child | match (spec) | Step 6 items 3-5 |
| S1-write | mockup S1 | Will create / Will save / Nothing moved line above question | match | Step 6 items 6-7 |
| S1-edit | mockup S1 | One-line text correction re-shows card | match | Step 6 item 7 |
| S1-states | mockup S1 | Loading "4/7 reading" state | match (round 1) | SKILL.md Step 3 progress line "Reading photos 4/7"; dryrun `progress`; test_loading_progress_line_per_photo |
| S1-render | mockup S1 | Preview card shown to a judge | match (round 1) | dryrun render_preview now prints the 7-part card; sample in references/README.md and gallery/00-chat.png; test_preview_card_* |
| S2-line | mockup S2 | Result line first, next-due highlight, created items with real IDs, status line | match (spec) | Step 11 completion card items 1-4 |
| S2-tag | mockup S2 | Status line "Tagged 6 photos fridge-door-done" | match (round 1) | SKILL.md Step 11 item 3; test_completion_card_four_parts_with_real_results |
| S2-render | mockup S2 | Completion card visible | match (round 1) | dryrun completion_card (4 parts, real ids and path only); README sample; gallery/00-chat.png; test_completion_card_* |
| S3 | mockup S3 | Digest Markdown preview, source file per item, checkbox | match | digest-format.md example, gallery 02-digest.png |
| S3-meta | mockup S3 | Meta line "7 photos read, generated on NAS timestamp", past mark | match (round 1) | digest-format.md meta line and `⚠` prefix replace "past"; dryrun digest; test_digest_meta_line_and_past_warning_prefix. At a glance and merged Not processed stay (docs/plan.md:513) |
| S4 | mockup S4 | Album grows 2 to 5 on rerun | match (spec) | Steps 6-7 add-to-existing; real UI only Round 2 |
| S4-img | mockup S4 | Photos app screenshot | blocked | needs real NAS (Round 2) |
| S5-pdf | mockup S5 | 1 page A4, 10 items, under 500 words, under 1 MB | match | PDF 91 KB, 484 words whole page (400 in the answers), 1 page |
| S5-layout | mockup S5 | Two columns 62/38 with NAS features table and test plan box | match | Two columns 62/38, NAS features table, boxed test plan; 1 page (R2 fix-r2/proposal.pdf.png) |
| S5-sign | mockup S5 | Name, signature, date, word count in footer | blocked | Name and signature are user input (checklist) |
| S5-claim | mockup S5 / 09 | "official static checker" claim true | gap | official check-skill.mjs not installed; docs/checks record is stale after test-plan.md change |
| S6 | mockup S6 | Round 2 video keyframes | blocked | Round 2 on iDX6011 Pro |
| 09-zip | 09 / checklist | ZIP under 10 MB, 5 files, check 0/0 | match | 14,711 bytes, identical to sources |
| 09-devpost | 09 | Devpost copy, thumbnail, 2+ gallery images | match | docs/submission |
| 09-gallery | 03 criteria | Gallery shows real card formats | match (round 1) | docs/submission/gallery/00-chat.png (preview and completion cards), 02-digest.png updated; devpost.md and checklist.md list it first. Real Photos album screenshot stays blocked (S4-img) |


Round 1 fix evidence: pytest 122 passed (7 new card tests), ruff and mypy clean, `python3 scripts/check.py fridge-door` 0 error 0 warning, dist ZIP rebuilt. New conformance tests: tests/integration/test_dryrun.py (card formats; README samples equal dry-run output).

## Round 2 audit (2026-11-01, independent)

Re-run: pytest 122 passed, ruff and mypy clean, `scripts/check.py` 0 error 0 warning, dry run flow-a completed (21 delegations, 2 waiting_approval then completed), dist ZIP identical to fridge-door/ sources (5 files, 38 KB), proposal 491 words. Screenshot reviewed: docs/submission/gallery/00-chat.png (preview and completion cards).

| id | artifact section | expected | status | evidence |
|---|---|---|---|---|
| R2-S1-card | mockup S1 | Preview card: counts strip, low-OCR warning, grouped lists, Will create/save, Proceed | match | dryrun Preview; 00-chat.png left card |
| R2-S1-lang | mockup S1 | Mockup mixes Korean chat copy | match (intended) | English output chosen for the English-language hackathon |
| R2-S2-card | mockup S2 | Result line, Next due highlight, real ids, grey status line, approval event | match | dryrun Completion card; 00-chat.png right card |
| R2-S3 | mockup S3 | Digest sections and checkbox, source file | match | dryrun Digest; 02-digest.png |
| R2-S4 | mockup S4 | Album growth 2 to 5 | blocked | needs real NAS (Round 2) |
| R2-S5 | mockup S5 | 1-page proposal under 500 words | match | 491 words |
| R2-count | 09 / submission | Test-count claims consistent | match | 123 tests stated in proposal.html, devpost.md, checklist.md (pytest 123 passed) |
| R2-official | 09 | "official static checker" claim | match | Wording now "local port of the official checker rules" (proposal, checklist); official kit not installed, rerun optional if user supplies it |

## Round 3 audit (2026-11-01, independent, full conformance)

Re-run: pytest 122 passed (.venv), ruff and mypy clean, `scripts/check.py fridge-door` 0 error 0 warning, dry run flow-a completed (21 delegations, 2 waiting_approval then completed, preview/progress/digest printed), dist ZIP extracted and diffed against fridge-door/ (identical, 15,854 bytes), proposal count 489 words, proposal.pdf 125 KB, git tree clean. Gallery 00-chat.png reviewed against mockups S1/S2.

| id | artifact section | expected | status | evidence |
|---|---|---|---|---|
| R3-S1 | mockup S1 | Preview card: counts strip 9/2/7, warning, grouped lists, Will create/save, Proceed | match | dryrun Preview; 00-chat.png |
| R3-S2 | mockup S2 | Completion card with Next due, real ids, grey status line | match | 00-chat.png right card |
| R3-S3 | mockup S3 | Digest preview with source files and checkboxes | match | dryrun Digest; 02-digest.png |
| R3-flow | 06 flows A/B/C | Confirm, read, preview, approve, save, tag; empty and denied paths | match | dryrun flow-a; integration tests |
| R3-S4 | mockup S4 | Real Photos album growth | blocked | needs real NAS (Round 2) |
| R3-S5 | mockup S5 | Signature and date | blocked | user input |
| R3-S6 | mockup S6 | Round 2 video keyframes | blocked | Round 2 on device |
| R3-official | 09 | Official check-skill.mjs 0 error | blocked | kit not installed, no third-party install allowed; docs/checks record stale |
| R3-win-real | criteria AI NAS Fit | Judge sees run on real data | blocked | cards are dry-run simulated; real NAS only Round 2 |

## Round 3 confirmation pass (2026-11-01, independent)

Re-run: pytest 122 passed, ruff and mypy clean, `scripts/check.py fridge-door` 0 error 0 warning, dry runs flow-a, testkit-a (translation, waiting_approval, same-name album check) and testkit-b (unreadable photo failed delegations, figure-name fallback) all completed, dist ZIP diffed against fridge-door/ (identical, 15,854 bytes).

| id | artifact section | expected | status | evidence |
|---|---|---|---|---|
| C3-FB | 06 flow B | Translation flow runnable | match | testkit-a dry run has 4 translate delegations, one waiting_approval; earlier row "no dryrun fixture for flow B" is stale |
| C3-FC | 06 flow C | Unreadable photos, fallback | match | testkit-b preview prints "Check needed ... could not be read" and Not related / unreadable section; 2 failed delegations handled |
| C3-S1-gallery | mockup S1 | Preview card sample consistent | gap (low) | gallery/00-chat.png says "Artwork (2)" but lists only IMG_0106; IMG_0107 appears only in the warning, unlike README sample and dry-run output (both list both items) |
| C3-zip-size | 09 / Devpost | ZIP size stated correctly | fixed (Round 3) | devpost.md:36 and checklist.md:18 now say 15,854 bytes (stat dist/fridge-door.zip = 15,854); checklist max file size corrected to 20,074 bytes (SKILL.md) |
| C3-S1-warn-render | mockup S1 | Low-OCR warning shown in a real run | match (spec) | flow-a dry run prints no warning (name read from the drawing); warning rendered in testkit-b and gallery |

## Round 4 audit (2026-11-01, independent, full conformance)

Re-run: pytest 122 passed, ruff and mypy clean, `scripts/check.py fridge-door` 0 error 0 warning, dry run flow-a completed (20 delegations listed, 2 waiting_approval then completed, digest printed), dist ZIP extracted and diffed against fridge-door/ (identical), git tree clean. Gallery 00-chat.png re-viewed against mockups S1/S2.

| id | artifact section | expected | status | evidence |
|---|---|---|---|---|
| R4-S1 | mockup S1 | Preview card: 9/2/7 strip, warning, grouped lists, Will create/save, Proceed | match | 00-chat.png left card |
| R4-S2 | mockup S2 | Completion card: Next due, real ids, tag line, grey status | match | 00-chat.png right card |
| R4-S3 | mockup S3 | Digest with source files, checkboxes, meta line | match | dryrun delegation 20 text |
| R4-flow | 06 flows A/B/C | Full flows runnable via dry run | match | flow-a, testkit-a, testkit-b |
| R4-gallery-artwork | mockup S1 | Gallery card: Artwork (2) lists both items | gap (low) | 00-chat.png and 00-chat.html:45 show "Artwork (2)" with only IMG_0106; IMG_0107 only in the warning. Still open from Round 3 |
| R4-S4/S5sign/S6/official | S4, S5, S6, 09 | Real NAS screens, signature, video, official checker | blocked | real NAS Round 2, user input, kit not installed |
| R4-win-real | criteria AI NAS Fit | Judge sees real-NAS run | blocked | dry-run only until Round 2 device |

## Round 4 confirmation pass (2026-11-01, independent)

Re-run: pytest 122 passed, ruff and mypy clean, `scripts/check.py fridge-door` static-pass (0 error 0 warning), dist ZIP extracted and diffed (identical, 15,854 bytes), proposal 489 words, flow-a dry run Preview/Progress/Digest/tag step re-read.

| id | artifact section | expected | status | evidence |
|---|---|---|---|---|
| R4C-gallery | mockup S1 / 09 gallery | First gallery image shows a consistent preview card | gap (medium) | gallery/00-chat.png and 00-chat.html:45-47: header "Artwork (2)" but only IMG_0106 listed (IMG_0107 missing); header merges "Not related (1)" on the same line; "Will save" line omits the "tag handled photos" clause the dry run prints. Dry run and README list both artworks. Open since Round 3, first image a judge sees |
| R4C-all | 05, 06, S1-S3, S5, 09 | everything else | match | see Round 4 table above |
| R4C-blocked | S4 image, S5 signature, S6, official checker, real-NAS run | n/a | blocked | real NAS Round 2, user input, kit not installed |

## Round 4 fix (2026-11-01)

| id | artifact section | expected | status | evidence |
|---|---|---|---|---|
| S1-gallery-artwork-list | mockup S1 / 09 gallery | Gallery preview card matches dry run and README: Artwork (2) lists IMG_0107 and IMG_0106, separate Not related group, Will save includes tag clause | fixed (Round 4) | gallery/00-chat.html and regenerated 00-chat.png; test_gallery_preview_card_lists_every_counted_artwork. Supersedes C3-S1-gallery, R4-gallery-artwork, R4C-gallery |

## Round 5 audit (2026-11-01, independent, full conformance)

Re-run: pytest 123 passed (.venv), ruff and mypy clean, `scripts/check.py fridge-door` static-pass (0 error 0 warning), dry run flow-a completed (21 delegations, 2 waiting_approval then completed, Preview/Progress/Digest printed), dist ZIP extracted and diffed against fridge-door/ (identical, 5 files, 15,854 bytes), proposal 489 words. Gallery 00-chat.png re-viewed: Artwork (2) lists both items, separate Not related group, tag clause present (Round 4 fix confirmed).

| id | artifact section | expected | status | evidence |
|---|---|---|---|---|
| R5-S1 | mockup S1 | Preview card 9/2/7 strip, warning, grouped lists, Will create/save, Proceed | match | dryrun Preview; 00-chat.png left card |
| R5-S2 | mockup S2 | Completion card Next due, real ids, tag line, grey status | match | 00-chat.png right card |
| R5-S3 | mockup S3 | Digest with source files, checkboxes, meta line | match | dryrun delegation 20 |
| R5-flow | 06 flows A/B/C | Runnable via dry run | match | flow-a, testkit-a, testkit-b |
| R5-count | 09 / Devpost | Test-count claim matches reality | match | fixed in Round 7: proposal.html, devpost.md, checklist.md now say 123 |
| R5-official | 09 | Official check-skill.mjs rerun | blocked | kit not installed; docs/checks/check-skill-2026-10-27.md stale (test-plan.md hash changed) |
| R5-S4/S5sign/S6/real | S4, S5, S6, criteria | Real NAS album, signature, video, real-data run | blocked | Round 2 device / user input |

## Round 6 confirmation (2026-11-01, independent)

Re-run: pytest 123 passed, ruff and mypy clean, `scripts/check.py fridge-door` 0 error 0 warning, flow-a dry run completed, dist ZIP extracted and diffed (identical).

| id | artifact section | expected | status | evidence |
|---|---|---|---|---|
| R6-count | 09 / Devpost | Test-count claim matches pytest | match | fixed in Round 7 (all docs say 123, pytest 123 passed) |
| R6-all | 05, 06, S1-S3, S5 | Everything else | match | Round 5 table reconfirmed by dry run output |
| R6-blocked | S4, S5 signature, S6, official checker, real NAS | n/a | blocked | device/user input, kit not installed |

## Round 7 polish (2026-11-01)

Re-run: pytest 123 passed (.venv), ruff and mypy clean, dist ZIP rebuilt (15,854 bytes, 5 files, identical), proposal.pdf regenerated (125,834 bytes, 1 page, 489 words). Test-count claims fixed to 123 in proposal.html, devpost.md (:47, :60), checklist.md; checklist PDF size updated. ZIP size, file count, kit numbers (16 photos, 13 handled) rechecked, all consistent.

## v1.0.0 redesign (2026-11-13)

Source: redesign spec 2026-11-13 (kit 0.7.7 catalog review). Evidence: `scripts/check.py fridge-door --catalog <kit catalog>` static-pass 0 error 0 warning (catalog 2.2.0, evidence lines match the catalog's CLI→agent values); pytest 152 passed, 1 skipped (153 passed with `FRIDGE_DOOR_KIT_CATALOG`); ruff and mypy clean; dry runs flow-a (one batch) and testkit (12 + 4 after "continue") completed; `dist/fridge-door.zip` 5 files, 20,510 bytes, identical to sources. The official `check-skill.mjs` was not run (docs/checks/check-skill-2026-11-13.md).

| id | spec section | expected | status | evidence |
|---|---|---|---|---|
| V1-format | 1 | Required h1s, evidence heading and `→` lines, single-line delegates, `'"'"'` escape only, 5 state tokens, forbidden strings | match | local checker 0/0; test_quote_escape_rule_matches_check_lib |
| V1-translate | 2.1 | No condense or translate delegation; Uliya writes summaries in the parent language, dates/amounts/names as written; optional translated copy of the saved digest only | match | Step 5 (no delegate), Step 13; test_step5_*, test_translated_copy_*; testkit summaries keep "$12.00" |
| V1-keepsake | 2.2 | Per-child keepsake folder `{output_folder}/Artwork - {child}`, copy (not move, no overwrite), one delegation per child | match | Step 8; test_step8_*, test_copy_name_conflict_is_reported_not_retried |
| V1-album | 2.2 | One album per child that follows the folder, created once; existing album means no creation; notice album and child fallback removed | match | Steps 7, 9; test_album_created_once_then_followed, test_existing_album_skips_creation |
| V1-album-fallback | 2.2 | Folder rule unsupported → regular album from a folder search; copy failure → no album | match (test-plan only) | test-plan.md fallback table; harness reports "could not be used as the album rule" |
| V1-save | 2.3 | Folder check before save, hint fridge-door-digest, only the returned path, save is not index readiness | match | Step 10; test_step10_*, test_save_without_verified_path_is_not_a_save |
| V1-carry | 2.4 | Find and read are separate; only an explicit "none" means no carry-over; cut-short read carries nothing; items done at the preview are ticked | match | Step 6; test_carry_over_*, test_empty_find_result_is_not_proof_of_none, test_cut_short_read_carries_nothing |
| V1-question | 2.5 | Questions about saved digests answered from the newest digest with sources, read only | match | "Questions about saved digests"; test_question_* |
| V1-batch | 2.6 | List up to 60 oldest first, batches of 12, "continue" only on request | match | Steps 1-2; test_batches_of_twelve_wait_for_continue, test_continue_reads_only_the_rest |
| V1-tag | 2.7 | Tag only verified-save notices and copied drawings | match | Step 11; test_no_album_without_copies, test_save_failed_shows_digest_and_keeps_notices_untagged |
| V1-states | 3 | waiting_* as resume flows, no labels on chat questions, refused approval follows the resumed terminal state, Done / Partly done | match | Completion and failure; test_five_states_follow_kit_077, test_refused_* |
| V1-privacy | 4 | No absolute "nothing leaves the NAS" claims; "this Skill called no outside service" | match | test_20_no_absolute_privacy_claims |
| V1-version | 5 | 1.0.0, disclosures for kit 0.7.7 / catalog 2.2.0, expected Actions with catalog effect and approval | match | references/README.md, disclosures.md; test_22_* |
| V1-numbers | 6 | 16-photo kit, 6 deadlines (1 past) + 2 events, 5 copies, 13 tags, 12 + 4 batches, Mina/Jun, 2026-11-23 week | match | test-plan.md expected results; test_testkit_* |
| V1-output-exclusion | gap found | Copies in the keepsake folder sit inside the source folder (depth 2) and would be listed next week | fixed | Step 1 leaves out `{output_folder}`; test_listing_must_leave_out_the_output_folder |
| V1-proposal | 09 | Proposal and Devpost describe the v1.0.0 package | not checked here | docs/proposal and docs/submission/devpost.md are maintained in a separate task |
| V1-device | 06 | Real NAS behaviour of each delegation | blocked | test-plan.md "Assumptions not yet checked on a device" (12 items); Round 2 |

## v1.0.0 second revision (2026-11-13)

Source: revision spec v2 (independent technical review and judge scoring of the first rewrite). Evidence: `scripts/check.py fridge-door --catalog <kit catalog>` static-pass 0 error 0 warning; pytest 204 passed, 1 skipped (205 with `FRIDGE_DOOR_KIT_CATALOG`); ruff and mypy clean; `dist/fridge-door.zip` 5 files, 25,749 bytes, identical to sources. Step numbers below are the new ones (15 steps; Step 1 is now the digest look-up).

| id | spec item | expected | status | evidence |
|---|---|---|---|---|
| V2-A1 | A1 | Tag exists but no listed file carries it is a normal answer, not a failure | match | Step 3 instruction and bullets; test_tag_exists_but_no_listed_file_carries_it |
| V2-A2 | A2 | Folder look-ups return the real full NAS path; the save gets `{output_folder_path}`, never the visible name | match | Steps 1, 11; test_save_goes_to_the_real_folder_path, test_folder_check_without_path_blocks_save |
| V2-A3 | A3 | Keepsake folder listing returns real path and file id; album rule uses both; missing either means no album | match | Steps 9, 10; test_album_gets_real_folder_path_and_id, test_missing_folder_id_means_no_album |
| V2-A4 | A4 | No "one approval" claim; copied files decided from the folder listing; separate folder approval mentioned | match | Step 9; test_copy_with_counts_only_is_judged_by_the_folder_listing |
| V2-A5-tag | A5 | Tag = handled once: notices, drawings (copied or same name), unrelated, unreadable after a verified save; failed photos never | match | Step 12; test_unreadable_photo_is_listed_tagged_and_still_done, test_failed_photo_is_never_tagged_and_makes_partly_done, test_unrelated_photos_are_tagged_only_after_a_verified_save |
| V2-A5-period | A5 | Digest first; "Next run starts from" in the meta line; default period from it to today (max 31 days), else 7 days | match | Required input, Steps 1, 11; test_default_period_*, test_next_run_starts_from_in_the_test_kit |
| V2-A5-order | A5 | Folder, children, language, then digest look-up, then one read-back with the period | match | Required input; test_default_period_starts_where_the_last_digest_stopped |
| V2-A5-60 | A5 | School folder recommended; optional narrowing over 60 photos, oldest 60 when it fails | match | Required input, Step 2, README "Which folder to use"; test_narrowing_*, test_listing_over_sixty_* |
| V2-A6 | A6 | Same-name drawing counts as handled and is tagged | match | Step 9; test_same_name_drawing_counts_as_handled |
| V2-A7 | A7 | Newest digest by creation time; translated copies and journals left out | match | Step 1; test_newest_digest_by_creation_time_not_translation_or_journal |
| V2-A8 | A8 | Same-name album counts as existing; another folder → ask for a new name | match (text) | Step 8; test_step8_album_lookup_and_preview |
| V2-A9 | A9 | Test-plan numbers recomputed; no new digest when nothing is new; Sora/Tae refusal edge; D06 two cases | match | test-plan.md; test_testkit_* |
| V2-B1 | B1 | Upcoming events carry over, past ones do not | match | Step 7; test_upcoming_events_carry_over_and_past_events_do_not |
| V2-B2 | B2 | "Done." only when every step completed and every planned item came back | match | Step 15; test_partial_tagging_is_partly_done |
| V2-B3 | B3 | Failed tag look-up asks before continuing | match | Step 3; test_tag_lookup_failure_* |
| V2-B4 | B4 | Fallback listing says when it returned fewer paths than the total | match | Step 2; test_fallback_listing_says_when_fewer_paths_than_total |
| V2-B5 | B5 | Questions and journal need only the output folder (and the child) | match | Required input; test_question_needs_only_the_output_folder, journal tests |
| V2-B6 | B6 | Preview shows "unknown, please tell me" until the parent answers; no invented summary content | match | README and digest-format examples equal the dry run; test_preview_shows_unknown_child_until_the_parent_answers |
| V2-B7 | B7 | Checker `\s` matches JavaScript's Unicode whitespace | match | scripts/check.py `js_re`, `js_trim`; test_unicode_space_* |
| V2-C1 | C1 | Child's words kept verbatim on the artwork line, asked once | match | Step 8, digest-format.md; test_child_note_is_kept_word_for_word |
| V2-C2 | C2 | Artwork journal on request, document-agent reads verbatim lines; file-agent fallback over 8 digests; save on request | match | "Artwork journal" section; test_journal_* |
| V2-D | D | All five package files, tests, harness, README, check record and ZIP consistent; 16 device assumptions | match | test_22_*; docs/checks/check-skill-2026-11-13.md |
| V2-gallery | D | Gallery and Devpost match the revised cards | not checked here | docs/submission is maintained in a separate task |

## v1.0.0 third revision (2026-11-13)

Source: final revision after a second independent attack on the v2 package (items A–E and 1–13). Step numbers kept (digest look-up 1, listing 2, tag look-up 3, text 4, picture check 5, copy 9, album 10, save 11, tag 12, optional 13–14, report 15); the output folder check moved from Step 11 to the first delegation of Step 9. Evidence: `scripts/check.py fridge-door --catalog <kit catalog>` static-pass 0 error 0 warning; pytest 214 passed, 1 skipped (215 with `FRIDGE_DOOR_KIT_CATALOG`); ruff and mypy clean; `dist/fridge-door.zip` 5 files, 27,577 bytes, identical to sources.

| id | spec item | expected | status | evidence |
|---|---|---|---|---|
| V3-A | A | Album check after the parent's corrections, including children assigned at the preview; preview shown again; album step only after a completed check that found no album | match | Steps 8, 10; test_album_check_runs_for_a_child_chosen_at_the_preview, test_no_album_when_the_check_after_the_preview_did_not_complete |
| V3-B | B | "Next run starts from": oldest photo no batch of the run tags (earlier batches included), else the last day of the period; a start later than today gives today alone | match | Required input 5, Step 11, digest-format.md, README; test_same_day_rerun_and_a_photo_added_later_that_day, test_untagged_photo_of_an_earlier_batch_sets_the_next_start, test_next_start_later_than_today_gives_today_alone |
| V3-C | C | Tagging failure names the untagged photos; no "start from the first day" advice | match | Step 12, test-plan fallback; test_tagging_failure_says_where_to_start_next |
| V3-D | D | First-run default is the last 7 days including today; Core 1 names its period; upload can set modification times | match | Required input 5, test-plan "Test kit", Edge Kit2 run; test_default_period_without_digest_is_last_seven_days |
| V3-E | E | Test plan gives the signing answers (Mina 김민아, Jun 이준; Sora and Tae do not sign) | match | test-plan Core 1, Edge |
| V3-1 | 1 | "continue" after an unsaved digest keeps the Step 1 digest | match | Step 3; test_continue_after_an_unsaved_digest_keeps_the_step1_digest |
| V3-2 | 2 | Cut listing with every listed photo tagged offers the period from the newest listed date | match | Step 3; test_cut_listing_with_every_listed_photo_tagged_offers_the_newer_period |
| V3-3 | 3 | No verified save: nothing is tagged, not even drawings | match | Step 12, digest-format.md, README, test-plan; test_save_failed_shows_digest_and_keeps_notices_untagged |
| V3-4 | 4 | Output folder check before the copy; copy and listing use `{output_folder_path}/Artwork - {child}`; step numbers kept | match | Step 9; test_flow_a_order_digest_first_then_copy_list_album_save_tag, test_step9_folder_check_then_copy_then_read_the_folder |
| V3-5 | 5 | Picture check NO on a paper document without readable text goes to unreadable | match | Step 5; test_paper_document_without_readable_text_is_unreadable_not_unrelated |
| V3-6 | 6 | Open items reported as unticked deadlines and upcoming events | match | Step 3, test-plan; test_testkit_rerun_same_period_creates_nothing |
| V3-7 | 7 | Journal fallback says "the N most recent digests (at most 8)"; document expert says whether every document was read in full | match | Artwork journal; test_journal_fallback_reads_the_eight_newest_digests, test_journal_names_a_digest_not_read_in_full |
| V3-8 | 8 | Goal names the optional archive exception | match | Goal |
| V3-9 | 9 | Core 1 asks at most for the output folder (besides signing) | match | test-plan Core 1 |
| V3-10 | 10 | Disclosures list the folder check, keepsake folder creation and storage type; no regular-album fallback claimed | match | disclosures.md, test-plan fallback |
| V3-11 | 11 | Card says "This Skill asked only the NAS experts; the AI model they use is the one the NAS owner set up."; carry-over and "read once" claims qualified | match | Step 15, README, digest-format.md; test_completion_card_with_real_results |
| V3-12 | 12 | Device assumptions 17–19 added (date filter and folder scope, storage type, 60-file limit after leaving out the output folder); 2 and 14 widened | match | test-plan.md (19 items); test_22_test_plan_contents |
| V3-13 | 13 | Digest chosen by the file-name timestamp, else the creation time | match | Step 1; test_digest_names_without_timestamp_are_chosen_by_creation_time |
| V3-device | – | Real NAS behaviour of each delegation | blocked | test-plan.md assumptions (19); Round 2 |
