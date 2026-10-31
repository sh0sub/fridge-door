# Device test plan

The plan for the Round 2 test day on the assigned NAS (iDX6011 Pro, 64 GB). Every run is recorded; failed runs are kept as evidence.

## Test kit

Printed and photographed test material with invented names, schools and phone numbers:

- 8 school notices: 5 in Korean, 3 in English; 1 with a due date that is already past on the test day.
- 6 children's drawings and crafts: 2 with a child's name written on them, 1 deliberately blurred.
- 1 receipt and 1 screenshot (unrelated photos).

Upload the kit into Photos/PhoneBackup in two batches so that one run never holds more than 12 photos: batch A (notices, receipt, screenshot) and batch B (drawings). Check that the modification time of every file falls inside the period used for its run. If both batches end up with the same time, put them in two subfolders (Photos/PhoneBackup/Kit-A and Photos/PhoneBackup/Kit-B) and name the subfolder as the source folder.

## Timebox (Pacific day 00:00 to 23:59 is 17:00 to 17:00 the next day in Korea)

| Korea time | Task |
|---|---|
| 17:00 | Sign in, install the Skill, upload the kit, check modification times |
| 18:00 | Core 1 (notices). On failure, use the fallback table |
| 20:00 | Core 2 (drawings, per-child albums, second run) |
| 22:00 | Edge cases (blurred photo, receipt, declined approval, empty period) |
| 23:00 | Fix wording, run the static check, reinstall, rerun the failed case |
| 01:00 | Record the demo video |
| 03:00 | Retakes and evidence backup (logs, recordings, result files); data cannot be recovered after the test day |

## Core 1: notices become a digest

- [ ] Fridge Door reads back folder, period, children and output folder and waits for a yes.
- [ ] The preview lists six deadlines in date order, one flagged as past, plus two events; each item names its source photo.
- [ ] The receipt and the screenshot are listed as left untouched.
- [ ] After approval: "School notices {year-month}" album holds the 8 notices; one digest file is saved; its real path is reported.
- [ ] The digest has the seven sections of [digest-format.md](digest-format.md) in order.
- [ ] With an English request, summaries appear in English next to the Korean key line.

## Core 2: drawings become per-child albums

- [ ] Five readable drawings are recognised as artwork with a one-sentence caption.
- [ ] Two drawings are assigned from the name read on them; for the others, Fridge Door asks which child.
- [ ] Two "Artwork – {child} {year}" albums are created after approval.
- [ ] A second run over the same periods skips the 13 handled photos (8 notices, 5 readable drawings) as already done and creates nothing; the receipt, screenshot and blurred drawing are listed again because they were never tagged.

## Edge: honest failure

- [ ] The blurred drawing is listed under "Needs your check" by file name; no caption is invented.
- [ ] Declining the album approval leaves the albums out and asks whether to save the digest only.
- [ ] An empty period ends with "no results" and nothing created; no other folder is searched.
- [ ] Nothing is created before the preview is approved.

## Expected results

| Run | Photos in | Expected deadlines | Expected albums | Left untouched | Needs your check |
|---|---|---|---|---|---|
| Core 1 (batch A) | 10 | 6 (1 past) and 2 events | School notices {year-month} (8) | receipt, screenshot | none |
| Core 2 (batch B) | 6 | 0 | Artwork – {child} {year} for each of 2 children (5 in total) | none | blurred drawing |
| Second run | same periods | none | none | none | the 3 unhandled photos are listed again; the 13 handled are skipped |

Fill in the actual numbers next to each row on the test day.

## Fallback table

| Problem on the device | Fallback |
|---|---|
| Step 1 listing by folder fails | Photo-agent lists photos stored in the same folder (Step 1 fallback) |
| Album creation from file paths fails | Album built from the folder and period, after the parent agrees (Step 7 fallback) |
| Name on a drawing not read | Parent chooses the child at the preview |
| People albums not indexed yet | Path-based results only; parent chooses the child |
| Translation fails or is declined | Keep the original summary; the digest says "translation unavailable" |
| Saving the digest fails | Show the digest text in the conversation |
| Tagging fails | Report it; the next run may show those photos again |
