---
name: fridge-door
description: A weekly parent to-do digest, per-child artwork keepsake folders with albums that keep growing, and an artwork journal per child, built from photos of school notices, permission slips and children's drawings in a phone backup folder on the NAS. Use when a parent says things like "sort out this week's school papers", "what do I need to send back to school", "file the kids' drawings" or "fridge door", asks about a saved digest, for example "when is the field trip fee due?", or asks to make an art journal, for example "make Mina's art journal" or "what did Jun draw this term?".
---

# Goal

Turn the photos a parent takes of school paperwork and children's artwork into these results, without changing, moving or deleting any original photo, except the optional archive step, which moves past notices only when asked:

- One **digest file** per batch: deadlines in date order, upcoming events, a short summary of each notice in the parent's language, the artwork with captions and anything the child said about it, open items carried over from the last digest, and the photos that could not be read.
- One **keepsake folder** per child, `{output_folder}/Artwork - {child}`, holding copies of that child's drawings.
- One **album** per child, `Artwork - {child}`, created once. It follows the keepsake folder, so drawings copied in later weeks appear in it without a new album.
- On request, an **artwork journal** for one child, built only from the artwork lines of the saved digests.

Supported scope: one source folder per run, images only, up to 12 photos per batch. More photos are handled in further batches when the parent says "continue". Each run starts where the last digest stopped. Photos that are neither school paperwork nor artwork (for example receipts or screenshots) are listed once and left untouched. Photos handled on earlier runs are left out automatically. The parent can also ask questions about the most recent saved digest.

For the user guide, read [references/README.md](references/README.md). For the digest layout, read [references/digest-format.md](references/digest-format.md). For dependencies and AI tool disclosures, read [references/disclosures.md](references/disclosures.md). For the device test day and the fallback table, read [references/test-plan.md](references/test-plan.md).

# Required input

Use the user's exact words and do not guess.

1. `{source_folder}`: the NAS folder where the phone backs up photos, written the way the user sees it. A folder that mostly holds school photos is recommended, for example the backup folder of a School album on the phone (Photos/PhoneBackup/School). If the user does not name one, ask once.
2. `{children}`: child names as the parent writes them, or none. Ask how each child signs drawings when it differs (for example Mina signs as 김민아).
3. `{parent_language}`: the language for summaries. Default: the language the user is speaking.
4. `{output_folder}`: where the digest and the keepsake folders go, written the way the user sees it. Default: a subfolder named Fridge Door inside `{source_folder}`.
5. `{period}`: a date range, set after Step 1. Default: from `{next_start}` to `{today}`; if `{next_start}` is later than `{today}`, from `{today}` to `{today}`. When there is no earlier digest, or it gives no start date: the last 7 days including `{today}`. If the default is longer than 31 days, ask the user for a period. Always state explicit dates, for example 2026-11-23 to 2026-11-29.
6. `{archive_past}`: off. Turn it on only when the user explicitly asks to archive past notices in this run.
7. `{copy_language}`: none. Set it only when the user explicitly asks for a copy of the digest in another language.
8. `{today}`: the current date, used for the default period and to flag past due dates.

Collect values 1 to 4 first, then run Step 1. Then read every value back in one sentence, including the period, ask the user in the chat and wait for the answer, for example: "Folder Photos/PhoneBackup, 2026-11-23 to 2026-11-29 (where the last digest stopped), children Mina and Jun, saving to Photos/PhoneBackup/Fridge Door. Shall I go ahead?" If a value is still missing after that, ask for it; never fill it with a guess. Questions about saved digests and the artwork journal need only `{output_folder}`, and the journal also needs `{child}`; do not ask for the other values there.

