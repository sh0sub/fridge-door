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
| R2-count | 09 / submission | Test-count claims consistent | match | 122 tests stated in proposal.html, devpost.md, checklist.md (pytest 122 passed) |
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
