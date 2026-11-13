# Device test plan

The plan for the Round 2 test day on the assigned NAS (iDX6011 Pro, 64 GB). Every run is recorded; failed runs are kept as evidence. Static checks and dry runs before this day do not count as device results.

## Test kit

16 printed and photographed items with invented names, schools and phone numbers:

- 8 school notices (N01 to N08): 5 in Korean, 3 in English; 1 (N05) with a due date that is already past on the test day. Together they hold 6 deadlines and 2 events.
- 6 children's drawings and crafts (D01 to D06): D01 has Mina's name (김민아) and D02 has Jun's name (이준) written on it; D06 is deliberately blurred.
- 1 receipt (R01) and 1 screenshot (S01).

Upload the kit into a new folder Photos/PhoneBackup/Kit, one file at a time in this order: N01 to N08, R01, S01, D01 to D06. One batch holds 12 photos, oldest first, so the order decides the batches: batch 1 is the 8 notices, R01, S01, D01 and D02; batch 2 (after "continue") is D03 to D06. Uploading can set each file's modification time to the moment it reaches the NAS instead of the day the photo was taken, so expect every modification time on the test day. Before the first run, check in File Manager that the modification times follow the upload order, that no two files share the same time and that all of them fall inside the Core 1 period.

Use the source folder Photos/PhoneBackup/Kit, the default output folder Photos/PhoneBackup/Kit/Fridge Door, children Mina and Jun, and the parent language of the request. Core 1 names the period explicitly as two dates covering the test day and the six days before it. The default period is tested separately: a first run without dates uses the last 7 days including today (SKILL.md, Required input 5), so it also holds files uploaded today; the Kit2 edge run checks this.

## Timebox (Pacific day 00:00 to 23:59 is 17:00 to 17:00 the next day in Korea)

| Korea time | Task |
|---|---|
| 17:00 | Sign in, install the Skill, upload the kit in order, check modification times |
| 18:00 | Core 1: first batch (notices, two named drawings, first albums). On failure, use the fallback table |
| 20:00 | Core 2: "continue" for the second batch (carry-over, existing albums, blurred drawing) |
| 22:00 | Edge: refused approval with the first-run default period, rerun of the same period, empty period, later default period, question about the digest, artwork journal |
| 23:00 | Fix wording, run the local static check, reinstall, rerun the failed case |
| 01:00 | Record the demo video |
| 03:00 | Retakes and evidence backup (logs, recordings, result files); data cannot be recovered after the test day |

## Core 1: first batch

- [ ] Ask in one request with the source folder, children Mina and Jun and the period as two dates, for example "Fridge Door, sort out the school papers in Photos/PhoneBackup/Kit from {test day minus 6 days} to {test day} for Mina and Jun." Fridge Door asks at most for the output folder, apart from how the children sign. When asked how the children sign, answer: Mina signs 김민아, Jun signs 이준. It looks for an earlier digest (none yet), then reads back folder, the named period, children and output folder and waits for a yes.
- [ ] The preview says 16 photos found, 12 in this batch, 4 left for later.
- [ ] The preview lists 6 deadlines in date order (N05 flagged as past) and 2 events; each item names its source photo.
- [ ] R01 and S01 are listed as left untouched.
- [ ] D01 is assigned to Mina and D02 to Jun from the names on them, each with a one-sentence caption. Fridge Door offers once to keep what a child said about a drawing; answer for D01 and check that the words appear unchanged in the digest.
- [ ] The preview says copies are new files and that the same drawing can show twice in UGREEN Photos.
- [ ] After approval: the output folder check returns its real path before anything is copied; one copy each in "Artwork - Mina" and "Artwork - Jun" inside that path; the folder listing returns each folder's real path, file id and storage type; one album per child is created from them and its real identifier is reported. Record whether creating each folder asked for its own approval.
- [ ] One digest file is saved with the seven sections of [digest-format.md](digest-format.md) in the real folder path returned by the folder check of Step 9; its name starts with fridge-door-digest. Its meta line says "Next run starts from:" the date of D03.
- [ ] 12 photos are tagged fridge-door-done (8 notices, R01, S01, D01, D02). The completion card starts with "Done.".
- [ ] Fridge Door does not start the next batch by itself.

## Core 2: "continue"

