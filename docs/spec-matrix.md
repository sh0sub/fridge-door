# Spec matrix (Round 1 audit, 2026-11-01)

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
| S5-pdf | mockup S5 | 1 page A4, 10 items, under 500 words, under 1 MB | match | PDF 109 KB, 491 words, 1 page |
| S5-layout | mockup S5 | Two columns 62/38 with NAS features table and test plan box | gap (low) | PDF is single column, details inlined in items 6 and 9 |
| S5-sign | mockup S5 | Name, signature, date, word count in footer | blocked | Name and signature are user input (checklist) |
| S5-claim | mockup S5 / 09 | "official static checker" claim true | gap | official check-skill.mjs not installed; docs/checks record is stale after test-plan.md change |
| S6 | mockup S6 | Round 2 video keyframes | blocked | Round 2 on iDX6011 Pro |
| 09-zip | 09 / checklist | ZIP under 10 MB, 5 files, check 0/0 | match | 14,711 bytes, identical to sources |
| 09-devpost | 09 | Devpost copy, thumbnail, 2+ gallery images | match | docs/submission |
| 09-gallery | 03 criteria | Gallery shows real card formats | match (round 1) | docs/submission/gallery/00-chat.png (preview and completion cards), 02-digest.png updated; devpost.md and checklist.md list it first. Real Photos album screenshot stays blocked (S4-img) |


Round 1 fix evidence: pytest 122 passed (7 new card tests), ruff and mypy clean, `python3 scripts/check.py fridge-door` 0 error 0 warning, dist ZIP rebuilt. New conformance tests: tests/integration/test_dryrun.py (card formats; README samples equal dry-run output).