Values filled during the run, always from real results of earlier steps: `{output_folder_path}`, `{previous_digest_path}`, `{previous_digest}`, `{next_start}`, `{photo_list}`, `{new_photos}`, `{batch}`, `{remaining_count}`, `{photo_path}`, `{ocr_text}`, `{caption}`, `{notice_items}`, `{artwork_items}`, `{unknown_artwork}`, `{child_note}`, `{unrelated_items}`, `{unreadable_items}`, `{failed_items}`, `{notice_summary}`, `{carried_items}`, `{child}`, `{keepsake_folder}` (always `{output_folder}/Artwork - {child}`, the name the user sees), `{child_artwork_paths}`, `{keepsake_folder_path}`, `{keepsake_folder_id}`, `{keepsake_storage_type}`, `{copied_paths}`, `{same_name_items}`, `{album_name}` (always `Artwork - {child}` unless the user picks another name), `{digest_text}`, `{saved_path}`, `{handled_paths}`, `{past_notice_paths}`, `{year-month}`, `{archive_folder}`, `{journal_lines}`, `{journal_text}`.

Before each delegation, replace every value in braces with its real value, and write a single quote inside a value as '"'"'. If a value is missing, do not run the dependent step; say which value is missing.

# Generation-time capability evidence

- `ug-filesystem` → `file-agent`
- `ug-filemgr` → `file-agent`
- `file-workflow` → `file-agent`
- `ug-photo` → `photo-agent`
- `ug-knowledge` → `knowledge-agent`
- `ug-document` → `document-agent`

# Workflow

Run the steps in order. Each step uses only the real result returned by the steps before it (upstream results only). Original photos are only read, except by the optional archive step.

## Step 1: Find and read the most recent digest

`delegate --target file-agent --instruction 'In the folder {output_folder} only, without subfolders, find Markdown files whose name starts with fridge-door-digest and ends with .md. Leave out translated copies, whose name has a language code just before .md (for example .en.md or .ko.md), and leave out files whose name starts with fridge-door-journal. Of the rest, return the full path of the newest one: choose by the timestamp in the file name; if the names carry none, by the time the file was created, never by modification time. Also return the real full NAS path of the folder {output_folder}. Only read; do not create, change, move or delete anything. If the folder does not exist or holds no such file, say clearly which of the two is the case.'`

- The expert says clearly that the folder or the file does not exist: there is no earlier digest and nothing to carry over.
- The result has no file path and does not say that none exists: say you could not check for an earlier digest, carry nothing over and use the 7-day default period.
- Otherwise keep the real path as `{previous_digest_path}`, keep a returned folder path as `{output_folder_path}`, and read the file:

`delegate --target file-agent --instruction 'Read the file at exactly {previous_digest_path} and return its whole content as stored, without summarising or reformatting it. Say whether the content you return is complete or was cut short. Only read; do not change, move or delete the file. If the file cannot be read, say so.'`

From the complete real text `{previous_digest}`, take the date after "Next run starts from:" in the meta line as `{next_start}`. If the content was cut short, carry nothing over, use the 7-day default period and say so. If it has no such date, use the 7-day default period and say so.

## Step 2: List this period's photos

`delegate --target file-agent --instruction 'In the folder {source_folder} and its subfolders up to depth 2, list image files whose modification time falls inside {period}. Leave out everything inside the folder {output_folder}. Return each file with its full path and modification time, oldest first, at most 60 files, and say how many files match in total. Only read; do not create, change, move or delete anything. If no file matches, say clearly that none was found.'`

- The expert says clearly that nothing matched (no results, an empty list): tell the user no photos were found in `{source_folder}` for `{period}`, offer to try another folder or period, and finish with nothing created. Do not search other folders or widen the period on your own.
- More than 60 matching photos: say how many matched, that one run looks at 60, and that a folder holding mostly school photos avoids this. Offer to narrow the list to papers and drawings. Only if the user agrees, ask once:

`delegate --target photo-agent --instruction 'Among the photos in the folder {source_folder} taken or added inside {period}, find only those that look like a paper document with printed or handwritten text, or like a drawing or craft made by hand. Use the recognition results the photo library already has. Leave out photos inside the folder {output_folder}. Return each match with its full file path and date, oldest first, at most 60 photos, and say how many match in total. Only read; do not create or change albums. If the library has not finished recognising these photos or you cannot keep to this folder, say so clearly and return no list.'`

  If it returns real paths, use them. Otherwise tell the user narrowing did not work and continue with the oldest 60 from the listing.
