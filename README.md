# fridge-door

**Fridge Door** is a Uliya Skill for UGREEN AI NAS. It turns the school notices and kids' drawings sitting in a phone backup folder into a weekly parent to-do digest and per-child artwork albums, read entirely on the NAS.

Built for the UGREEN Hackathon 2026 on AI NAS (Round 1 deadline 2026-11-16 KST). Round 1 submission is a 500-word proposal plus the skill ZIP; no device required.

- Input: photos already on the NAS via phone auto-backup
- OCR, vision and translation run on the NAS built-in models; nothing leaves the device
- Output: weekly to-do list, per-child albums in Photos, run memory via NAS file tags

## Status

Round 1 package ready (checked 2026-11-01): `fridge-door/SKILL.md` plus four references, zipped to `dist/fridge-door.zip` (5 files, 15,854 bytes). Passes the local static check with 0 errors and 0 warnings, and 123 automated tests pass. The one-page proposal (`docs/proposal/proposal.pdf`, 489 words) and Devpost copy (`docs/submission/devpost.md`) match this package. No video is required for Round 1. Not yet run on a NAS (Round 2).

## Layout

| Path | What |
|---|---|
| `fridge-door/` | The Skill package (goes into the ZIP as-is): `SKILL.md`, `references/` |
| `scripts/check.py` | Static checker: Python port of uliya-skill-kit 0.7.3 `check-lib.mjs` plus the plan.md checklist rules |
| `scripts/build_zip.py` | Builds `dist/fridge-door.zip` after a clean check, verifies size and file limits |
| `scripts/dryrun.py` | Dry run of the workflow against simulated expert answers |
| `tests/fixtures/dryrun/` | Simulated expert answers: flow A, test kit batch A (notices), batch B (drawings) |
| `docs/plan.md` | Plan |

## Development

```
python3 -m venv .venv && .venv/bin/pip install pytest ruff mypy
.venv/bin/pytest                                   # unit + integration tests
.venv/bin/ruff check . && .venv/bin/mypy           # lint, typecheck
.venv/bin/python scripts/check.py fridge-door --summary
.venv/bin/python -m scripts.build_zip              # dist/fridge-door.zip
.venv/bin/python -m scripts.dryrun tests/fixtures/dryrun/flow-a.json
```

The official checker is `node uliya-skill-kit/scripts/check-skill.mjs fridge-door` from the kit download; run it as well before submitting.

## License

MIT
