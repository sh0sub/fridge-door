# Disclosures

## Package contents

| File | Purpose |
|---|---|
| SKILL.md | The orchestration workflow Uliya follows |
| references/README.md | User guide |
| references/digest-format.md | Fixed layout of the digest file, with an example |
| references/disclosures.md | This file |
| references/test-plan.md | Device test plan and fallback table |

The package holds Markdown only: no scripts, binaries, manifests or credentials.

## NAS capabilities used

All NAS work is delegated to registered experts. The Skill itself never runs a CLI.

| Expert agent | CLI | Actions the expert is expected to use | Effect | Used in |
|---|---|---|---|---|
| file-agent | ug-filesystem | find (photo list, earlier digest), mkdir and cpmv, for the optional archive only | read; archive moves files | Steps 1, 5, 10 |
| file-agent | ug-filemgr | tag-get-by-name, tag-filter, tag-add, tag-add-file | read; adds one tag | Steps 2, 9 |
| photo-agent | ug-photo | vision-ocr, vision-vlm, albums, figure-albums, search-picture, create-album | read; creates albums | Steps 1 (fallback), 3, 4, 5, 6, 7 |
| document-agent | ug-document | writing (condense), translate | read; returns text only | Step 5 |
| knowledge-agent | ug-knowledge | save-text | writes one new file | Step 8 |

The experts choose and run the actual actions; the table records what the workflow asks for, checked against the public capability catalog 2.0.0 shipped with uliya-skill-kit 0.7.3.

## Third-party components

None. The Skill uses only the OCR, vision, document and translation models built into the NAS. It calls no external service and needs no API key.

## Developed during the hackathon

Everything in this package was written for the UGREEN Hackathon 2026 (from 2026-10-26): the workflow, the digest layout, the user guide, the test plan and the test notices and drawings used for checking. Names, schools and phone numbers in examples and test material are invented.

## AI tools

- Claude Code (Anthropic) helped draft the Skill text and the static checks.
- uliya-skill-kit 0.7.3 (UGREEN) was used as the capability reference and static check rule set.

All text was reviewed by the author.

## Data and privacy

Photos, recognised text, captions and digests stay on the NAS. The Skill keeps no memory outside the NAS; the only run memory is the fridge-door-done file tag and the digest files in the output folder.