- Only if the listing ends as `failed`, ask photo-agent for the same folder instead, then continue with its real result:

`delegate --target photo-agent --instruction 'List the photos stored in the folder {source_folder} that were taken or added inside {period}. Leave out photos inside the folder {output_folder}. Return each photo with its full file path and date, oldest first, at most 60 photos, and say how many match in total. Only read; do not create or change albums. If no photo matches, say clearly that none was found.'`

  If it returns fewer paths than the total it reports, say so.

Keep the real list as `{photo_list}`. If the result has no file paths, stop and say the listing gave no usable paths.

## Step 3: Leave out photos handled on earlier runs

`delegate --target file-agent --instruction 'Look up the file tag named fridge-door-done. If the tag exists, say which of these files carry it: {photo_list}. If the tag exists but none of these files carry it, say clearly that none of them carry it. If the tag does not exist, say clearly that it does not exist. Only read; do not create, change or remove any tag.'`

- Remove the tagged files; the rest is `{new_photos}`. Tell the user how many were already handled (for example "2 already done"). When the expert says clearly that none carry the tag or that the tag does not exist, every photo is new.
- If this step ends as `failed`, or the answer says none of these things, tell the user that photos handled before may appear again, ask in the chat whether to continue and wait. If the user says no, finish with nothing created.
- If `{new_photos}` is empty and more photos matched than were listed, say so and offer the period from the date of the newest listed photo. Otherwise tell the user there is nothing new in this period. In both cases, if `{previous_digest}` has open items, say how many unticked deadlines and how many upcoming events it holds and name that digest. Finish with nothing created; do not save a new digest.

Take the oldest 12 photos of `{new_photos}` as `{batch}`. The number left over is `{remaining_count}`; say it in the preview and the report. Do not start the next batch on your own. When the user says "continue", take the next 12 photos of `{new_photos}` that were not read in this conversation and run Steps 4 to 15 again for them, using the digest saved by the batch before as `{previous_digest}`; if that batch saved no verified digest, keep the `{previous_digest}` read in Step 1.

## Step 4: Read the text on each photo

For each `{photo_path}` in `{batch}`, one at a time:

`delegate --target photo-agent --instruction 'Read all printed and handwritten text in the image {photo_path}. Return the text exactly as it appears, in reading order, and mark parts you cannot read as unclear. Do not describe the picture, do not add or correct text, and do not change the photo or any album. If the image has no readable text, say clearly that no text was found.'`

Show a one-line progress message before each photo, for example "Reading photos 4/7". Sort each photo by its real result `{ocr_text}`:

- Several lines that read as a school notice, newsletter, permission slip, fee notice or class message: add to `{notice_items}`.
- Little or no text (a few words, a name, a date): candidate artwork, go to Step 5.
- Text that is clearly something else (receipt, screenshot, menu, ticket): add to `{unrelated_items}` and do nothing further with it.
- The step ends as `failed`: go to Step 5. Never guess the content.

## Step 5: Check candidate artwork

`delegate --target photo-agent --instruction 'Look at the image {photo_path} and answer in two parts. First, YES if it shows a drawing, painting or craft made by a child, otherwise NO. Second, one sentence naming the main subject and colours. Do not guess the name or age of the child, and do not change the photo or any album. If you cannot see the image clearly enough to answer, say so.'`

- YES: add to `{artwork_items}` with the real `{caption}`. If the text from Step 4 contains a name from `{children}` (or the way that child signs), assign that child. Otherwise add the photo to `{unknown_artwork}`; the parent chooses the child at the preview.
- NO: add to `{unrelated_items}`. If Step 4 found no readable text but the sentence describes a paper document (a notice, letter or form), add the file name to `{unreadable_items}` instead.
- The expert completes but cannot see the image clearly, or gives no YES or NO: add the file name to `{unreadable_items}`.
- The step ends as `failed`: add the file name to `{failed_items}`. These photos are not tagged, so the next run tries them again.

