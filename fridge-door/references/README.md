# Fridge Door user guide

Fridge Door reads the photos you take of school notices and of your children's drawings, which already sit in your phone backup folder on the UGREEN NAS. Once a week it gives you one digest file with deadlines in date order and creates per-child artwork albums in UGREEN Photos. All reading (OCR, picture checks, translation) happens on the NAS.

Fridge Door is an independent community Skill made for the UGREEN Hackathon 2026. It is not an official UGREEN product.

## Who it is for

- Parents of kindergarten and primary-school children who photograph paper notices, permission slips, fee notices and artwork.
- Parents who do not read the local language well: summaries can be translated into your language.
- Families whose phones back up photos to the NAS automatically.

## Install

1. Get the Skill: either find "fridge-door" in Skills Hub, or download the fridge-door ZIP.
2. In UGOS, open the Uliya Skills page and add the Skill from Skills Hub, or upload the ZIP. The ZIP holds one folder, fridge-door, with SKILL.md and this references folder.
3. Ask Uliya "What can fridge-door do?" to check that it is active.

## What it reads and writes

| Kind | What | When |
|---|---|---|
| Reads | Image files in the source folder you name (subfolders up to depth 2), inside the period you name | Every run |
| Reads | The most recent Fridge Door digest in the output folder, to carry over open deadlines | Every run |
| Writes | New albums in UGREEN Photos: "School notices {year-month}" and "Artwork – {child} {year}" | Only after you agree to the preview and the NAS approves |
| Writes | One new digest file "Fridge Door – {period}.md" in the output folder (default: a Fridge Door folder inside the source folder) | Only after you agree and the NAS approves |
| Writes | The file tag fridge-door-done on photos that were handled, so the next run leaves them out | Only after you agree and the NAS approves |
| Moves | Past notice photos into "Fridge Door/Archive {year-month}" | Never, unless you explicitly ask for archiving in that run |

Original photos are never renamed or deleted. Nothing is sent outside the NAS.

## Example requests

- "Fridge Door, sort out this week's school papers."
- "What do I need to send back to school this week?"
- "Read the notices from my daughter's school this week and tell me in English what I need to do."
- "냉장고 문, 이번 주 학교 통신문 정리해 줘."
- "애들 그림 아이별 앨범으로 정리해 줘."
- "지난 2주 동안 찍은 가정통신문에서 마감만 뽑아 줘."

## What you see in the chat

While photos are read, one progress line updates ("Reading photos 4/7"). Then you get the preview card. Nothing is created until you answer yes.

    7 photos read. Please check before I save anything.
    9 photos found · 2 already done · 7 to process
    Photos/PhoneBackup · 2026-10-19 to 2026-10-25

    School notices (4)
    - IMG_0104.jpg · Field-trip fee · 2026-10-31 · field-trip fee, KRW 12,000 · Mina
    - IMG_0102.jpg · Museum field trip consent · 2026-11-01 · Sign and return the consent slip · Mina
    - IMG_0103.jpg · PE item to bring · 2026-11-04 · Pack a jump rope for PE · Jun
    - IMG_0105.jpg · School arts festival · 2026-11-07 14:00 · Attend the arts festival (optional) · all children

    Artwork (2)
    - IMG_0107.jpg · Mina · A paper-cup robot craft, silver and red.
    - IMG_0106.jpg · Mina · A crayon drawing of a yellow school bus under a rainbow.

    Not related / unreadable (1)
    - IMG_0108.jpg · receipt · left untouched

    Will create: album School notices 2026-10 (4), album Artwork – Mina 2026 (2)
    Will save: Fridge Door – 2026-10-19 to 2026-10-25.md in Photos/PhoneBackup/Fridge Door · tag handled photos fridge-door-done
    Nothing will be moved or deleted.
    Proceed? (yes / or correct, e.g. 'IMG_4410 is Jun's')

After you agree and the NAS approves each step, the completion card shows only what was really created, with the identifiers and path the NAS returned:

    Done. 3 deadlines, 1 event, 2 artworks.
    Next due: 2026-10-31 · field-trip fee · KRW 12,000 · Mina · IMG_0104.jpg
    Created:
    - Album 'School notices 2026-10' · 4 photos · id a1f0c2d4-0001
    - Album 'Artwork – Mina 2026' · 2 photos · id a1f0c2d4-0002
    - Saved digest · Photos/PhoneBackup/Fridge Door/Fridge Door – 2026-10-19 to 2026-10-25.md
    - Tagged 6 photos fridge-door-done
    Skipped 1 (receipt) · 2 already done · Unreadable 0 · Nothing moved or deleted · All processing stayed on this NAS

## Weekly use

1. Ask once a week; Fridge Door does not run on a schedule by itself.
2. Check the folder, dates and child names it reads back, then answer yes.
3. Look at the preview. Correct a child name or say no if something looks wrong; nothing is created before you agree.
4. Open the digest in the output folder and tick a box (`- [x]`) when a task is done. Next week, open items are carried over and ticked ones are not.
5. Photos already handled carry the fridge-door-done tag and are left out next time. Remove the tag from a photo in File Manager if you want it read again.

Tips: photograph notices flat and in good light. One run handles up to 12 photos; for more, ask for a shorter period. Handwritten notes and blurred photos may be listed under "Needs your check" instead of being guessed. If a drawing has your child's name written on it, the album is chosen automatically; tell Fridge Door how each child signs (for example Mina signs as 김민아).

## Remove

Delete the Skill from the Uliya Skills page. Albums, digest files and tags that were created stay on the NAS; delete the albums in UGREEN Photos, the digest files in File Manager, and the fridge-door-done tag in File Manager if you no longer want them.

## Version history

| Version | Date | Changes |
|---|---|---|
| 0.9.0 | planned for the Round 1 submission (2026-11-14) | Wording review after a user walkthrough |
| 0.7.0 | 2026-10-27 | Complete package: workflow, digest layout, disclosures, device test plan |
