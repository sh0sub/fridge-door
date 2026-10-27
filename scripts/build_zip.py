#!/usr/bin/env python3
"""Build the submission ZIP: one top-level folder fridge-door/ with SKILL.md and references/.

Refuses to build when scripts/check.py reports any error, and verifies the limits from
docs/plan.md (ZIP <= 10 MB, <= 100 files, each file <= 1 MB). No __MACOSX entries, no hidden
files, fixed timestamps so the same input gives the same ZIP.

Usage: python3 scripts/build_zip.py [--out dist/fridge-door.zip]
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

from scripts.check import check_skill

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "fridge-door"
ZIP_MAX_BYTES = 10 * 1024 * 1024
FILE_MAX_BYTES = 1024 * 1024
MAX_FILES = 100
FIXED_TIME = (2026, 1, 1, 0, 0, 0)


class BuildError(Exception):
    pass


def package_files(skill_dir: Path) -> list[Path]:
    files = sorted(p for p in skill_dir.rglob("*") if p.is_file() or p.is_symlink())
    for p in files:
        rel = p.relative_to(skill_dir)
        if any(part.startswith(".") for part in rel.parts):
            raise BuildError(f"hidden file in package: {rel}")
        if p.is_symlink():
            raise BuildError(f"symlink in package: {rel}")
    return files


def build(skill_dir: Path, out: Path) -> dict[str, int]:
    result = check_skill(skill_dir)
    if result["summary"]["errors"]:
        raise BuildError(f"checker reports {result['summary']['errors']} error(s); run scripts/check.py")
    files = package_files(skill_dir)
    if len(files) > MAX_FILES:
        raise BuildError(f"{len(files)} files > {MAX_FILES}")
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in files:
            data = p.read_bytes()
            if len(data) > FILE_MAX_BYTES:
                raise BuildError(f"{p.name} is {len(data)} bytes > 1 MB")
            info = zipfile.ZipInfo(f"{skill_dir.name}/{p.relative_to(skill_dir).as_posix()}", FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, data)
    size = out.stat().st_size
    if size > ZIP_MAX_BYTES:
        out.unlink()
        raise BuildError(f"ZIP is {size} bytes > 10 MB")
    return {"files": len(files), "zip_bytes": size, "warnings": result["summary"]["warnings"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=ROOT / "dist" / "fridge-door.zip")
    args = parser.parse_args(argv)
    try:
        info = build(SKILL_DIR, args.out)
    except BuildError as error:
        print(f"build failed: {error}", file=sys.stderr)
        return 1
    print(f"{args.out}: {info['files']} files, {info['zip_bytes']} bytes, {info['warnings']} checker warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
