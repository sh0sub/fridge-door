# Digest format

The digest is one Markdown file per batch, saved in the agreed output folder. The NAS names the file from the hint fridge-door-digest and adds a timestamp; use only the path the NAS returns. The file always has the title line, a meta line and the same seven sections in the same order, even when a section is empty. Write it in the parent language. Use only real results from the run; every item names its source photo file.

## Fixed layout

```
# Fridge Door – {period}
Source: {source_folder} · {N} photos read · Generated on NAS {date time} · Next run starts from: {YYYY-MM-DD}

## At a glance
## Deadlines
## Events
## Notices
## Artwork
## Needs your check
## Left untouched and run details
```

## Section rules

0. **Meta line**, directly under the title: `Source: {source_folder} · {N} photos read · Generated on NAS {YYYY-MM-DD HH:MM} · Next run starts from: {YYYY-MM-DD}`. N is the number of photos read in this batch; use `{today}` alone when the NAS time is not known.
   - "Next run starts from" is the date of the oldest listed photo that no batch of this run tags: a photo left for a later batch, a photo whose expert call failed, or a drawing that was not copied or whose child was not chosen, in this batch or an earlier one. When more photos matched than were listed, the date of the newest listed photo also counts. When nothing stays untagged, it is the last day of the period; the tag keeps the photos already handled on that day from being read twice, and a photo added later that day is read next time.
   - The next run uses this date as the start of its default period, up to today (at most 31 days; otherwise Fridge Door asks for a period; a date later than today gives today alone). Without an earlier digest the default is the last 7 days including today.
   - Fridge Door finds the earlier digest by the timestamp in its file name, or by creation time when the name has none, so ticking a box in an older digest does not change which one it reads. Translated copies (a language code before .md, for example .en.md) and artwork journals are never read as digests.

1. **At a glance**: the next open due item with its date and source file; counts of open deadlines (past ones and carried-over ones in brackets), events (carried-over ones in brackets) and artworks per child; how many photos were left untouched, already handled on earlier runs and left for the next batch; each keepsake folder with the number of copies made; each album with its real state (created, already existed, or not created and why).
2. **Deadlines**: one checkbox line per due item, earliest first: `- [ ] {date} — {action} · {child} · "{quoted date text}" · {source file}`. Put the warning prefix `⚠` before the date when the due date is before the run date: `- [ ] ⚠ {date} — ...`.
   - Items taken from the previous digest end with ` · carried over from {previous digest file name}`. Only unticked lines (`- [ ]`) are carried over, and only when the previous digest was read completely.
   - An item the parent called done at the preview is written as `- [x]`, so the next run does not carry it over. The parent ticks a box (`- [x]`) in the file when a task is done; the next run treats ticked lines as done.
   - Because open items are carried forward, the newest digest holds every open item, unless the carry-over could not be checked or the previous digest was read incompletely; "Needs your check" then says so.
3. **Events**: one line per event with date and time, what it is, who it concerns, the quoted date text and the source file: `- {date time} — {what} · {child} · "{quoted date text}" · {source file}`. No checkbox. Events dated on or after the run date are carried over to the next digest with ` · carried over from {previous digest file name}`; past events are not.
4. **Notices**: a table with one row per notice: source file, original key line (quoted as read), a one-line summary in the parent language written by Uliya, due date, action type. A summary of a notice in another language keeps dates, amounts and names exactly as written in the notice, and says only what the notice says.
5. **Artwork**: one subheading per child. Under it, one line with the keepsake folder and the album state, then one line per photo:
   `- {source file} · {child} · {photo date} · {caption} · Said: "{child_note}" · {how the child was assigned} · {copy state}`.
   - The caption is the real answer of the picture check. `Said: "..."` is there only when the parent told you what the child said about the drawing, in the parent's own words and language, unchanged; otherwise leave that part out.
   - How the child was assigned: `name read on the drawing: {name}` or `chosen by the parent`.
   - Copy state: `copied` (the file is in the keepsake folder listing), `already in the folder (same name), not copied`, or `not copied` with the reason the expert gave.
   - Artwork without a child goes under "Child not chosen" and is not copied or tagged.
   - The artwork journal is built from these lines, so keep them on one line each and in this order.
6. **Needs your check**: photos that could not be read, photos whose expert call failed (they are read again next run), dates or amounts marked "needs check", drawings whose child is unclear, and a carry-over that could not be checked or was read incompletely, each with the file name and the reason. Write "Nothing to check this time." when empty.
7. **Left untouched and run details**: unrelated photos (with a one-word reason such as receipt or screenshot), photos already handled on earlier runs, the number of photos left for the next batch, the run status line, and the line "Originals were not moved or deleted." When the parent asked for the optional archive in this run, write instead which past notice photos will be moved after approval and their new folder; the archive runs after the digest is saved, so the chat report states what was actually moved.