- [ ] The second batch reads D03 to D06 only.
- [ ] The 6 open deadlines and the 2 upcoming events from the first digest are carried over, each marked "carried over from" that file name.
- [ ] Fridge Door asks which child made D03, D04 and D05; answer Mina, Jun, Jun.
- [ ] D06: record the real result. Either it is listed as unreadable under "Needs your check" by file name, or the picture check answers YES and Fridge Door asks which child made it (answer Mina). In both cases no caption or child is invented.
- [ ] The preview says both albums already exist. No new album is created.
- [ ] D06 unreadable: 3 copies are made and 4 photos are tagged (D03 to D06); after indexing, Mina's album shows 2 photos and Jun's 3. D06 YES: 4 copies and 4 tags; Mina's album shows 3 and Jun's 3.
- [ ] The second digest says "Next run starts from:" the last day of the period (the test day). Over both batches: 16 tagged photos, 2 albums, and 5 copies (D06 unreadable) or 6 copies (D06 YES).

## Edge: honest failure

- [ ] Refused approval and the first-run default period: upload a fresh copy of the kit to Photos/PhoneBackup/Kit2 and run with children Sora and Tae, giving no dates. The read-back period is the last 7 days including today, and the preview says 16 photos found, so the kit uploaded today is inside it. When asked how the children sign, answer: Sora and Tae do not sign their drawings. No name on D01 or D02 matches, so the parent assigns both at the preview: answer D01 Sora, D02 Tae. Fridge Door then checks both albums (none exist yet) and shows the preview again with two new albums planned. Refuse the NAS approval for Tae's copy and record the terminal state the resumed delegation returns. Tae's drawing is not copied or tagged and no album is created for Tae; Sora's copy and album are made; the digest is still saved and says "Next run starts from:" the date of D02; 11 photos are tagged; the card starts with "Partly done." and lists the copy step.
- [ ] Rerun of the same period: run the Core folder again with the Core period named explicitly. All 16 photos are skipped as already done; no new digest is saved; Fridge Door says the last digest still holds 6 unticked deadlines and 2 upcoming events; nothing is created.
- [ ] Empty period: a period with no photos ends with "no results" and nothing created; no other folder is searched.
- [ ] Later default period: a run without dates on the Core folder reads back a period from the "Next run starts from" date of the newest digest (the test day) to today. Photos already tagged on that day are skipped; a photo uploaded after Core 2 is read.
- [ ] Question: "When is the field trip fee due?" is answered from the newest digest, naming the digest file and the source photo, without reading photos again and without asking for the source folder.
- [ ] Artwork journal: "Make Mina's art journal" lists Mina's artwork lines from both digests exactly as written, in date order, with the child's words from Core 1. Record whether the document expert read the Markdown digests in full or the file-agent fallback was used, and how many digests it checked. Save it only after asking; the real path starts with fridge-door-journal.
- [ ] Nothing is created before the preview is approved.

## Expected results

| Run | Photos read | Deadlines and events | Copies | Albums created | Tagged | Left untouched or unreadable |
|---|---|---|---|---|---|---|
| Core 1 (batch 1) | 12 | 6 deadlines (1 past), 2 events | 2 (Mina 1, Jun 1) | 2 | 12 | R01, S01 left untouched |
| Core 2 (batch 2), D06 unreadable | 4 | 6 deadlines and 2 events carried over, 0 new | 3 (Mina 1, Jun 2) | 0 | 4 | D06 unreadable (tagged) |
| Core 2 (batch 2), D06 answered YES | 4 | 6 deadlines and 2 events carried over, 0 new | 4 (Mina 2, Jun 2) | 0 | 4 | none |
| Edge, refused approval (Sora, Tae) | 12 | as Core 1 | 1 (Sora) | 1 (Sora) | 11 | R01, S01 left untouched; D02 not copied |
| Edge, rerun same period | 0 | none (6 unticked deadlines and 2 upcoming events reported from the last digest) | 0 | 0 | 0 | 16 skipped as already done |

Fill in the actual numbers next to each row on the test day.

## Assumptions not yet checked on a device

The catalog shows that each capability exists, not how the experts behave. These points can only be checked on the NAS:

