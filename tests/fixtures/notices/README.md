# Round 2 test notices (invented data)

All schools, teachers, children, phone numbers (`02-000-0000`) are made up. HTML sources live here; PDFs are generated into `.local/notices/` (gitignored) with:

```
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf="<abs>/.local/notices/<name>.pdf" "file://<abs>/tests/fixtures/notices/<name>.html"
```

Print on A4 at 100%, then photograph on a flat surface in daylight (no QR codes inside). Matching mock OCR/answers: `tests/fixtures/dryrun/testkit-a.json` (KIT_N01..N08). Test day is 2026-11-30 / 12-01; all dates below are after it except the past one.

| Photo | File | Title | Sender | Due / event | Type | Amount | Child |
|---|---|---|---|---|---|---|---|
| KIT_N01 | ko-01-reply | 겨울 체험학습 참가 동의서 회신 안내 | 하늘초등학교 2학년 3반 | due 2026-12-04 (trip 12-16) | Reply slip | - | Mina (김민아) |
| KIT_N02 | ko-03-fee | 현장학습비 납부 안내 | 하늘초등학교 | payment 2026-12-08 (스쿨뱅킹) | Payment | KRW 18,000 | Mina (김민아) |
| KIT_N03 | ko-02-supplies | 준비물 안내 (리코더 등) | 하늘초등학교 1학년 2반 | due 2026-12-09 | Item to bring | - | Jun (이준) |
| KIT_N04 | ko-04-event | 겨울 학예회 안내 | 하늘초등학교 | event 2026-12-18 14:00, 본관 2층 강당 | Event | - | none |
| KIT_N05 | ko-05-survey-past (fictionalized from a public sample; original kept in `.local/notices/_original/`) | 하늘시교육청 2026 생성형 AI 활용 실태조사 안내 | 하늘초등학교 | period 2026-08-19 to 09-23 (past) | Reply slip | - | none |
| KIT_N06 | en-03-event | Winter Concert flyer | Sunny Hill International School, Grade 2 | event 2026-12-10 18:00, Main Hall | Event | free | none |
| KIT_N07 | en-01-permission | Field Trip Permission Slip | Sunny Hill International School, Class 1B | due 2026-12-04 (trip 12-11) | Reply slip | USD 12.00 | Jun (Jun Lee) |
| KIT_N08 | en-02-supplies | Winter Art Week Supply List | Sunny Hill International School, Grade 2 | due 2026-12-14 (bring that day) | Item to bring | - | none |

Expected digest counts: 6 deadlines (1 past) and 2 events.