After a verified save, every photo the digest lists (notices, drawings in a keepsake folder, unrelated and unreadable photos) gets the fridge-door-done tag, so later runs leave it out. Without a verified save nothing is tagged; copies already in a keepsake folder come back next run as "already in the folder (same name)". If tagging fails, the chat names the untagged photos: the saved digest already starts the next run after them, and a rerun of the same period reads them again.

## Run status line

The digest is saved before tagging and the optional steps run, so it cannot hold the final verdict; the completion card in the chat does ("Done." or "Partly done."). The digest records the state of the steps that ran before saving:

- `- Run status when saved: every step before saving completed.` when the carry-over check, every copy and folder listing, every planned album and the folder check ended as completed and every photo was read.
- Otherwise `- Run status when saved: Partly done before saving: {step} ({state}); ...` naming each step that failed, was cancelled, returned no usable value, or did not run because an earlier step did not complete. Never describe such a step as done anywhere in the digest.

Never invent dates, amounts, school names, child names, captions, a child's words or file paths. A value that cannot be read is written as "needs check", not guessed.

## Example

This example is the output of the repository dry run for one batch. It uses invented names, a fictional school and a sample file name. Parent language: English. The parent chose the child for IMG_0107.jpg at the preview and told Fridge Door what Mina said about her bus drawing.

```
# Fridge Door – 2026-11-23 to 2026-11-29
Source: Photos/PhoneBackup · 7 photos read · Generated on NAS 2026-11-29 21:14 · Next run starts from: 2026-11-29

## At a glance
- Next due: 2026-12-04 — Pay the field-trip fee, KRW 12,000 · Mina · "12월 4일까지 납부" · IMG_0104.jpg
- 3 deadlines (0 past), 1 event, 2 artworks (Mina 2)
- 1 photo left untouched, 2 already handled on earlier runs, 0 left for the next batch
- Keepsake folders: Artwork - Mina (2 copied)
- Albums: Artwork - Mina (created)

## Deadlines
- [ ] 2026-12-04 — Pay the field-trip fee, KRW 12,000 · Mina · "12월 4일까지 납부" · IMG_0104.jpg
- [ ] 2026-12-05 — Sign and return the consent slip · Mina · "12월 5일까지 회신" · IMG_0102.jpg
- [ ] 2026-12-08 — Pack a jump rope for PE · Jun · "12월 8일 체육 시간 준비물: 줄넘기" · IMG_0103.jpg

## Events
- 2026-12-11 14:00 — School arts festival · all children · "12월 11일 오후 2시 학예회" · IMG_0105.jpg

## Notices
| Source | Original key line | Summary | Due | Action |
|---|---|---|---|---|
| IMG_0102.jpg | 현장체험학습 참가 동의서를 12월 5일까지 회신해 주세요. | Museum field trip: return the signed consent slip by 12월 5일. | 2026-12-05 | Reply slip |
| IMG_0103.jpg | 12월 8일 체육 시간 준비물: 줄넘기 | Bring a jump rope to PE on 12월 8일. | 2026-12-08 | Item to bring |
| IMG_0104.jpg | 현장체험학습비 12,000원을 12월 4일까지 납부해 주세요. | Field-trip fee 12,000원, due by 12월 4일. | 2026-12-04 | Payment |
| IMG_0105.jpg | 12월 11일 오후 2시 강당에서 학예회를 엽니다. | Arts festival in the school hall, 12월 11일 2 pm. | 2026-12-11 14:00 | Event |

## Artwork
### Mina
Keepsake folder: Photos/PhoneBackup/Fridge Door/Artwork - Mina · album Artwork - Mina: created
- IMG_0106.jpg · Mina · 2026-11-28 · A crayon drawing of a yellow school bus under a rainbow. · Said: "This is our school bus. It goes to the rainbow!" · name read on the drawing: 김민아 · copied
- IMG_0107.jpg · Mina · 2026-11-28 · A paper-cup robot craft, silver and red. · chosen by the parent · copied

## Needs your check
Nothing to check this time.

## Left untouched and run details
- Left untouched: IMG_0108.jpg (receipt)
- Already handled on earlier runs: IMG_0100.jpg, IMG_0101.jpg
- Left for the next batch: none
- Run status when saved: every step before saving completed.
- Originals were not moved or deleted.
```
