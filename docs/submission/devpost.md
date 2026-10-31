# Devpost page: Fridge Door (paste-ready, English)

Paste each block into the field of the same name. Track: **Bring Memories to Life**. Images: `gallery/thumbnail.png` (1200x800, 3:2), then `gallery/01-flow.png`, `02-digest.png`, `03-delegation.png`, `04-privacy.png` (each 1500x1000).

---

## Project name
Fridge Door

## Tagline (short description)
A Uliya Skill that turns school-notice and kids'-drawing photos in your NAS phone backup into a weekly to-do digest and per-child albums, read entirely on the device.

## Track
Bring Memories to Life

---

## Inspiration
Paper used to live on the fridge door: the field-trip slip, the fee notice, the drawing a child was proud of. Today we photograph it, the photo lands in a phone backup folder, and it is forgotten. Reply slips are missed, fees are paid late, and hundreds of drawings pile up that nobody can attribute to a child or find again. Parents who do not read the local language well are hit hardest, because even the photographed notice is hard to act on.

A UGREEN AI NAS already holds that backup and already has OCR, vision and translation models on board. Fridge Door puts them to work on the one job every school parent has every week.

## What it does
Once a week the parent says, for example, "Sort out this week's school papers." Fridge Door:

1. Reads back the source folder, the period (default: last 7 days, stated as explicit dates), the children's names and the output folder, and waits for a yes.
2. Lists the period's images (at most 12 per run) and leaves out photos already tagged `fridge-door-done`.
3. Reads each photo with the NAS OCR. Photos with little or no text go to the NAS vision model, which decides whether it is a drawing and writes a one-sentence caption.
4. Structures every notice into deadline, action, amount and child, and assigns artwork to a child by the name written on it (or asks the parent).
5. Shows a preview of deadlines, events, artwork and everything it would create. Nothing is created before the parent approves.
6. After approval, creates albums in UGREEN Photos ("School notices {year-month}" and "Artwork - {child} {year}"), saves one Markdown digest file, and tags handled photos so the next run only processes new ones.

The digest always has the same seven sections: At a glance, Deadlines (checkbox lines in date order, past ones flagged), Events, Notices (with summaries translated into the parent's language when it differs), Artwork, Needs your check, and Left untouched and run details. Every item names its source photo file. Receipts and screenshots are listed and left untouched; blurred or unreadable photos are listed by name instead of being guessed. Original photos are never renamed or deleted.

## How we built it
Fridge Door is a Markdown-only orchestration Skill built with the UGOS Skill Creation Tool (uliya-skill-kit 0.7.3) and the Uliya Skill Development Standard. The package is `SKILL.md` plus four references (user guide, digest format, disclosures, test plan): 5 files, 14,711 bytes zipped, no scripts or binaries.

The Uliya parent agent never touches the NAS itself. It issues only `delegate` commands, in a fixed order, to four registered expert agents, and passes only real upstream results into the next step:

- file-agent (`ug-filesystem`, `ug-filemgr`): list photos, look up and add the run-memory tag
- photo-agent (`ug-photo`): `vision-ocr`, `vision-vlm`, `create-album`
- document-agent (`ug-document`): condense and translate
- knowledge-agent (`ug-knowledge`): `save-text` for the digest

All five delegation states (completed, failed, waiting for approval, waiting for the user, cancelled) are handled, as are empty and partial results. An optional archive step exists but is off by default and runs only on explicit request.

Because there is no NAS available before Round 2, we built a Python checker (a port of the uliya-skill-kit 0.7.3 rules plus our own checklist), a ZIP builder with size and file limits, and a dry-run harness that follows `SKILL.md` step by step against simulated expert answers. 115 automated tests cover the checker, the package and the dry runs.

## Challenges we ran into
- **Orchestrating without a device.** The real answer formats of the experts are not documented, so the dry-run fixtures use minimal assumed shapes. We marked them as unverified and kept every instruction defensive: say "no results" when empty, never invent a value.
- **Honest failure over plausible output.** OCR on photographed paper can be wrong. The Skill reports unreadable photos by file name and writes "needs check" instead of guessing dates, amounts or names.
- **Writes without surprises.** Albums, the digest file and the tag are all writes, so each one happens only after a preview, the parent's yes and the platform's approval, and only for photos that were actually handled.
- **Keeping it small enough to be reliable.** One folder, 12 photos, images only per run. Larger jobs become shorter periods.

## Accomplishments that we're proud of
- A complete Skill package that passes our local static check with 0 errors and 0 warnings.
- A fixed, readable digest where every to-do points back to its source photo.
- Run memory without a database: the NAS file tag `fridge-door-done` is the only state, so a second run skips everything already handled.
- A 16-photo invented test kit specified for the device test: 8 notices (5 Korean, 3 English, 1 past-dated), 6 drawings (2 with a child's name written on them, 1 deliberately blurred), 1 receipt and 1 screenshot. Expected result: 6 deadlines (1 past) and 2 events from the notices, and a second run that skips all 13 handled photos while the receipt, the screenshot and the blurred drawing are reported, not handled.
- 115 automated tests.

## What we learned
- On a NAS Skill, the best prompt is a boring one: fixed steps, quoted values, one delegate per line, and a rule for every state the expert can return.
- "Nothing leaves the device" is a design constraint, not just a claim. It decided the architecture: built-in models only, no keys, no cloud.
- Memory can be as simple as a file tag.
- Writing the failure paths (declined approval, empty period, blurred photo) first made the happy path shorter.

## What's next
- Round 2: run the Skill on the assigned NAS and replace the simulated expert answers with real ones, tuning the wording of approval prompts, OCR handling on Korean and English print, vision captions on drawings and album creation from file paths.
- Based on what the device shows, widen the 12-photo cap and handle more kinds of notices.
- A user walkthrough of the README by another parent to tighten the wording (planned v0.9.0).

## Built with
UGREEN AI NAS (Uliya Skills), UGOS Skill Creation Tool (uliya-skill-kit 0.7.3), Markdown, UGREEN Photos, NAS built-in OCR, vision, document and translation models, Python (checker, ZIP builder and dry-run harness only; not part of the Skill), pytest, Claude Code

## Try it out
- Skill package: `fridge-door.zip` (one folder `fridge-door/` with `SKILL.md` and `references/`), uploaded with this submission.
- In UGOS, open the Uliya Skills page, upload the ZIP, then say "Fridge Door, sort out this week's school papers."
- Source: https://github.com/sh0sub/fridge-door (MIT) [PRIVATE REPO: make public or remove this line before submitting]
- Not yet run on a NAS (Round 1 needs no device).

---

## License
Fridge Door is released under the MIT License, Copyright (c) 2026 sh0sub. The full text is in the `LICENSE` file of the repository.

## Third-party components
None. The Skill uses only the OCR, vision, document and translation models built into the UGREEN AI NAS. It calls no external service and needs no API key.

## AI tools disclosure
Claude Code (Anthropic) was used to help draft the Skill text, the proposal, this page, and the static checks and tests. The UGOS Skill Creation Tool (uliya-skill-kit 0.7.3, UGREEN) was used as the capability reference and static check rule set. All text was reviewed by the author.

## Developed during the hackathon
Everything in the package (workflow, digest layout, user guide, test plan and the invented test notices and drawings) was written for the UGREEN Hackathon 2026, starting 2026-10-26. All names, schools and phone numbers in examples and test material are invented. Fridge Door is an independent community Skill, not an official UGREEN product.

## Team
Individual.
