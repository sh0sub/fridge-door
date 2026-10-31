# Digest format

The digest is one Markdown file per run, saved as "Fridge Door – {period}.md" in the agreed output folder. It always has the title line, a meta line and the same seven sections in the same order, even when a section is empty. Write it in the parent language. Use only real results from the run; every item names its source photo file.

## Fixed layout

```
# Fridge Door – {period}
Source: {source_folder} · {N} photos read · Generated on NAS {date time}

## At a glance
## Deadlines
## Events
## Notices
## Artwork
## Needs your check
## Left untouched and run details
```

## Section rules

0. **Meta line**, directly under the title: `Source: {source_folder} · {N} photos read · Generated on NAS {YYYY-MM-DD HH:MM}`. N is the number of photos read in this run (the photos to process); use `{today}` alone when the NAS time is not known.

1. **At a glance**: the next due item with its date and source file; counts of deadlines (past ones separately), events, artworks per child; how many photos were left untouched and how many were already handled; album names with photo counts.
2. **Deadlines**: one checkbox line per due item, earliest first: `- [ ] {date} — {action} · {child} · "{quoted date text}" · {source file}`. Put the warning prefix `⚠` before the date when the due date is before the run date: `- [ ] ⚠ {date} — ...`. Add "carried over from {previous digest name}" for items taken from the last digest. The parent ticks a box (`- [x]`) when done; the next run treats ticked lines as done.
3. **Events**: one line per event with date and time, what it is, who it concerns, the quoted date text and the source file. No checkbox.
4. **Notices**: a table with one row per notice: source file, original key line (quoted as read), summary in the parent language, due date, action. When translation failed, keep the original summary and write "translation unavailable".
5. **Artwork**: one subheading per child, then one line per photo: source file, the caption from the vision check, and how the child was assigned (name read on the drawing, people album, or chosen by the parent). Artwork without a child goes under "Child not chosen".
6. **Needs your check**: photos that could not be read, dates or amounts marked "needs check", and notices whose child is unclear, each with the file name and the reason. Write "Nothing to check this time." when empty.
7. **Left untouched and run details**: unrelated photos (with a one-word reason such as receipt or screenshot), photos already handled on earlier runs, albums created with their real photo counts, steps that were declined or failed, and the line "Originals were not moved or deleted." When the parent asked for the optional archive in this run, list instead the past notice photos that will be moved after approval and their new folder; the archive runs after the digest is saved, so the run report states what was actually moved.

Never invent dates, amounts, school names, child names or captions. A value that cannot be read is written as "needs check", not guessed.

## Example

This example uses invented names and a fictional school. Parent language: English.

```
# Fridge Door – 2026-10-19 to 2026-10-25
Source: Photos/PhoneBackup · 7 photos read · Generated on NAS 2026-10-26 21:14

## At a glance
- Next due: field-trip fee KRW 12,000 by 2026-10-31 (IMG_0104.jpg)
- 3 deadlines (0 past), 1 event, 2 artworks (Mina 2)
- 1 photo left untouched, 2 already handled on earlier runs
- Albums: School notices 2026-10 (4 photos), Artwork – Mina 2026 (2 photos)

## Deadlines
- [ ] 2026-10-31 — Pay the field-trip fee, KRW 12,000 · Mina · "10월 31일까지 납부" · IMG_0104.jpg
- [ ] 2026-11-01 — Sign and return the consent slip for the museum trip · Mina, Class 2-3 · "11월 1일까지 회신" · IMG_0102.jpg
- [ ] 2026-11-04 — Pack a jump rope for PE · Jun · "11월 4일 준비물: 줄넘기" · IMG_0103.jpg

## Events
- 2026-11-07 14:00 — School arts festival, parents welcome · all children · "11월 7일 오후 2시 학예회" · IMG_0105.jpg

## Notices
| Source | Original key line | Summary | Due | Action |
|---|---|---|---|---|
| IMG_0102.jpg | 현장체험학습 참가 동의서를 11월 1일까지 회신해 주세요. | Museum field trip: return the signed consent slip. | 2026-11-01 | Reply slip |
| IMG_0103.jpg | 11월 4일 체육 시간 준비물: 줄넘기 | Bring a jump rope to PE. | 2026-11-04 | Item to bring |
| IMG_0104.jpg | 현장체험학습비 12,000원을 10월 31일까지 납부해 주세요. | Field-trip fee KRW 12,000. | 2026-10-31 | Payment |
| IMG_0105.jpg | 11월 7일 오후 2시 강당에서 학예회를 엽니다. | Arts festival in the school hall, 2 pm. | 2026-11-07 | Event |

## Artwork
### Mina
- IMG_0106.jpg — A crayon drawing of a yellow school bus under a rainbow. (name read on the drawing: 김민아)
- IMG_0107.jpg — A paper-cup robot craft, silver and red. (chosen by the parent)

## Needs your check
Nothing to check this time.

## Left untouched and run details
- Left untouched: IMG_0108.jpg (receipt)
- Already handled on earlier runs: IMG_0100.jpg, IMG_0101.jpg
- Albums created: School notices 2026-10 (4 photos), Artwork – Mina 2026 (2 photos)
- Originals were not moved or deleted.
```
