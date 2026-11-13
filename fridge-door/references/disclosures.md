# Disclosures

## Package contents

| File | Purpose |
|---|---|
| SKILL.md | The orchestration workflow Uliya follows |
| references/README.md | User guide |
| references/digest-format.md | Fixed layout of the digest file, with an example |
| references/disclosures.md | This file |
| references/test-plan.md | Device test day plan, device assumptions and fallback table |

The package holds Markdown only: no scripts, binaries, manifests or credentials.

## NAS capabilities used

All NAS work is delegated to registered experts with plain-language instructions. The Skill never runs a CLI itself, and its instructions name no CLI, Action or parameter; each expert picks its own Actions. The table lists the Actions we expect each expert to use, checked against the public capability catalog (structure 2.2.0) shipped with uliya-skill-kit 0.7.7. Effect and approval are the catalog values. Which Action an expert really uses is only known on the device.

| Expert agent | CLI | Expected Action | Effect | Approval | Used in |
|---|---|---|---|---|---|
| file-agent | ug-filesystem | `find` | read | none | Step 1 newest digest (timestamp in the file name, else creation time), Step 2 photo list, artwork journal fallback (at most the 8 newest digests) |
| file-agent | ug-filesystem | `cat` | read | none | Step 1 read the newest digest by its path; artwork journal fallback |
| file-agent | ug-filesystem | `stat`, `mkdir` | read; state-change | none; gateway | Step 9, before any copy: make sure the output folder exists and return its real path |
| file-agent | ug-filesystem | `ls`, `category` | read | none | Step 9 list the keepsake folder: its real path, file id, storage type (personal or shared) and files |
| file-agent | ug-filesystem | `cpmv` | state-change | gateway | Step 13 optional archive (moves files) |
| file-agent | ug-filemgr | `tag-get-by-name`, `tag-list-file` or `tag-get-file` | read | none | Step 3 photos handled before |
| file-agent | ug-filemgr | `tag-add`, `tag-add-file` | state-change | gateway | Step 12 tag handled photos |
| file-agent | file-workflow | `batch-transfer` (copy) | state-change | workflow | Step 9 copy drawings into keepsake folders; creates the keepsake folder when it does not exist |
| file-agent | ug-filesystem | `mkdir` | state-change | gateway | Step 9 create the keepsake folder, if the expert creates it before the copy instead |
| file-agent | file-workflow | `batch-move` | state-change | workflow | Step 13 optional archive, as an alternative to `cpmv` |
| photo-agent | ug-photo | `search-picture` | read | none | Step 2 fallback listing when the folder listing fails, and the optional narrowing to papers and drawings when more than 60 photos match |
| photo-agent | ug-photo | `vision-ocr` | read | none | Step 4 text on each photo |
| photo-agent | ug-photo | `vision-vlm` | read | none | Step 5 is it a child's drawing, caption |
| photo-agent | ug-photo | `albums`, `album-detail` | read | none | Step 8 does the child's album exist, and which folder it follows |
| photo-agent | ug-photo | `create-album-condition` | state-change | workflow | Step 10 one album per child that follows the keepsake folder (folder path, file id and storage type) |
| knowledge-agent | ug-knowledge | `save-text` | state-change | workflow | Step 11 save the digest to the real folder path; artwork journal save on request |
| document-agent | ug-document | `qa` | read | none | Artwork journal: read the artwork lines of one child from the saved digests |
| document-agent | ug-document | `translate` | mixed | gateway | Step 14 optional translated copy of the saved digest |

Not delegated: structuring notices, the one-line summaries and their translation into the parent language. Uliya writes these itself from the recognised text (Step 6), because the catalog has no Action that takes text and returns a translation. Uliya also builds the artwork journal itself, only from the lines the experts return.

## Third-party components

None. The Skill calls no external service, downloads nothing and needs no API key.

## Developed during the hackathon

Everything in this package was written for the UGREEN Hackathon 2026 (from 2026-10-26): the workflow, the digest layout, the artwork journal, the user guide, the test plan and the test notices and drawings used for checking. Names, schools and phone numbers in examples and test material are invented.

## AI tools

- Claude Code (Anthropic) helped write and review the Skill text, the local static checker, the dry-run harness and the tests.
- uliya-skill-kit 0.7.7 (UGREEN) was used as the capability reference and as the source of the static check rules. Its checker script was read as source and its rules were ported to a local Python checker; the official script itself was not run.

All text was reviewed by the author.

## Data and privacy

Photos, recognised text, captions, copies and digests are stored on the NAS. Text recognition and the picture check run in the NAS photo expert. Summaries and the digest text are written by Uliya, so they are processed by whichever model the NAS owner has set up for Uliya (a local model or a cloud model the owner chose). The Skill keeps no memory of its own; the only run memory is the fridge-door-done file tag and the digest files in the output folder (including the "Next run starts from" date). A child's words are stored only when the parent types them at the preview.