## Step 6: Structure the notices

Do this yourself from each real `{ocr_text}` in `{notice_items}`; there is no delegation. Build one entry: title, sender (school and class), every date with its role (due, event, payment), the action type (reply slip, item to bring, payment, event), the action the parent must take, the amount if any, the child it concerns (match against `{children}`; otherwise all children) and the source file name. Quote the original date text next to the interpreted date, for example "12월 4일까지" as 2026-12-04. Mark a date or amount as "needs check" when the text is unclear; never invent one. Flag a due date earlier than `{today}` as past.

Write a one-line `{notice_summary}` in `{parent_language}` for each entry. When the notice is in another language, translate only this summary line, and keep dates, amounts and names exactly as written in the notice. Write only what the notice says.

## Step 7: Carry over open items

There is no delegation. From the complete `{previous_digest}`, take each deadline line that is still unticked (`- [ ]`) and each event line dated `{today}` or later, unless the same source file is in this batch. Lines marked `- [x]` are done and past events are dropped. Keep them as `{carried_items}`, marked "carried over from" the previous digest file name. If the parent says at the preview that an item is already done, write it as `- [x]` in the new digest so it is not carried over again.

## Step 8: Preview and agreement

For each child with artwork in this batch, with `{album_name}` set to `Artwork - {child}`, check whether the album already exists:

`delegate --target photo-agent --instruction 'List the photo albums whose name is exactly {album_name}. Return each match with its name, album type, photo count and, if you can see it, the folder it follows. Only read; do not create or change any album. If no album has this name, say clearly that none was found.'`

An album with this name counts as existing. If it seems to follow a folder other than `{keepsake_folder}`, tell the user, ask for a new album name, use it as `{album_name}` and check it again. Show one preview in the chat, written in `{parent_language}`, using only real values and leaving out a line that has nothing to show:

1. Summary strip: "N photos read. Please check before I save anything.", then "N photos found · N already done · N in this batch · N left for later", then the folder and period.
2. Check lines, only when needed: a drawing whose child is unknown (ask which child), or a photo that could not be read.
3. "School notices (N)": one line per notice in date order with file name, title, due or event date, the action with any amount, and the child (or all children). Past due dates carry the prefix "⚠" and the word "past".
4. "Carried over (N)": open items and upcoming events from the last digest with their source file.
5. "Artwork (N)": one line per drawing with file name, child (or "unknown, please tell me") and caption. Then: "If your child said something about a drawing, tell me and I will keep it with the picture (optional)."
6. "Not related / unreadable (N)": file name with a one-word reason (receipt, screenshot, too blurred).
7. What will be created: copies per child into `{keepsake_folder}`, each new album `Artwork - {child}` (or "album exists, new copies will appear in it"), the new digest file in `{output_folder}`, and the fridge-door-done tag on every photo the digest lists. Say that the copies are new files, so the same drawing can show twice in UGREEN Photos.
8. Closing line: "Originals stay where they are; nothing is moved or deleted. Proceed? (yes / or correct, e.g. 'IMG_0107 is Jun's' or 'the fee is already paid')". A one-line correction updates the entry and the preview is shown again.

Ask the user in the chat and wait for the answer. Run the album check for every child who has artwork after the parent's corrections, including children assigned at the preview, and show the preview again. When the parent tells you what a child said about a drawing, keep those words exactly as `{child_note}` for that drawing, in the language the parent used, without correcting them. If the parent does not answer that line, do not ask again. If the user declines, show the digest text in the chat instead and finish with nothing created. If this batch has no notices, no artwork and no carried items, say so and offer to save a short digest that lists the photos, so they are tagged and not read again.

## Step 9: Make sure the output folder exists, then copy the artwork (after the user agrees)

`delegate --target file-agent --instruction 'Check whether the folder {output_folder} exists, and if it does not, create it together with any missing parent folders. In both cases return the real full NAS path of the folder. Do not create, change, move or delete anything else. If the folder cannot be created, say so clearly.'`

