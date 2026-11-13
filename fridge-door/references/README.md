# Fridge Door user guide

Fridge Door reads the photos you take of school notices and of your children's drawings, which already sit in your phone backup folder on the UGREEN NAS. Each week it gives you one digest file with deadlines in date order, copies each child's drawings into a keepsake folder, and keeps one album per child in UGREEN Photos that follows that folder. When you ask, it also turns a child's saved drawings into an artwork journal.

Fridge Door is an independent community Skill made for the UGREEN Hackathon 2026. It is not an official UGREEN product.

## Who it is for

- Parents of kindergarten and primary-school children who photograph paper notices, permission slips, fee notices and artwork.
- Parents who do not read the school's language well: each notice gets a one-line summary in your language, with dates, amounts and names kept as written.
- Families whose phones back up photos to the NAS automatically.

## Install

1. Get the Skill: find "fridge-door" in Skills Hub, or download the fridge-door ZIP.
2. In UGOS, open the Uliya Skills page and add the Skill from Skills Hub, or upload the ZIP. The ZIP holds one folder, fridge-door, with SKILL.md and this references folder.
3. Ask Uliya "What can fridge-door do?" to check that it is active.

The Skill uses the file, photo, knowledge and document experts that come with the NAS. It needs no API key, no download and no outside service.

## Which folder to use

Point Fridge Door at a folder that mostly holds school photos, for example the backup folder of a "School" album on your phone. A whole camera roll works, but one run looks at 60 photos at most. When more than 60 photos match, Fridge Door says so and offers to ask the photo expert for only the photos that look like papers or drawings; this uses the recognition the photo library has already done, so it does not work until indexing has finished. If narrowing does not work, the run takes the oldest 60 and the next run continues from there.

## What it reads and writes

| Kind | What | When |
|---|---|---|
| Reads | The newest digest in the output folder (by the timestamp in its name, or by creation time; never a translated copy or a journal), to find where the last run stopped, to carry over open deadlines and upcoming events, and to answer your questions | Every run, and when you ask a question |
| Reads | Image files in the source folder you name (subfolders up to depth 2) inside the period, except the output folder | Every run |
| Reads | The text in each photo and a short look at drawings, done by the NAS photo expert | Every run |
| Writes | Copies of each child's drawings in "{output folder}/Artwork - {child}". The originals stay where they are | Only after you agree to the preview and the NAS approves |
| Writes | One album per child, "Artwork - {child}", created once. It follows the keepsake folder, so later copies appear in it after the NAS indexes them | First time only, after you agree and the NAS approves |
| Writes | One new digest file per batch in the output folder (default: a Fridge Door folder inside the source folder). The NAS adds a timestamp to the name fridge-door-digest | Only after you agree and the NAS approves |
| Writes | The file tag fridge-door-done on every photo the saved digest lists, including receipts and unreadable photos, so later runs leave it out. Nothing is tagged when the digest could not be saved | Only after you agree and the NAS approves |
| Writes | A translated copy of the digest | Only when you ask for one |
| Writes | An artwork journal, fridge-door-journal, in the output folder | Only when you ask for a journal and then ask to save it |
| Moves | Past notice photos into "{output folder}/Archive {year-month}" | Never, unless you ask for archiving in that run |

Original photos are never renamed, changed or deleted. Because the keepsake folders hold copies, the same drawing can show twice in UGREEN Photos: once in the backup folder and once in the keepsake folder.

Privacy: Fridge Door delegates only to the NAS experts above and calls no outside service. Text recognition and the picture check run in the NAS photo expert. The summaries, the digest and the journal are written by Uliya, so the model they run on is the one the NAS owner set up for Uliya (a local model or a cloud model the owner chose).

## Example requests

- "Fridge Door, sort out this week's school papers."
- "When is the field trip fee due?"
- "Make Mina's art journal."
- "냉장고 문, 이번 주 학교 통신문 정리해 줘."
- "애들 그림 아이별 폴더로 정리해 줘."
- "학교에 아직 낼 거 남은 거 있어?"

## What you see in the chat

