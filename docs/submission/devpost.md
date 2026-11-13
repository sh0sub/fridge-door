# Devpost page: Fridge Door (paste-ready, English)

Paste each block into the field of the same name. Track: **Bring Memories to Life**. Images: `gallery/thumbnail.png` (1200x800, 3:2), then `gallery/00-chat.png` (chat preview and completion cards), `gallery/01-flow.png`, `02-digest.png`, `03-delegation.png`, `04-privacy.png` (each 1500x1000).

---

## Project name
Fridge Door

## Tagline (short description)
A Uliya Skill that turns school-notice and kids' drawing photos in your NAS phone backup into a weekly to-do digest and a growing art album per child.

## Track
Bring Memories to Life

---

## Inspiration
Paper used to come home and go on the fridge door: the field-trip slip, the fee notice, the drawing a child was proud of. Now we photograph it, the photo is backed up with everything else, and that is usually the last time anyone looks at it. Reply slips get missed, fees are paid late, and drawings pile up with no child or date attached. A parent who does not read the school's language well has an extra step before any of it can be acted on.

A UGREEN AI NAS already holds the backup and has OCR and vision models built in. Fridge Door uses them for one weekly chore: finding what the school wants back and keeping what the child made.

## What it does
Once a week the parent says, for example, "Sort out this week's school papers." Fridge Door then:

1. Looks for the most recent digest in the output folder. Each digest's meta line says "Next run starts from: {date}", so the default period begins where last week's run stopped and runs to today (at most 31 days; otherwise it asks). With no earlier digest, the default is the last 7 days including today. It reads back the source folder, the period as explicit dates, the children's names and the output folder, and waits for a yes.
2. Lists the images in that period. If more than 60 match, it offers to narrow the list to papers and drawings, or takes the oldest 60. It then leaves out photos tagged `fridge-door-done`, which means Fridge Door has handled the photo once. A batch is the oldest 12 new photos; the parent says "continue" for the next 12.
3. Reads each photo with the NAS OCR. Photos with little or no text go to the NAS vision model, which says whether it is a child's drawing and gives a one-sentence caption.
4. Structures each notice into deadline, action, amount and child, and assigns a drawing to a child by the name written on it, or asks.
5. Carries over deadlines left unticked in the previous digest and upcoming events, so the newest digest holds every open item.
6. Shows one preview with the notices, carried-over items, artwork and everything it would create. For each drawing it asks, as an optional line, whether the child said anything about it. Nothing is written before the parent says yes.
7. After the yes and the NAS approval, copies each child's drawings into a keepsake folder `Artwork - {child}`, creates one album per child that follows that folder, saves one Markdown digest file, and tags every photo the digest lists.

The album is created once per child. Drawings copied in later weeks show up in it without a new album. Because the folder holds copies, the same drawing can appear twice in UGREEN Photos, and the preview says so.

If the parent tells Fridge Door what the child said about a drawing, the words are stored with that drawing in the digest, unchanged and in the language the parent used, for example `Said: "This is our school bus. It goes to the rainbow!"`. If the parent says nothing, nothing is added and the question is not repeated.

On request ("Make Mina's art journal", "What did Jun draw this term?") the Skill builds an artwork journal for one child. It asks the document expert for that child's Artwork lines from the saved digests, exactly as written and in date order, and arranges only those lines into a dated list with the captions, the child's words, the photo file names and the keepsake folder. It shows the journal in the chat and saves it as a file only if the parent wants that.

The digest has seven fixed sections: At a glance, Deadlines (checkbox lines in date order, past ones marked), Events, Notices, Artwork, Needs your check, and Left untouched and run details. Every item names its source photo. Receipts and screenshots are listed and left alone; blurred photos are listed by file name instead of being guessed. Once the digest is saved, notices, copied drawings, unrelated photos and unreadable photos all get the done tag, so later runs leave them out. Only a photo whose expert call failed, or a drawing that was not copied, stays untagged and is tried again next time; if the digest cannot be saved, nothing is tagged and the batch comes back. Original photos are never renamed or deleted.