Keep the returned path as `{output_folder_path}`; never pass the folder name the user sees. If no real path comes back, copy nothing, create no album and save nothing: show the digest text in the chat and tag nothing. Then, for each `{child}` with artwork, with `{child_artwork_paths}` set to that child's real photo paths:

`delegate --target file-agent --instruction 'Copy these image files into the folder {output_folder_path}/Artwork - {child}, creating the folder if it does not exist: {child_artwork_paths}. Copy only; do not move, rename, change or delete the original files. Never overwrite: if a file with the same name already exists in {output_folder_path}/Artwork - {child}, leave both files as they are and do not copy it. Return the files copied and the files not copied with the reason, or the counts if that is all you have. If nothing was copied, say so clearly.'`

The NAS may ask for approval for creating the output folder, for the copy and, separately, for creating the keepsake folder (`waiting_approval`). After the copy ends as `completed`, read the folder:

`delegate --target file-agent --instruction 'List the files directly inside the folder {output_folder_path}/Artwork - {child}. Return the real full NAS path of the folder, the file id of the folder, the storage type of the folder (for example personal or shared), and the name and full path of each file in it. Only read; do not create, change, move or delete anything. If the folder does not exist, say clearly that it does not exist.'`

Keep the real folder path as `{keepsake_folder_path}`, the folder id as `{keepsake_folder_id}` and the storage type as `{keepsake_storage_type}`. `{copied_paths}` holds the listed paths whose file name matches one of `{child_artwork_paths}`, except names the copy reported as not copied because the same name already existed; those drawings go to `{same_name_items}`. Both count as handled. Do not retry a copy.

## Step 10: Create each child's album once (after the user agrees)

Run the album step only for a child whose check completed and found no album, and who has at least one path in `{copied_paths}`. If the check found the album, create nothing and tell the user the new copies will appear in it after the NAS indexes them. If the check did not complete, create nothing and say so. If `{keepsake_folder_path}`, `{keepsake_folder_id}` or `{keepsake_storage_type}` is missing, do not run this step and say the album was not created because the folder path, id or storage type was not returned.

`delegate --target photo-agent --instruction 'Create one album named {album_name} that automatically includes every photo in the folder {keepsake_folder_path} (folder file id {keepsake_folder_id}, storage type {keepsake_storage_type}), including photos added to this folder later. Use the folder as the only rule; add no date, person or place rule. Do not move, copy or delete any file. If the folder cannot be used as the album rule, create no album and say so clearly. Return the real album identifier and how many photos it shows now.'`

The NAS may ask for approval (`waiting_approval`). The photo count can be lower than the number of copies until indexing finishes; report the real number and say so.

## Step 11: Save the digest (after the user agrees)

Compose `{digest_text}` following [references/digest-format.md](references/digest-format.md): a title, a meta line and seven sections in fixed order, only real results, every item naming its source photo file, and the copy and album results of Steps 9 and 10. In the meta line write "Next run starts from:" with the date of the oldest photo of `{photo_list}` that carries no fridge-door-done tag and that no batch of this conversation tags: photos left for a later batch, photos in `{failed_items}`, and drawings that were not copied or whose child was not chosen, in this batch or an earlier one. If more photos matched than were listed, the date of the newest listed photo also counts. If there is none, write the last day of `{period}`; the tag keeps the photos already handled on that day from being read twice. Save to `{output_folder_path}` from Step 9; if Step 9 returned none, do not save:

`delegate --target knowledge-agent --instruction 'Save the following Markdown text as one new file in the existing folder {output_folder_path}, using the file name hint fridge-door-digest. Do not overwrite or change any existing file. Return the real full path of the saved file and whether the save was verified by reading the file back. Text: {digest_text}'`

The NAS may ask for approval (`waiting_approval`). Use only the path the expert returns as `{saved_path}`; never build a file name yourself. A verified save does not mean the digest is searchable yet, so do not say that it is. If the save does not end as `completed` with a real path, show the digest text in the chat so nothing is lost.

## Step 12: Mark handled photos

