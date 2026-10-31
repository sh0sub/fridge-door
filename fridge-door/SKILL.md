---
name: fridge-door
description: A weekly parent to-do digest and per-child artwork albums built from the school notices, newsletters, permission slips and children's drawings that sit as photos in a phone backup folder on the NAS, read entirely on the device. Use when a parent says things like "sort out this week's school papers", "what do I need to send back to school", "file the kids' drawings", or "fridge door".
---

# Goal

Turn the photos a parent takes of school paperwork and children's artwork into two results, without moving or deleting any original photo:

- One **digest file** for the chosen period: deadlines in date order, events, a short summary of each notice (translated into the parent's language when it differs), captions for the artwork, and a list of photos that could not be read.
- **Albums** in UGREEN Photos: one "School notices {year-month}" album and one "Artwork – {child} {year}" album per child.

Supported scope: one source folder per run, up to 12 photos per run, images only. Photos that are neither school paperwork nor artwork (for example receipts or screenshots) are listed and left untouched. On later runs, photos already handled are left out automatically.

For the user guide, read [references/README.md](references/README.md). For the digest layout, read [references/digest-format.md](references/digest-format.md). For dependencies and AI tool disclosures, read [references/disclosures.md](references/disclosures.md). For the device test checklist and the fallback table, read [references/test-plan.md](references/test-plan.md).

# Required input

Collect these values before the first delegation. Use the user's exact words; do not guess.

1. `{source_folder}`: the NAS folder where the phone backs up photos, written the way the user sees it (for example Photos/PhoneBackup). If the user does not name one, ask once (`waiting_user`).
2. `{period}`: a date range. Default: the last 7 days, stated back as explicit dates (for example 10/19 to 10/25).
3. `{children}`: child names as the parent writes them, in any language, or none. Ask how each child signs drawings when it differs (for example Mina signs as 김민아).
4. `{parent_language}`: the language for summaries. Default: the language the user is speaking.
5. `{output_folder}`: where the digest is saved. Default: a subfolder named Fridge Door inside `{source_folder}`.
6. `{archive_past}`: off. Turn it on only when the user explicitly asks to archive past notices in this run.
7. `{today}`: the current date, used to flag past due dates.

Before the first delegation, read the values back in one sentence and wait for a yes (`waiting_user`), for example: "Folder Photos/PhoneBackup, last 7 days (10/19 to 10/25), children Mina and Jun, saving to Photos/PhoneBackup/Fridge Door. Shall I go ahead?" If a value is still missing after that, ask for it; never fill it with a guess.

Values filled during the run, always from real results of earlier steps: `{photo_list}`, `{new_photos}`, `{photo_path}`, `{ocr_text}`, `{caption}`, `{notice_items}`, `{artwork_items}`, `{unknown_artwork}`, `{unrelated_items}`, `{unreadable_items}`, `{notice_summary}`, `{translated_summary}`, `{previous_digest}`, `{carried_items}`, `{digest_text}`, `{album_name}`, `{album_paths}`, `{year-month}`, `{child}`, `{year}`, `{saved_path}`, `{handled_paths}`, `{past_notice_paths}`, `{archive_folder}`.

Before each delegation, replace every value in braces with its real value and write a single quote inside a value as '\''. If a value is missing, stop the dependent step and say which value is missing.

# Generation-time capability evidence

- `ug-filesystem` → `file-agent`
- `ug-filemgr` → `file-agent`
- `ug-photo` → `photo-agent`
- `ug-document` → `document-agent`
- `ug-knowledge` → `knowledge-agent`

# Workflow

Run the steps in order. Each step uses only the real result returned by the steps before it (upstream results only). Original photos are only read.

## Step 1: List this period's photos

`delegate --target file-agent --instruction 'In the folder {source_folder} and its subfolders up to depth 2, list image files whose modification time falls inside {period}. Return each file with its full path, size and modification time, newest first, at most 12 files, and say how many files match in total. Only read; do not create, move, rename or delete anything. If nothing matches, say so and return an empty list.'`

- Empty list (no results): tell the user no photos were found in `{source_folder}` for `{period}`, ask for another folder or period, and finish as `completed` with nothing created. Do not search other folders or widen the period on your own.
- More than 12 matching photos: say how many matched and ask the user to narrow `{period}` (`waiting_user`). Do not pick a subset on your own.
- Only if this step ends as `failed`, ask photo-agent for the same folder instead, then continue with its real result:

`delegate --target photo-agent --instruction 'List the photos stored in the folder {source_folder} that were taken or added inside {period}. Return each photo with its full path and date, newest first, at most 12 photos, and say how many match in total. Only read; do not create or change albums. If nothing matches, return an empty list.'`

Keep the real list as `{photo_list}`.

## Step 2: Leave out photos handled on earlier runs

`delegate --target file-agent --instruction 'Look up the file tag named fridge-door-done. If it exists, return which of the following files carry it: {photo_list}. If the tag does not exist, say so and return an empty list. Only read; do not create or change tags.'`

- Remove the tagged files; the rest is `{new_photos}`. Tell the user how many were already handled (for example "2 already done").
- If `{new_photos}` is empty, tell the user there is nothing new in this period and finish as `completed` with nothing created.
- If this step ends as `failed`, say so and continue with all of `{photo_list}`; photos handled before may appear again.

## Step 3: Read the text on each photo

For each `{photo_path}` in `{new_photos}`, one at a time:

`delegate --target photo-agent --instruction 'Run OCR on the image {photo_path} and return the recognised text exactly as read, in reading order, with unclear parts marked. Do not describe the picture, do not add text that is not in the image, and do not change the photo or any album. If no text is recognised, return an empty result and say so.'`

Sort each photo by its real OCR result `{ocr_text}`:

- Several lines that read as a school notice, newsletter, permission slip, fee notice or class message: add to `{notice_items}`.
- Little or no text (a few words, a name, a date): candidate artwork, go to Step 4.
- Text that is clearly something else (receipt, screenshot, menu, ticket): add to `{unrelated_items}` and do nothing further with it.
- OCR `failed`: try Step 4; if that also gives no usable answer, add the file name to `{unreadable_items}`. Never guess the content.

## Step 4: Check candidate artwork

`delegate --target photo-agent --instruction 'Look at the image {photo_path} and answer in two parts. First, YES if it shows a drawing, painting or craft made by a child, otherwise NO. Second, one sentence naming the main subject and colours. Do not guess the name or age of the child. Do not change the photo or any album.'`

- YES: add to `{artwork_items}` with the real `{caption}`. If the OCR text from Step 3 contains a name from `{children}` (or the way that child signs), assign that child. Otherwise add the photo to `{unknown_artwork}`; the parent chooses the child at the preview (`waiting_user`).
- NO: add to `{unrelated_items}`.
- `failed` or no usable answer: add the file name to `{unreadable_items}`.

## Step 5: Structure the notices

From each `{ocr_text}` in `{notice_items}`, build one entry: title, sender (school and class), every date with its role (due, event, payment), the action type (reply slip, item to bring, payment, event), the action the parent must take, the amount if any, the child it concerns (match against `{children}`; otherwise all children) and the source file name. Quote the original date text next to the interpreted date, for example "11월 1일(금)까지" as 2026-11-01. Mark a date or amount as "needs check" when the text is unclear; never invent one. Flag a due date earlier than `{today}` as past. Write a one-line `{notice_summary}` for each entry.

When a notice text is longer than about 400 words, condense it first:

`delegate --target document-agent --instruction 'Condense this school notice for a parent. Keep every date, deadline, amount, place, item to bring and action required, word for word. Remove greetings and boilerplate. Return plain text in the result and do not save any file. Text: {ocr_text}'`

### Translation

If `{parent_language}` differs from the language of a notice, translate only its short summary, never the full text:

`delegate --target document-agent --instruction 'Translate the following school notice summary into {parent_language}. Keep dates, amounts and names unchanged. Return the translation as text in the result and do not save any file. Text: {notice_summary}'`

Keep the real translation as `{translated_summary}` and show each notice as: original key line, translated summary, due date, action. The NAS may ask for approval (`waiting_approval`); wait for it. If translation fails or is declined, keep the original summary and say so in the digest.

### Child fallback

Only when `{unknown_artwork}` is not empty and `{children}` was given, check the named people albums once:

`delegate --target photo-agent --instruction 'Among the people albums that have a name, find the ones named {children}. For each match, say which of these photos are among the pictures of that person: {unknown_artwork}. Only read; do not create, rename or change any album. If no named people album matches, or face indexing is not finished, say so and return an empty result.'`

Use only real matches. If the result is empty, ask the parent at the preview which child each drawing belongs to (`waiting_user`). The path-based results from Steps 1 to 4 stay the main source; this check only fills gaps.

### Carry over open items

Only when an earlier digest may exist in `{output_folder}`:

`delegate --target file-agent --instruction 'In the folder {output_folder}, find files whose name starts with Fridge Door and ends with .md, pick the most recently modified one, and return its full text exactly as stored. Only read; do not change, move or delete anything. If there is no such file, return an empty result.'`

From the real text `{previous_digest}`, take each deadline line that is still open (`- [ ]`) and not already found in this run; lines marked `- [x]` count as done. Keep them as `{carried_items}` and list them under Deadlines marked "carried over" with their original source file. An empty result means there is nothing to carry over.

## Step 6: Preview and agreement

For each planned album, with `{album_name}` set to "School notices {year-month}" or "Artwork – {child} {year}", look for an album with the same name:

`delegate --target photo-agent --instruction 'List the albums whose name contains {album_name}. Return each album name and its photo count. Only read; do not create or change albums. If there is none, return an empty list.'`

Show one preview: deadlines in date order (past ones flagged), events, notice summaries with translations, artwork with captions and the assigned child, carried-over items, unrelated photos that will be left alone, unreadable photos, and exactly what will be created: album names with photo counts, the digest file name inside `{output_folder}`, and the fridge-door-done tag. If an album with the same name exists, ask whether to add the photos to it. State that nothing will be moved or deleted.

Preview format (plain text in the chat, written in `{parent_language}`; use the real values from earlier steps and leave a line out when it has nothing to show):

1. Summary strip, first line: "N photos found · N already done · N to process", then the folder and period.
2. Warning line, only when OCR confidence was low for a photo: name the file and what could not be read, and ask which child it belongs to.
3. Group "School notices (N)": one line per notice in date order with file name, title, due date or event date and time, the action (pay, return, bring, attend) with any amount, and the child (or all children). Past due dates are flagged.
4. Group "Artwork (N)": one line per drawing with file name, the child (or "unknown, please tell me") and the caption.
5. Group "Not related / unreadable (N)": file name with a one-word reason (receipt, screenshot, too blurred).
6. What will be created: album names with photo counts, the digest file name in `{output_folder}`, and the tag.
7. Closing line: "Nothing will be moved or deleted. Proceed? (yes / or correct, e.g. 'IMG_4410 is Jun's')". A one-line text correction updates the entry and the preview is shown again.

Ask the user to approve or correct; this is a `waiting_user` point. If the user declines, show the digest text in the conversation instead and finish as `cancelled` with nothing created.

## Step 7: Create albums (after the user agrees)

For each album, with `{album_paths}` set to its real photo paths:

`delegate --target photo-agent --instruction 'Create an album named {album_name} containing exactly these photos: {album_paths}. If an album with this name already exists and the user agreed to add to it, add the photos to it instead of creating a second one, and say which happened. Do not move, copy or delete any file. Return the real album identifier and the number of photos it now holds.'`

The NAS may ask the user to approve (`waiting_approval`); wait for it. If approval is denied, that album counts as `cancelled`: tell the user and ask whether to continue with saving the digest only (`waiting_user`).

If adding photos by path is not supported and the step ends as `failed`, explain that the fallback album holds every photo of `{period}` in `{source_folder}`, ask first (`waiting_user`), and only then:

`delegate --target photo-agent --instruction 'Create an album named {album_name} from the photos in the folder {source_folder} taken or added inside {period}. Do not move, copy or delete any file. Return the real album identifier and the number of photos it holds.'`

## Step 8: Save the digest (after the user agrees)

Compose `{digest_text}` following [references/digest-format.md](references/digest-format.md): seven sections in fixed order, only real results, and every item naming its source photo file. Save it:

`delegate --target knowledge-agent --instruction 'Save the following Markdown text as a new file in the folder {output_folder}, creating the folder if it does not exist, using the file name hint Fridge Door – {period}. Do not overwrite an existing file; if the name is taken, add a number. Return the real saved path and whether the save was verified. Text: {digest_text}'`

Wait for approval if asked (`waiting_approval`). Report `{saved_path}` only after the expert returns `completed`. If saving fails, show the digest text in the conversation so nothing is lost.

## Step 9: Mark handled photos

`{handled_paths}` holds only photos in an album that ended `completed` or cited in a digest saved as `completed`. Unrelated, unreadable and failed photos are never tagged.

`delegate --target file-agent --instruction 'Make sure a file tag named fridge-door-done exists, creating it if needed, then add the tag to these files: {handled_paths}. Do not remove any other tag and do not change the files. Return which files were tagged.'`

Wait for approval if asked (`waiting_approval`). If tagging fails, say so; the run is still complete, but the next run may show these photos again.

## Step 10: Archive past notices (optional, off by default)

Run this step only when `{archive_past}` is on, and only for notice photos whose due date is past (`{past_notice_paths}`). Show the list and the target folder `{archive_folder}`, which is `{source_folder}/Fridge Door/Archive {year-month}`, and wait for a yes (`waiting_user`):

`delegate --target file-agent --instruction 'Create the folder {archive_folder} if it does not exist, then move these files into it: {past_notice_paths}. Do not overwrite files that already exist there and do not delete anything. Return the real new path of each moved file.'`

Wait for approval (`waiting_approval`). This is the only step that moves an original photo; without an explicit request it never runs.

## Step 11: Report

Report only real results: the next due item, counts of deadlines (past ones separately), events and artwork per child, each album with its real identifier and photo count, the saved digest path, photos left untouched as unrelated, photos already handled, and photos that could not be read. Example: "3 deadlines (earliest: field-trip fee, 10/31), 1 event, 2 artworks (Mina). Albums: School notices 2026-10 (4), Artwork – Mina 2026 (2). Digest saved to {saved_path}. 1 receipt was left untouched."

Completion card (plain text in the chat, in `{parent_language}`):

1. Result line first: "Done. N deadlines, N events, N artworks." Counts come from the real results.
2. Next due item, highlighted: the earliest open deadline with its date, task, amount, child and source file name.
3. Created items, only what an expert returned as `completed`: each album with its real identifier and photo count, and the digest with its real `{saved_path}`. Never write an identifier or path that was not returned. For an album or file that was denied or failed, say it was not created and why.
4. Status line, last: photos skipped as already done or unrelated, photos that could not be read, "nothing was moved or deleted", "everything stayed on this NAS".

# Completion and failure

- `completed`: use the real result in the next step. Never say an album exists or a file was saved unless the responsible expert returned `completed` with a real identifier or path.
- `failed`: name the step and the file, with the reason the expert gave. In Steps 3 to 5, continue with the remaining photos and list the failed ones under "Needs your check". If Step 1 and its fallback both fail, stop. If Step 8 fails, show the digest text in the conversation.
- `cancelled`: stop the workflow, report what was already created, and state that nothing more will be created.
- `waiting_user`: show the question to the user exactly, wait for the answer, then resume the same step.
- `waiting_approval`: tell the user what will change (an album, one new file, a tag, or moved photos) and resume only after the NAS reports approval. Denied approval counts as `cancelled` for that item only.

Empty and partial results: an empty list from Step 1 or Step 2 ends the run honestly with nothing created. If only some photos could be read, build the albums and the digest from those and list the rest by file name. Never invent dates, amounts, school names, child names or captions; every item in the digest names its source photo file.

Safety: original photos are read only and never renamed or deleted, and they are moved only by the optional archive step after an explicit request. The only other writes are new albums, one new digest file in the agreed `{output_folder}`, and the fridge-door-done tag, each after the user agrees and the NAS approves. No data leaves the NAS. The Skill never runs `cli.invoke` itself; all NAS work goes through the delegate commands above.