Fridge Door first reads back the folder, the period and the children, for example "Folder Photos/PhoneBackup, 2026-11-23 to 2026-11-29, children Mina and Jun, saving to Photos/PhoneBackup/Fridge Door. Shall I go ahead?". The period starts where your last digest stopped; on the first run it is the last 7 days including today. While photos are read, one progress line updates ("Reading photos 4/7"). Then you get the preview card. Nothing is created until you answer yes.

    7 photos read. Please check before I save anything.
    9 photos found · 2 already done · 7 in this batch · 0 left for later
    Photos/PhoneBackup · 2026-11-23 to 2026-11-29
    Check needed · IMG_0107.jpg: I could not tell whose drawing this is. Which child made it?

    School notices (4)
    - IMG_0104.jpg · Field-trip fee · 2026-12-04 · Pay the field-trip fee, KRW 12,000 · Mina
    - IMG_0102.jpg · Museum field trip consent · 2026-12-05 · Sign and return the consent slip · Mina
    - IMG_0103.jpg · PE item to bring · 2026-12-08 · Pack a jump rope for PE · Jun
    - IMG_0105.jpg · School arts festival · 2026-12-11 14:00 · Attend the arts festival (optional) · all children

    Artwork (2)
    - IMG_0106.jpg · Mina · A crayon drawing of a yellow school bus under a rainbow.
    - IMG_0107.jpg · unknown, please tell me · A paper-cup robot craft, silver and red.
    If your child said something about a drawing, tell me and I will keep it with the picture (optional).

    Not related / unreadable (1)
    - IMG_0108.jpg · receipt · left untouched

    Will copy: 1 drawing into Photos/PhoneBackup/Fridge Door/Artwork - Mina (new copies, so a drawing can show twice in UGREEN Photos)
    Will create: album Artwork - Mina, which follows its keepsake folder
    Drawings whose child you tell me are copied into that child's keepsake folder the same way
    Will save: a new digest in Photos/PhoneBackup/Fridge Door · tag the photos it lists fridge-door-done
    Originals stay where they are; nothing is moved or deleted. Proceed? (yes / or correct, e.g. 'IMG_0107 is Jun's' or 'the fee is already paid')

Here the parent answered "IMG_0107 is Mina's" and added what Mina said about her bus drawing; both go into the digest. After you agree and the NAS approves each step, the completion card shows only what was really created, with the identifiers and path the NAS returned. It starts with "Partly done." instead of "Done." when a step or a planned item did not finish, and lists those.

    Done. 3 deadlines, 1 event, 2 artworks.
    Next due: 2026-12-04 · Pay the field-trip fee, KRW 12,000 · Mina · IMG_0104.jpg
    Created:
    - 2 copies in Photos/PhoneBackup/Fridge Door/Artwork - Mina
    - Album 'Artwork - Mina' · 2 photos · id a1f0c2d4-0002
    - Saved digest · Photos/PhoneBackup/Fridge Door/fridge-door-digest_20261129_211405.md
    - Tagged 7 photos fridge-door-done
    2 already done · Left untouched 1 (receipt) · Unreadable 0 · 0 left for later · Originals were not moved or deleted · This Skill asked only the NAS experts; the AI model they use is the one the NAS owner set up

The example uses invented names, a fictional school and a sample file name; the real file name is the one the NAS returns.

## Weekly use

1. Ask once a week; Fridge Door does not run on a schedule by itself.
2. Check the folder, dates and child names it reads back, then answer yes. The dates start from "Next run starts from" in the last digest's first lines: the oldest photo it left for later, or else the last day it covered. Photos already tagged on that day are left out and photos added later that day are read. If that date is more than 31 days ago, Fridge Door asks you for the dates.
3. Look at the preview. Correct a child name, say that an item is already done, tell it what your child said about a drawing, or say no; nothing is created before you agree.
4. One batch holds up to 12 photos. If more are waiting, the preview says how many; say "continue" for the next batch.
5. Open the digest in the output folder and tick a box (`- [x]`) when a task is done. Next week, open deadlines and upcoming events are carried over and ticked ones are not, so the newest digest holds every open item. If the last digest could not be checked or was read only in part, nothing is carried over and the new digest says so under "Needs your check".
6. Drawings land in the child's keepsake folder and appear in that child's album; Fridge Door does not create a second album.
7. Every photo the digest lists carries the fridge-door-done tag afterwards and is left out next time. Only photos the photo expert failed on, and drawings that were not copied, come back. If the digest could not be saved, nothing is tagged and the whole batch comes back; drawings already copied are then listed as already in the folder. If tagging fails, Fridge Door names the untagged photos; ask for the same period again to read them. Remove the tag from a photo in File Manager if you want it read again.
8. If nothing new arrived, Fridge Door saves no new digest and tells you how many unticked deadlines and upcoming events are still in the last one.
9. Ask questions such as "When is the field trip fee due?" at any time. The answer comes from the newest digest and names the digest file and the source photo.
10. Ask "Make Mina's art journal" for a list of Mina's drawings from all saved digests, with dates, captions and her own words. It is shown in the chat and saved only if you ask.

Tips: photograph notices flat and in good light. Blurred photos are listed under "Needs your check" instead of being guessed. If a drawing has your child's name written on it, the child is chosen automatically; tell Fridge Door how each child signs (for example Mina signs as 김민아).

## Remove

1. Delete the Skill from the Uliya Skills page. What it created stays on the NAS until you remove it yourself.
2. Albums: in UGREEN Photos, delete the "Artwork - {child}" albums. Deleting an album does not delete the photos in it.
3. Keepsake folders: in File Manager, delete the "Artwork - {child}" folders inside the output folder if you no longer want the copies. The originals in the backup folder are not affected.
4. Digests: in File Manager, delete the fridge-door-digest files in the output folder, any translated copies and any fridge-door-journal files.
5. Tag: in File Manager, delete the fridge-door-done tag. This removes it from every photo.
6. Archive: if you used archiving, the moved notice photos are in "Archive {year-month}" inside the output folder; move them back or delete them.

## Version history

| Version | Date | Changes |
|---|---|---|
| 1.0.0 | 2026-11-13 | Round 1 submission. Checked against uliya-skill-kit 0.7.7 (catalog structure 2.2.0). Keepsake folders and one album per child that follows its folder (created from the real folder path and id); the notice album is removed. Summaries are written by Uliya. Each run starts where the last digest stopped; every photo the digest lists is tagged once. Batches of 12 with "continue", optional narrowing when more than 60 photos match. Open deadlines and upcoming events carry over. A child's own words kept with a drawing. Questions about saved digests. Artwork journal on request. Optional translated copy of the digest |
| 0.7.0 | 2026-10-27 | First complete package: workflow, digest layout, disclosures, device test plan (checked against uliya-skill-kit 0.7.3) |