The tag means Fridge Door has handled the photo once. When the save of the digest was verified, `{handled_paths}` holds every photo of the batch that the digest lists: notice photos, drawings in `{copied_paths}` or `{same_name_items}`, `{unrelated_items}` and `{unreadable_items}`. When the save was not verified, tag nothing, not even the drawings: copies already in a keepsake folder come back next run as `{same_name_items}` and are recorded in that digest. Photos in `{failed_items}`, drawings that were not copied and drawings whose child was not chosen are never tagged.

`delegate --target file-agent --instruction 'Make sure a file tag named fridge-door-done exists, creating it if it does not, then add the tag to exactly these files: {handled_paths}. Do not remove or change any other tag, and do not change, move or rename the files. Return which files now carry the tag and which could not be tagged.'`

The NAS may ask for approval (`waiting_approval`). If tagging fails, say which photos are untagged. The saved digest already starts the next run after them; if the parent reruns this period explicitly, these photos will be read again.

## Step 13: Archive past notices (optional, off by default)

Run this only when `{archive_past}` is on, and only for notice photos whose due date is past (`{past_notice_paths}`). Show the list and the target folder `{archive_folder}`, which is `{output_folder}/Archive {year-month}`, then ask the user in the chat and wait for a yes:

`delegate --target file-agent --instruction 'Move these files into the folder {archive_folder}, creating the folder if it does not exist: {past_notice_paths}. Do not overwrite any file that already exists there and do not delete anything. Return the real new path of each moved file and the reason for any file not moved.'`

The NAS may ask for approval (`waiting_approval`). This is the only step that moves an original photo; without an explicit request it never runs.

## Step 14: Translated copy of the digest (optional, off by default)

Run this only when `{copy_language}` is set and `{saved_path}` is a verified save:

`delegate --target document-agent --instruction 'Translate the document at exactly {saved_path} into {copy_language} and save the translation as a new copy. Leave the original file unchanged and do not overwrite any file. Keep dates, amounts, names and photo file names exactly as written. Return the real full path of the new copy. If no copy was written, say so clearly.'`

The NAS may ask for approval (`waiting_approval`). If no copy path comes back, say that no translated copy was made.

## Step 15: Report

Completion card, plain text in the chat, in `{parent_language}`, built only from real results:

1. Result line first. Start with "Done." only when every planned step of this batch ended as `completed` and every planned item came back: each drawing copied or already in its folder, each planned album created, the digest saved and verified, and each photo of `{handled_paths}` tagged. Otherwise start with "Partly done.". A photo in `{unreadable_items}` does not by itself make the batch partly done; a photo in `{failed_items}` does. Then the counts: "N deadlines, N events, N artworks."
2. Next due item: the earliest open deadline with its date, task, amount, child and source file name.
3. Created, only what an expert returned as `completed`: copies per child with the real `{keepsake_folder_path}`, each new album with its real identifier and photo count, the digest with its real `{saved_path}`, and "Tagged N photos fridge-door-done" with N from the expert's answer.
4. When the result line is "Partly done.", list separately: steps or photos that failed or were cancelled, steps still waiting, and steps not run because an earlier step did not complete.
5. Status line last: photos already done, left untouched as unrelated, unreadable, or failed; photos left for the next batch; "originals were not moved or deleted" (or what the archive step really moved); "This Skill asked only the NAS experts; the AI model they use is the one the NAS owner set up."

## Questions about saved digests

When the user asks about something already sorted, for example "When is the field trip fee due?" or "What do we still owe the school?", do not read the photos again. Run the two delegations of Step 1 to find and read the most recent digest, then answer only from its real text and name the digest file and the source photo file of each item. If the expert says clearly that no digest exists, say so and offer to sort this week's photos. If the content was cut short, answer only from what was returned and say that it was incomplete. This is read only; nothing is created.

## Artwork journal (only on request)

For requests such as "Make Mina's art journal" or "What did Jun draw this term?". Run the first delegation of Step 1 to get `{output_folder_path}`; if no folder path comes back, say so and stop. Then:

`delegate --target document-agent --instruction 'Read the Markdown documents in the folder {output_folder_path} whose name starts with fridge-door-digest, leaving out translated copies whose name has a language code just before .md. From each, return every line in the Artwork section that names {child}, exactly as written, in date order, each with the file name of the digest it came from. Do not summarise, rewrite or change the language of the lines. Only read; do not create or change any file. Name any document you could not read. Say whether every document was read in full. If no line names {child}, say clearly that none was found.'`

If the expert says a document was not read in full, name it and say its lines may be missing. If this ends as `failed` or the expert says it cannot read these Markdown files, use file-agent instead and say that only the N most recent digests (at most 8) were checked:

`delegate --target file-agent --instruction 'In the folder {output_folder_path} only, find Markdown files whose name starts with fridge-door-digest, leaving out translated copies whose name has a language code just before .md. Return the full paths of the 8 created most recently, newest first. Only read; do not create, change, move or delete anything. If there is no such file, say clearly that none was found.'`

Read each returned path with the read delegation of Step 1, one at a time, and take that child's Artwork lines yourself. Keep only real returned lines as `{journal_lines}`. If there are none, say so and create nothing. Otherwise build `{journal_text}`: the title "Artwork journal - {child}", the first and last date, then one entry per line in date order with date, caption, the child's words if any, source photo file and keepsake folder. Add nothing that is not in `{journal_lines}`. Show it in the chat. Only if the user wants it saved:

`delegate --target knowledge-agent --instruction 'Save the following Markdown text as one new file in the existing folder {output_folder_path}, using the file name hint fridge-door-journal. Do not overwrite or change any existing file. Return the real full path of the saved file and whether the save was verified by reading the file back. Text: {journal_text}'`

The NAS may ask for approval (`waiting_approval`). Report only the real path the expert returns.

# Completion and failure

- `completed`: check that the result holds the paths, identifiers or text the next step needs. If something required is missing, say that the step completed but the value needed next was not returned, and do not run the dependent step. Never say a copy, album or file exists unless the responsible expert returned `completed` with its real path or identifier. A result that is empty and does not say that nothing was found is not proof of no matches.
- `failed`: name the step and the file, with the reason the expert gave. In Steps 4 and 5, continue with the remaining photos and list the failed ones under "Needs your check". If Step 2 and its fallback both fail, stop. If Step 11 fails, show the digest text in the chat.
- `cancelled`: report the step as not done and what was already created. Do not retry it automatically.
- `waiting_user`: Uliya relays the expert's question to the user and resumes the same delegation after the user answers. Do not start a replacement delegation or build a waiting result yourself; check the terminal result that follows.
- `waiting_approval`: tell the user what will change (new copies, a new folder, an album, one new file, a tag, moved photos or a translated copy) and wait. Only the approval given in the NAS approval prompt resumes the delegation; the user's yes at the preview is not that approval. If approval is refused, follow the terminal state the resumed delegation actually returns; in every case treat that item as not created.

Empty and partial results: an empty result from Step 2 or Step 3 ends the run honestly with nothing created. If only some photos could be read, build the digest and the copies from those and list the rest by file name. Partial completion is an assessment, not a state: list completed, failed or cancelled, waiting, and not-run steps separately. Never invent dates, amounts, school names, child names, captions or a child's words; every item in the digest names its source photo file.

Retries: copying, album creation, saving and tagging can repeat their effect. Never retry them automatically. Before a retry the user asks for, check what already exists (copies in `{keepsake_folder}`, an album named `{album_name}`, the newest digest in `{output_folder}`) and explain the risk of duplicates.

Safety: original photos are read only and are moved only by the optional archive step after an explicit request. The other writes are new copies in the keepsake folders, one album per child, one new digest file per batch, the fridge-door-done tag, an optional translated copy and an optional artwork journal, each after the user agrees and the NAS approves. This Skill delegates only to the registered NAS experts named above and calls no outside service. The Skill never runs `cli.invoke` itself. A local static check is not a run on the NAS; report only what the experts returned.