1. The file expert can filter by modification time inside a period, keep to depth 2, leave out the output folder, return oldest first, and report the total count.
2. The file expert can pick the newest digest by the timestamp in its file name (by creation time when the names carry none), leave out translated copies and journal files, and return the real full path of the output folder.
3. The photo expert accepts a full path that came from the file listing (the catalog describes paths the user gives in the message).
4. The photo expert's fallback listing returns real file paths; the catalog's photo search shows a preview of the first 20 results.
5. The photo expert can narrow a folder and period to papers and drawings from the library's existing recognition results, and says so when indexing has not finished (the catalog's structured photo search takes a folder and dates but matches recognised objects or text, not "paper or drawing" as such).
6. The tag look-up by name works when the tag does not exist yet or no listed file carries it, and the expert says which case it is.
7. The batch copy keeps existing files and reports a name conflict instead of overwriting or renaming; whether it names files or only gives counts, and whether creating the keepsake folder asks for its own approval.
8. The keepsake folder listing returns the real full path, the file id and the storage type (personal or shared) of the folder.
9. The folder path and file id can be the rule of an album, the album includes photos copied into the folder later, and how long indexing takes.
10. The album list can be narrowed to an exact name and shows the album type and the folder it follows.
11. The folder check returns the real full path, the save Action accepts it, and the saved file name still starts with fridge-door-digest after the NAS cleans the hint and adds a timestamp.
12. Reading the digest by its path returns the whole file and says when it was cut short.
13. Which steps ask for approval, how a refusal is shown, and which terminal state follows it.
14. The translated copy can be made from a Markdown digest, where the copy is saved, what it is named, and whether its name ends with a language code before .md (otherwise Step 1 could take it for a digest).
15. The document expert can read the Markdown digests of a folder and return the artwork lines of one child exactly as written, with their file names.
16. A tag stays on a photo after the optional archive moves it.
17. The photo expert's date filter (fallback listing and narrowing) applies the period even when the request names no year, and how it expects a folder to be given as the scope (the catalog writes a path scope as storage-type:folder-id:path).
18. A condition album needs the storage type of its folder (the catalog's path scope starts with it), and the photo expert accepts the storage type passed on from the keepsake folder listing.
19. The listing's limit of 60 files is applied after the output folder is left out, so copies in the keepsake folders inside the source folder do not take places in the list.

## Fallback table

| Problem on the device | Decision |
|---|---|
| Listing by folder fails | Photo expert lists photos in the same folder (Step 2 fallback) |
| Listing returns no usable paths | Stop. Retry with the kit subfolder only; record the answer |
| More than 60 photos and narrowing does not work | Continue with the oldest 60; the next run starts from the newest listed date. Recommend a folder that holds mostly school photos |
| Photo expert does not accept paths from the listing | Record it. Retest with one photo path written in the request; if that works, note that the parent must name photos |
| No clear answer whether an earlier digest exists, or it was read incompletely | Carry nothing over, use the 7-day default period and say so in "Needs your check" |
| Tag look-up fails | Ask the parent whether to continue; photos handled before may appear again |
| Copy fails or is refused | No album for that child. The digest lists the drawings with "not copied"; they are not tagged and come back next run |
| The copy reports only counts | Use the keepsake folder listing; names found there count as copied |
| Folder listing gives no path, no file id or no storage type | No album this week; the digest says why. The copies stay in the folder |
| The folder cannot be used as an album rule | No album this week; the copies stay in the folder. SKILL.md has no regular-album step, so that day change SKILL.md to create a regular album instead, run the local static check again, reinstall and rerun |
| Album exists but new copies do not show | Wait for indexing and check the keepsake folder; do not create a second album |
| Album with the same name follows another folder | Ask the parent for a new album name |
| Output folder cannot be created | Nothing is copied, saved or tagged; the digest text is shown in the chat. Ask the parent for an existing folder and run the batch again |
| Saving the digest fails | Show the digest text in the chat; tag nothing. Copies already made come back next run as same-name items and are recorded in that digest |
| Tagging fails | Report which photos are untagged. The saved digest already starts the next run after them; rerun this period explicitly to read them again |
| Name on a drawing not read | Parent chooses the child at the preview |
| Translated copy fails | Report that no copy was made; the original digest stays |
| Document expert cannot read the Markdown digests for the journal | File expert finds the most recent digests (at most 8) and reads them one at a time; say how many were checked |
| Saving the journal fails | Keep the journal text in the chat |