Later the parent can ask, for example, "When is the field trip fee due?" The answer comes from the newest saved digest, names the digest file and the source photo, and does not read the photos again. A translated copy of the digest is made only if the parent asks for one.

## How it is different
Calendar apps and chat assistants can already pull a date out of a photo you give them, and they do it well. Fridge Door does not claim to read notices better. The difference is narrower:

- It works on the backup that already happens, so there is nothing to upload each week.
- It keeps state between weeks: a file tag marks handled photos, unticked deadlines move into the next digest, and the next run starts from the date the last digest stopped at.
- One run covers both what the school wants back and what the child made.
- The album follows a folder, so it grows without being rebuilt.
- It keeps what the child said next to the drawing, and can turn the saved Artwork lines into a dated journal for one child. Both use only what the parent typed and what the digests already hold.

## How we built it
Fridge Door is a Markdown-only orchestration Skill (version 1.0.0) written against the Uliya Skill Development Standard and the UGOS Skill Creation Tool (uliya-skill-kit 0.7.7, capability catalog 2.2.0). The ZIP has 5 files and is 27,577 bytes: `SKILL.md` plus four references (user guide, digest format, disclosures, test plan). There are no scripts or binaries.

The Skill does not touch the NAS itself. It sends `delegate` commands in a fixed order to four registered experts and passes on only real results from earlier steps. Its instructions name no CLI or action; each expert chooses its own. In `references/disclosures.md` we list the actions we expect, checked against the catalog:

- file-agent: find and read the newest digest and list photos (`ug-filesystem`), look up and add the done tag (`ug-filemgr`), copy drawings into keepsake folders (`file-workflow`)
- photo-agent (`ug-photo`): `vision-ocr`, `vision-vlm`, check whether an album exists, create a folder-following album
- knowledge-agent (`ug-knowledge`): `save-text` for the digest
- document-agent (`ug-document`): the optional translated copy, and reading one child's Artwork lines from the saved digests for the art journal

Uliya writes the notice summaries and any translation of them herself from the recognised text, because the catalog has no action that returns a translation. The workflow has 15 numbered steps plus two sections that run on request (questions about a saved digest, the artwork journal). All five delegation states (completed, failed, waiting for approval, waiting for the user, cancelled) are handled, and so are empty and partial results. Archiving past notices exists as an optional step that is off by default.

No NAS is available before Round 2, so we wrote a Python port of the uliya-skill-kit 0.7.7 check rules, a ZIP builder with the size and file limits, and a dry-run harness that follows `SKILL.md` step by step against simulated expert answers. 214 automated tests cover the checker, the package and the dry runs.

## Challenges we ran into
- **No device yet.** The real reply formats of the experts are not documented, so the dry-run fixtures use assumed shapes. The test plan lists the assumptions to check on the NAS, with a fallback for each.
- **Albums cannot be built from a list of photos.** The album action we found takes no file paths. The first design therefore did not work. We switched to copying drawings into one folder per child and creating an album whose rule is that folder.
- **Photographed paper is not reliable OCR input.** The Skill lists unreadable photos by file name and writes "needs check" for an unclear date or amount instead of filling it in.
- **Writes need care.** Copies, albums, the digest and the tag all change the NAS. Each one waits for the preview, the parent's yes and the NAS approval, and none is retried automatically because a retry could duplicate it.
- **Scope.** One folder, images only, 12 photos per batch. A larger backlog is handled in several batches.

