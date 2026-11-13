# fridge-door

**Fridge Door** is a Uliya Skill for UGREEN AI NAS. It turns the school notices and kids' drawings sitting in a phone backup folder into a weekly parent to-do digest, per-child keepsake folders, and one album per child that follows its folder.

Built for the UGREEN Hackathon 2026 on AI NAS (Round 1 deadline 2026-11-16 KST). Round 1 submission is a 500-word proposal plus the skill ZIP; no device required.

- Input: photos already on the NAS via phone auto-backup
- Text recognition and the picture check are delegated to the NAS photo expert; the Skill calls no outside service. Summaries are written by Uliya, on whichever model the NAS owner set up for it
- Output: weekly to-do digest (open deadlines and upcoming events carried over, a child's own words kept with a drawing), copies of drawings in per-child keepsake folders, one album per child created once from the folder's real path and id, an artwork journal on request, run memory via a NAS file tag (every listed photo is handled once) and the digest's "Next run starts from" date
- Batches of 12 photos ("continue" for more), optional narrowing when more than 60 photos match; questions such as "when is the field trip fee due?" are answered from the newest digest

## Status

Round 1 package v1.0.0, rewritten for uliya-skill-kit 0.7.7 (capability catalog structure 2.2.0) on 2026-11-13: `fridge-door/SKILL.md` plus four references, revised the same day after an independent review and again after a second review (15 workflow steps, 20 delegations, SKILL.md body 233 lines), zipped to `dist/fridge-door.zip` (5 files, 27,577 bytes). The local static checker (a Python port of the kit's `check-lib.mjs` 0.7.7 rules, with JavaScript's Unicode `\s`) reports 0 errors and 0 warnings, including the CLI-to-agent evidence check against the kit's catalog; 214 automated tests pass (215 with `FRIDGE_DOOR_KIT_CATALOG` set). The official `check-skill.mjs` was not run; see `docs/checks/check-skill-2026-11-13.md`. Not yet run on a NAS (Round 2).

## Layout

| Path | What |
|---|---|
| `fridge-door/` | The Skill package (goes into the ZIP as-is): `SKILL.md`, `references/` |
| `scripts/check.py` | Static checker: Python port of uliya-skill-kit 0.7.7 `check-lib.mjs` plus the plan.md checklist rules; `--catalog` validates the kit's capability catalog (not vendored) |
| `scripts/build_zip.py` | Builds `dist/fridge-door.zip` after a clean check, verifies size and file limits |
| `scripts/dryrun.py` | Dry run of the workflow against simulated expert answers |
| `tests/fixtures/dryrun/` | Simulated expert answers: flow A (one batch), the 16-photo test kit (two batches); variants such as the refused-approval edge, narrowing and the artwork journal are derived in `tests/integration/test_dryrun.py` |
| `docs/plan.md` | Plan |

## Development

```
python3 -m venv .venv && .venv/bin/pip install pytest ruff mypy
.venv/bin/pytest                                   # unit + integration tests
.venv/bin/ruff check . && .venv/bin/mypy           # lint, typecheck
.venv/bin/python scripts/check.py fridge-door --summary
.venv/bin/python scripts/check.py fridge-door --summary --catalog <kit>/data/capability-catalog.json
.venv/bin/python -m scripts.build_zip              # dist/fridge-door.zip
.venv/bin/python -m scripts.dryrun tests/fixtures/dryrun/flow-a.json
```

The official checker is `node uliya-skill-kit/scripts/check-skill.mjs fridge-door` from the kit download (0.7.7); run it as well before submitting. The kit's catalog is not copied into this repository because its licence is unclear.

## License

MIT