## Accomplishments that we're proud of
- A local check with 0 errors and 0 warnings against our port of the 0.7.7 rules, and 214 automated tests. We could not run the official `check-skill.mjs`, so we do not call the result an official pass.
- A digest where every to-do points to its source photo and can be ticked off, where last week's open items reappear without anyone copying them, and where the next run knows from the digest itself where to start.
- Run memory without a database: one file tag plus the digest files in the output folder.
- A 16-photo test kit with invented content, specified together with the result we expect on the device: 8 notices (5 Korean, 3 English, 1 already past due), 6 drawings (2 with a child's name written on them, 1 deliberately blurred), 1 receipt and 1 screenshot. The first batch should give 6 deadlines (1 past) and 2 events. After "continue", 5 drawings are copied into two keepsake folders (6 if the blurred one is judged a drawing) and 2 albums exist. Over both batches all 16 photos carry the tag, because the receipt, the screenshot and an unreadable blurred drawing are listed in the digest and then tagged too. They are not copied and not guessed at.
- A written list of 19 device assumptions in `references/test-plan.md`, each with a fallback, so the test day starts from what we do not know instead of what we hope.

## What we learned
- A prompt for a NAS expert works best when it is dull: fixed steps, quoted values, one delegate per line, and a rule for every state the expert can return.
- Checking the capability catalog against the design found a real mistake early. We had planned an album per list of photos, and the catalog showed it cannot be done.
- Memory can be as simple as a file tag plus one date in the digest. Our first rule tagged only notices and drawings, so the receipt and the blurred photo would have been read again every week. Tagging every photo the digest lists fixed that.
- Writing the failure paths first (declined approval, empty period, blurred photo) made the normal path shorter.

## What's next
- Round 2 device tests, from `references/test-plan.md`: (1) the first batch on the 16-photo kit: OCR on Korean and English notices, 6 deadlines in date order with 1 marked past, 2 events, and the two named drawings assigned to Mina and Jun without a question; (2) "continue" for the remaining drawings, which must carry over the open deadlines, reuse the two existing albums and report the blurred one; (3) a refused approval, a rerun of the same period, an empty period, a question about the saved digest, and an art journal for Mina that includes the words kept in step (1).
- Replace the simulated expert answers with the real ones and adjust the approval wording to what the device shows.
- Nothing has been run on a NAS yet. The gallery cards are simulated output, not device screenshots.

## Built with
UGREEN AI NAS (Uliya Skills), UGOS Skill Creation Tool (uliya-skill-kit 0.7.7), Markdown, UGREEN Photos, NAS built-in OCR and vision models, Python (checker port, ZIP builder and dry-run harness only; not part of the Skill), pytest, Claude Code

## Try it out
- Skill package: `fridge-door.zip` (one folder `fridge-door/` with `SKILL.md` and `references/`), uploaded with this submission.
- In UGOS, open the Uliya Skills page, upload the ZIP, then say "Fridge Door, sort out this week's school papers."
- Source: https://github.com/sh0sub/fridge-door (MIT)
- Evidence: 214 automated tests (`pytest`), the local static check (0 errors, 0 warnings), and the 16-photo test kit with expected results in `references/test-plan.md`. The gallery cards marked "Simulated dry run" are not device screenshots.

---

## License
Fridge Door is released under the MIT License, Copyright (c) 2026 sh0sub. The full text is in the `LICENSE` file of the repository.

## Third-party components
None. The Skill delegates only to the registered NAS experts, uses the OCR and vision models built into the UGREEN AI NAS, downloads nothing and needs no API key. The summaries and the digest text are written by Uliya, so they run on whichever model the NAS owner has set up for Uliya.

## AI tools disclosure
Claude Code (Anthropic) helped write and review the Skill documents, the local static checker, the tests and this submission text. The UGOS Skill Creation Tool (uliya-skill-kit 0.7.7, UGREEN) was the capability reference and the source of the check rules; we read its checker script as source and ported the rules, and did not run the official script. All text was reviewed by the author.

## Developed during the hackathon
Everything in the package (workflow, digest layout, user guide, test plan and the invented test notices and drawings) was written for the UGREEN Hackathon 2026, starting 2026-10-26. All names, schools and phone numbers in examples and test material are invented. Fridge Door is an independent community Skill, not an official UGREEN product.

## Team
Individual.
