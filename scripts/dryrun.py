#!/usr/bin/env python3
"""Dry run of the fridge-door workflow against simulated expert responses (fixtures).

The Skill is executed on the NAS by the Uliya parent agent. There is no NAS here, so this
harness plays both sides deterministically:

* Expert side: every delegate answer (file list, tags, OCR text, vision answer, copy result,
  folder listing, album id, saved path, ...) comes from a JSON fixture. The shapes of real
  answers are not known (catalog example outputs are synthetic), so fixtures use a minimal
  shape (미확인: 실호출로 확인 필요). Look-ups of saved digests (Step 1, the artwork journal)
  and the keepsake folder listing (Step 9) are answered from a small simulated NAS
  (``nas_files``, ``keepsake_existing`` and files written during the same dry run) unless the
  fixture gives explicit answers.
* Parent side: follows SKILL.md step by step. The delegate commands are taken verbatim from
  SKILL.md and every {value} is filled from upstream results, so a missing value, a leftover
  brace or broken shell quoting fails the run. Judgement calls the parent would make
  (structuring a notice, its summary line in the parent language) are fixture data under
  "parent_llm"; the rule-based parts (default period, batching, sorting, past flag, child
  matching, carry-over, which photos are tagged, "Next run starts from", Done / Partly done)
  are computed here.

Waiting states: ``waiting_user`` and ``waiting_approval`` resume the same delegation. After a
refused approval the fixture must say which terminal state the resumed delegation returned
(``denied``); the harness never predicts it.

Usage:  python3 -m scripts.dryrun tests/fixtures/dryrun/flow-a.json
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import shlex
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from scripts.check import delegate_commands, full_instruction

ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = ROOT / "fridge-door" / "SKILL.md"
DIGEST_FORMAT = ROOT / "fridge-door" / "references" / "digest-format.md"
LIST_LIMIT = 60
BATCH_SIZE = 12
MAX_PERIOD_DAYS = 31
JOURNAL_FALLBACK_LIMIT = 8
PAST_MARK = "⚠"
TAG = "fridge-door-done"
DIGEST_HINT = "fridge-door-digest"
JOURNAL_HINT = "fridge-door-journal"
NEXT_START = "Next run starts from: "
NAME_STAMP = re.compile(r"_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})")
PAPER_WORDS = ("paper", "document", "notice", "form", "letter", "printed")
TRANSLATED_COPY = re.compile(r"[._-][a-z]{2}(?:-[A-Za-z]{2})?\.md$")
SCHOOL_MARKERS = ("학교", "가정통신문", "학부모", "담임", "회신", "준비물", "납부", "school", "class", "parents", "teacher", "pta")
WRITE_KEYS = ("copy_artwork", "create_album", "ensure_folder", "save_digest", "tag_add", "archive", "translate_copy", "journal_save")

# (heading prefix, index of the delegate under that heading) -> step key
STEP_KEYS = {
    ("## Step 1", 0): "find_digest",
    ("## Step 1", 1): "read_digest",
    ("## Step 2", 0): "list_photos",
    ("## Step 2", 1): "narrow_photos",
    ("## Step 2", 2): "list_photos_fallback",
    ("## Step 3", 0): "tag_lookup",
    ("## Step 4", 0): "ocr",
    ("## Step 5", 0): "vlm",
    ("## Step 8", 0): "album_lookup",
    ("## Step 9", 0): "ensure_folder",
    ("## Step 9", 1): "copy_artwork",
    ("## Step 9", 2): "list_keepsake",
    ("## Step 10", 0): "create_album",
    ("## Step 11", 0): "save_digest",
    ("## Step 12", 0): "tag_add",
    ("## Step 13", 0): "archive",
    ("## Step 14", 0): "translate_copy",
    ("## Artwork journal", 0): "journal_query",
    ("## Artwork journal", 1): "journal_find",
    ("## Artwork journal", 2): "journal_save",
}


class DryRunError(Exception):
    """The workflow text or the fixture is inconsistent (a test failure, not a workflow state)."""


class Stop(Exception):
    def __init__(self, status: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


@dataclass
class Template:
    key: str
    target: str
    instruction: str
    line: int


@dataclass
class Call:
    key: str
    item: str
    target: str
    command: str
    status: str


@dataclass
class Batch:
    number: int
    photos: list[str]
    remaining: int = 0
    notices: list[dict[str, Any]] = field(default_factory=list)
    artwork: list[dict[str, Any]] = field(default_factory=list)
    unrelated: list[dict[str, str]] = field(default_factory=list)
    unreadable: list[dict[str, str]] = field(default_factory=list)
    failed: list[dict[str, str]] = field(default_factory=list)
    carried: list[str] = field(default_factory=list)
    carried_events: list[str] = field(default_factory=list)
    carry_note: str = ""
    period_note: str = ""
    previous_digest: str | None = None
    albums_existing: dict[str, bool | None] = field(default_factory=dict)
    keepsake_paths: dict[str, str] = field(default_factory=dict)
    keepsake_ids: dict[str, str] = field(default_factory=dict)
    keepsake_types: dict[str, str] = field(default_factory=dict)
    copies: dict[str, list[dict[str, str]]] = field(default_factory=dict)
    same_name: dict[str, list[str]] = field(default_factory=dict)
    not_copied: dict[str, list[dict[str, str]]] = field(default_factory=dict)
    albums: list[dict[str, Any]] = field(default_factory=list)
    album_notes: dict[str, str] = field(default_factory=dict)
    steps: list[tuple[str, str]] = field(default_factory=list)
    preview: str | None = None
    preview_again: str | None = None
    digest: str | None = None
    digest_shown_in_conversation: bool = False
    saved_path: str | None = None
    next_start: str = ""
    handled: list[str] = field(default_factory=list)
    tagged: list[str] = field(default_factory=list)
    archived: list[str] = field(default_factory=list)
    translated_copy: str | None = None
    report: str = ""
    completion_card: str = ""
    progress: list[str] = field(default_factory=list)


@dataclass
class Outcome:
    status: str = "completed"
    calls: list[Call] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)
    approvals: list[str] = field(default_factory=list)
    period: str = ""
    photos_found: int = 0
    total_matches: int = 0
    already_done: list[str] = field(default_factory=list)
    new_photos: list[str] = field(default_factory=list)
    batches: list[Batch] = field(default_factory=list)
    answer: str = ""
    journal: str = ""
    journal_path: str | None = None
    report: str = ""

    def calls_for(self, key: str) -> list[Call]:
        return [c for c in self.calls if c.key == key]

    @property
    def batch(self) -> Batch:
        if not self.batches:
            raise DryRunError("no batch was started")
        return self.batches[-1]

    def _last(self, name: str, default: Any = None) -> Any:
        return getattr(self.batches[-1], name) if self.batches else default

    # convenience views on the last batch
    preview = property(lambda self: self._last("preview"))
    digest = property(lambda self: self._last("digest"))
    saved_path = property(lambda self: self._last("saved_path"))
    completion_card = property(lambda self: self._last("completion_card", ""))
    notices = property(lambda self: self._last("notices", []))
    artwork = property(lambda self: self._last("artwork", []))
    unrelated = property(lambda self: self._last("unrelated", []))
    unreadable = property(lambda self: self._last("unreadable", []))
    failed = property(lambda self: self._last("failed", []))
    carried = property(lambda self: self._last("carried", []))
    albums = property(lambda self: self._last("albums", []))
    progress = property(lambda self: self._last("progress", []))
    digest_shown_in_conversation = property(lambda self: self._last("digest_shown_in_conversation", False))

    @property
    def tagged(self) -> list[str]:
        return [p for b in self.batches for p in b.tagged]

    @property
    def copied(self) -> list[str]:
        return [c["copy"] for b in self.batches for items in b.copies.values() for c in items]


# ---- SKILL.md parsing -----------------------------------------------------

def heading_prefix(heading: str, prefixes: set[str]) -> str | None:
    for p in prefixes:
        if heading == p or heading.startswith(p + ":") or heading.startswith(p + " "):
            return p
    return None


def load_templates(skill_md: Path = SKILL_MD) -> dict[str, Template]:
    source = skill_md.read_text(encoding="utf-8")
    commands = dict(delegate_commands(source))
    heading = ""
    index_under: dict[str, int] = {}
    templates: dict[str, Template] = {}
    prefixes = {p for (p, _) in STEP_KEYS}
    for number, line in enumerate(source.splitlines(), 1):
        if line.startswith("#"):
            heading = line
            continue
        if number not in commands:
            continue
        command = commands[number]
        prefix = heading_prefix(heading, prefixes)
        if prefix is None:
            raise DryRunError(f"delegate on line {number} is under an unmapped heading: {heading}")
        idx = index_under.get(prefix, 0)
        index_under[prefix] = idx + 1
        key = STEP_KEYS.get((prefix, idx))
        if key is None:
            raise DryRunError(f"unexpected extra delegate #{idx} under {heading}")
        target = command.split("--target", 1)[1].split()[0]
        templates[key] = Template(key, target, full_instruction(command)[1:-1], number)
    missing = set(STEP_KEYS.values()) - set(templates)
    if missing:
        raise DryRunError(f"SKILL.md lost delegates for: {sorted(missing)}")
    return templates


def digest_sections(path: Path = DIGEST_FORMAT) -> list[str]:
    text = path.read_text(encoding="utf-8")
    layout = text.split("## Fixed layout", 1)[1].split("```")[1]
    return [line[3:] for line in layout.splitlines() if line.startswith("## ")]


def shell_escape(value: str) -> str:
    """The only escape check-lib.mjs 0.7.7 accepts inside a single-quoted instruction."""
    return value.replace("'", "'\"'\"'")


def render(template: Template, values: dict[str, Any]) -> str:
    def fill(m: re.Match[str]) -> str:
        name = m.group(1)
        if name not in values or values[name] in (None, "", []):
            raise DryRunError(f"{template.key}: value {{{name}}} is missing (SKILL.md says do not run the dependent step)")
        value = values[name]
        text = "; ".join(map(str, value)) if isinstance(value, list) else str(value)
        return shell_escape(text)

    instruction = re.sub(r"\{([a-z][a-z0-9_-]*)\}", fill, template.instruction)
    command = f"delegate --target {template.target} --instruction '{instruction}'"
    tokens = shlex.split(command)
    if len(tokens) != 5 or tokens[:4] != ["delegate", "--target", template.target, "--instruction"]:
        raise DryRunError(f"{template.key}: rendered command does not parse as one delegate: {tokens[:5]}")
    return command


# ---- helpers ---------------------------------------------------------------

def name_of(path: str) -> str:
    return path.rsplit("/", 1)[-1]


def plural(n: int, word: str) -> str:
    return f"{n} {word}" + ("" if n == 1 else "s")


def classify(text: str) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) < 3 and len(text.strip()) < 40:
        return "artwork_candidate"
    lowered = text.lower()
    if any(marker in lowered for marker in SCHOOL_MARKERS):
        return "notice"
    return "unrelated"


def line_date(line: str) -> str:
    m = re.match(r"- (?:\[[ x]\] )?(?:⚠ )?(\d{4}-\d{2}-\d{2}|needs check)", line)
    return m.group(1) if m else "needs check"


def section_of(text: str, title: str) -> str:
    if f"## {title}" not in text:
        return ""
    return text.split(f"## {title}", 1)[1].split("\n## ", 1)[0]


def period_bounds(period: str) -> tuple[date, date]:
    m = re.fullmatch(r"(\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})", period.strip())
    if not m:
        raise DryRunError(f"period is not two explicit dates: {period!r}")
    return date.fromisoformat(m.group(1)), date.fromisoformat(m.group(2))


def is_digest_name(name: str) -> bool:
    return name.startswith(DIGEST_HINT) and name.endswith(".md") and not TRANSLATED_COPY.search(name)


class DryRun:
    def __init__(self, fixture: dict[str, Any], skill_md: Path = SKILL_MD, digest_format: Path = DIGEST_FORMAT) -> None:
        self.fx = copy.deepcopy(fixture)
        self.templates = load_templates(skill_md)
        self.sections = digest_sections(digest_format)
        self.inputs: dict[str, Any] = self.fx.get("inputs", {})
        self.user: dict[str, Any] = self.fx.get("user", {})
        self.experts: dict[str, Any] = self.fx.get("experts", {})
        self.llm: dict[str, Any] = self.fx.get("parent_llm", {})
        self.today = date.fromisoformat(self.fx["today"])
        self.store: dict[str, str] = {}
        self.created: dict[str, str] = {}
        for i, (path, entry) in enumerate(self.fx.get("nas_files", {}).items()):
            text = entry if isinstance(entry, str) else entry["text"]
            self.store[path] = text
            self.created[path] = entry.get("created", f"2000-01-01 00:{i:02d}") if isinstance(entry, dict) else f"2000-01-01 00:{i:02d}"
        self.keepsake_files: dict[str, set[str]] = {c: set(n) for c, n in self.fx.get("keepsake_existing", {}).items()}
        self.out = Outcome()
        self.read_this_conversation: set[str] = set()
        self.photo_dates: dict[str, str] = {}
        self.listed_newest = ""
        self.listing_cut = False
        self.prev_text: str | None = None
        self.prev_name: str | None = None
        self.prev_note = ""
        self.period_note = ""
        self.write_counter = 0

    # -- delegate with the five states --
    def response_for(self, key: str, item: str) -> dict[str, Any]:
        response = self.experts.get(key)
        if isinstance(response, dict) and "status" not in response:
            response = response.get(item)
        if isinstance(response, list):  # consumed in order, one per call (later batches, retries)
            if not response:
                raise DryRunError(f"fixture ran out of responses for {key}:{item}")
            response = response.pop(0)
        if not isinstance(response, dict) or "status" not in response:
            raise DryRunError(f"fixture has no expert response for {key}:{item}")
        return response

    def has_fixture(self, key: str, item: str) -> bool:
        response = self.experts.get(key)
        if isinstance(response, dict) and "status" not in response:
            return item in response
        return response is not None

    def delegate(self, key: str, item: str, values: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        template = self.templates[key]
        command = render(template, {**self.base_values(), **values})
        simulated = key in ("find_digest", "read_digest", "journal_query", "journal_find", "list_keepsake")
        response = self.simulated(key, item, values) if simulated and not self.has_fixture(key, item) else self.response_for(key, item)
        while True:
            status = response["status"]
            self.out.calls.append(Call(key, item, template.target, command, status))
            if status == "waiting_approval":
                self.out.approvals.append(f"{key}:{item}")
                if self.fx.get("approvals", {}).get(f"{key}:{item}", True):
                    response = response["then"]
                else:
                    self.out.messages.append(f"Approval refused for {key} {item}".strip())
                    if "denied" not in response:
                        raise DryRunError(f"{key}:{item}: approval refused but the fixture does not say what the resumed delegation returned")
                    response = response["denied"]
                continue
            if status == "waiting_user":
                self.out.questions.append(response.get("question", ""))
                response = response["then"]
                continue
            if status in ("completed", "failed", "cancelled"):
                return status, response.get("result", {}) or {}
            raise DryRunError(f"unknown status {status} for {key}:{item}")

    def folder_path(self) -> str:
        """The real NAS path of the output folder in the simulated NAS (fixture ``real_paths``, else the visible name)."""
        folder = str(self.inputs["output_folder"])
        return str(self.fx.get("real_paths", {}).get(folder, folder))

    def digests_in_folder(self, folder: str) -> list[str]:
        found = [p for p in self.store if p.startswith(folder + "/") and "/" not in p[len(folder) + 1:] and is_digest_name(name_of(p))]
        return sorted(found, key=self.digest_order)

    def digest_order(self, path: str) -> str:
        """The timestamp in the file name (YYYYMMDD_HHMMSS) first; without one, the creation time."""
        m = NAME_STAMP.search(name_of(path))
        if m:
            return f"{m.group(1)}-{m.group(2)}-{m.group(3)} {m.group(4)}:{m.group(5)}:{m.group(6)}"
        return self.created[path]

    def simulated(self, key: str, item: str, values: dict[str, Any]) -> dict[str, Any]:
        """Answers from the simulated NAS: saved digests (name timestamp, else creation time), the keepsake folder listing."""
        if key == "find_digest":
            folder = self.folder_path()
            found = self.digests_in_folder(folder)
            if not found:
                return {"status": "completed", "result": {"none": True, "folder_path": folder}}
            return {"status": "completed", "result": {"path": found[-1], "folder_path": folder}}
        if key == "read_digest":
            path = str(values["previous_digest_path"])
            if path not in self.store:
                return {"status": "failed", "result": {"reason": "file not found"}}
            return {"status": "completed", "result": {"text": self.store[path], "complete": True}}
        if key == "journal_find":
            found = self.digests_in_folder(str(values["output_folder_path"]))
            if not found:
                return {"status": "completed", "result": {"none": True}}
            return {"status": "completed", "result": {"paths": list(reversed(found))[:JOURNAL_FALLBACK_LIMIT]}}
        if key == "journal_query":
            child = str(values["child"])
            lines = [{"line": line, "file": name_of(p)} for p in self.digests_in_folder(str(values["output_folder_path"]))
                     for line in self.artwork_lines_for(self.store[p], child)]
            if not lines:
                return {"status": "completed", "result": {"none": True}}
            return {"status": "completed", "result": {"lines": lines}}
        # list_keepsake
        folder = f"{values['output_folder_path']}/Artwork - {item}"
        real = str(self.fx.get("real_paths", {}).get(folder, folder))
        names = sorted(self.keepsake_files.get(item, set()))
        return {"status": "completed", "result": {"folder_path": real, "folder_id": f"fid-{item.lower()}", "storage_type": "personal",
                                                  "files": [{"name": n, "path": f"{real}/{n}"} for n in names]}}

    @staticmethod
    def artwork_lines_for(text: str, child: str) -> list[str]:
        return [line for line in section_of(text, "Artwork").splitlines() if line.startswith("- ") and f" · {child} · " in line]

    def base_values(self) -> dict[str, Any]:
        children = [c["name"] for c in self.inputs.get("children", [])]
        return {**self.inputs, "children": children, "today": self.fx["today"]}

    def ask(self, question: str, answer_key: str, default: Any) -> Any:
        self.out.questions.append(question)
        return self.user.get(answer_key, default)

    # -- workflow --
    def run(self) -> Outcome:
        try:
            mode = self.fx.get("mode")
            if mode == "question":
                self.run_question()
            elif mode == "journal":
                self.run_journal()
            else:
                self._run()
        except Stop as stop:
            self.out.status = stop.status
            self.out.messages.append(stop.message)
            if self.out.batches and not self.out.batch.report:
                self.out.batch.report = stop.message
        if not self.out.report:
            self.out.report = self.out.batch.report if self.out.batches and self.out.batch.report else (
                self.out.messages[-1] if self.out.messages else "")
        return self.out

    def _run(self) -> None:
        self.step_inputs()
        self.step_previous_digest()
        self.step_period_and_read_back()
        photos = self.step_list()
        self.out.new_photos = self.step_tags(photos)
        continues = int(self.user.get("continue", 0))
        number = 1
        while True:
            pending = [p for p in self.out.new_photos if p not in self.read_this_conversation]
            batch = Batch(number, pending[:BATCH_SIZE], remaining=max(0, len(pending) - BATCH_SIZE))
            self.read_this_conversation.update(batch.photos)
            self.out.batches.append(batch)
            self.run_batch(batch)
            self.out.report = batch.report
            if not batch.remaining or number > continues:
                break
            self.out.questions.append("continue")
            number += 1

    def step_inputs(self) -> None:
        if not self.inputs.get("source_folder"):
            raise Stop("waiting_user", "Which NAS folder does your phone back up photos to?")
        self.inputs.setdefault("output_folder", f"{self.inputs['source_folder']}/Fridge Door")
        self.inputs.setdefault("archive_past", False)

    def step_previous_digest(self) -> None:
        """Step 1: find the newest digest by creation time, then read it by its exact path."""
        status, result = self.delegate("find_digest", "", {})
        if status == "completed" and result.get("folder_path"):
            self.inputs["output_folder_path"] = result["folder_path"]
        if status == "completed" and result.get("none"):
            return
        path = result.get("path") if status == "completed" else None
        if not path:
            self.prev_note = "I could not check for an earlier digest, so nothing was carried over."
            return
        status, result = self.delegate("read_digest", "", {"previous_digest_path": path})
        text = str(result.get("text", "")) if status == "completed" else ""
        if status != "completed" or not text:
            self.prev_note = f"I could not read {name_of(path)}, so nothing was carried over."
            return
        if result.get("complete") is not True:
            self.prev_note = f"{name_of(path)} was cut short when read, so nothing was carried over."
            return
        self.prev_text, self.prev_name = text, name_of(path)

    def next_start_of_previous(self) -> str | None:
        if not self.prev_text:
            return None
        m = re.search(re.escape(NEXT_START) + r"(\d{4}-\d{2}-\d{2})", self.prev_text.split("\n## ", 1)[0])
        return m.group(1) if m else None

    def step_period_and_read_back(self) -> None:
        origin = ""
        if not self.inputs.get("period"):
            start = self.next_start_of_previous()
            if start:
                first, origin = date.fromisoformat(start), " (where the last digest stopped)"
                if (self.today - first).days + 1 > MAX_PERIOD_DAYS:
                    raise Stop("waiting_user", f"The last digest stopped at {start}, more than {MAX_PERIOD_DAYS} days ago. "
                                               "Which period should I look at?")
                first = min(first, self.today)  # a start later than today gives today alone
                self.inputs["period"] = f"{first.isoformat()} to {self.today.isoformat()}"
            else:
                if self.prev_text:
                    self.period_note = f"{self.prev_name} gives no start date, so this run looks at the last 7 days."
                self.inputs["period"] = f"{self.today - timedelta(days=6)} to {self.today}"  # the last 7 days including today
        self.out.period = str(self.inputs["period"])
        names = " and ".join(c["name"] for c in self.inputs.get("children", [])) or "none"
        question = (f"Folder {self.inputs['source_folder']}, {self.inputs['period']}{origin}, children {names}, "
                    f"saving to {self.inputs['output_folder']}. Shall I go ahead?")
        if not self.ask(question, "proceed", True):
            raise Stop("cancelled", "Stopped before reading any photo. Nothing was created.")

    def files_of(self, result: dict[str, Any]) -> list[str]:
        files = [f for f in result.get("files", []) if f.get("path")]
        for f in files:
            self.photo_dates[f["path"]] = str(f.get("mtime") or f.get("date") or "")[:10]
        return [f["path"] for f in files]

    def step_list(self) -> list[str]:
        status, result = self.delegate("list_photos", "", {})
        fallback = False
        if status == "failed":
            self.out.messages.append("Listing by folder failed; asking photo-agent for the same folder.")
            status, result = self.delegate("list_photos_fallback", "", {})
            fallback = True
            if status == "failed":
                raise Stop("failed", f"Step 2 failed: could not list photos in {self.inputs['source_folder']}. Nothing was created.")
        if status == "cancelled":
            raise Stop("cancelled", "Stopped at Step 2. Nothing was created.")
        files = self.files_of(result)
        if result.get("none"):
            raise Stop("completed", f"No photos were found in {self.inputs['source_folder']} for {self.inputs['period']} "
                                    "(no results). Tell me another folder or period. Nothing was created.")
        if not files:
            raise Stop("failed", "Step 2 completed but returned no usable file paths, and did not say that nothing matched. "
                                 "Nothing was created.")
        output = str(self.inputs["output_folder"]) + "/"
        if any(p.startswith(output) for p in files):
            raise DryRunError("Step 2 listing contains files inside the output folder; the instruction says to leave them out")
        total = int(result.get("total", len(files)))
        if len(files) > LIST_LIMIT:
            raise DryRunError(f"listing returned {len(files)} files, more than the {LIST_LIMIT} the instruction asks for")
        if fallback and len(files) < total:
            self.out.messages.append(f"The photo expert returned {len(files)} paths of {total} matching photos.")
            self.listing_cut = True
            self.listed_newest = max(self.photo_dates[p] for p in files)
        if total > LIST_LIMIT:
            files = self.step_narrow(files, total)
        self.out.photos_found = len(files)
        self.out.total_matches = total
        return files

    def step_narrow(self, files: list[str], total: int) -> list[str]:
        self.out.messages.append(f"{total} photos match; one run looks at {LIST_LIMIT}. A folder that mostly holds school photos avoids this.")
        if not self.ask("Shall I narrow the list to papers and drawings?", "narrow", False):
            self.listing_cut = True
            self.listed_newest = max(self.photo_dates[p] for p in files)
            return files
        status, result = self.delegate("narrow_photos", "", {})
        narrowed = self.files_of(result) if status == "completed" else []
        if not narrowed:
            self.out.messages.append(f"Narrowing did not work, so this run continues with the oldest {LIST_LIMIT}.")
            self.listing_cut = True
            self.listed_newest = max(self.photo_dates[p] for p in files)
            return files
        narrowed_total = int(result.get("total", len(narrowed)))
        if narrowed_total > len(narrowed):
            self.listing_cut = True
            self.listed_newest = max(self.photo_dates[p] for p in narrowed)
        self.out.messages.append(f"Narrowed to {plural(narrowed_total, 'paper or drawing')}.")
        return narrowed

    def step_tags(self, photos: list[str]) -> list[str]:
        status, result = self.delegate("tag_lookup", "", {"photo_list": photos})
        if status == "cancelled":
            raise Stop("cancelled", "Stopped at Step 3. Nothing was created.")
        tagged: set[str] = set()
        if status == "completed" and isinstance(result.get("tagged"), list):
            tagged = set(result["tagged"])
        elif status == "completed" and (result.get("tag_exists") is False or result.get("none_carry") is True):
            tagged = set()
        else:
            question = "I could not check which photos were handled before, so photos handled before may appear again. Continue?"
            if not self.ask(question, "continue_without_tags", True):
                raise Stop("cancelled", "Stopped before reading any photo. Nothing was created.")
            self.out.messages.append("Could not check earlier runs; photos handled before may appear again.")
        self.out.already_done = [p for p in photos if p in tagged]
        new = [p for p in photos if p not in tagged]
        if self.out.already_done:
            self.out.messages.append(f"{len(self.out.already_done)} already done")
        if not new:
            deadlines, events = self.open_previous_items()
            tail = ""
            if (deadlines or events) and self.prev_name:
                tail = (f" {self.prev_name} still has {plural(len(deadlines), 'unticked deadline')} and "
                        f"{plural(len(events), 'upcoming event')}.")
            if self.listing_cut:
                newest = max(self.photo_dates.get(p, "") for p in photos)
                raise Stop("completed", f"All {len(photos)} listed photos were already handled, but {self.out.total_matches} matched. "
                                        f"Shall I look at the period from {newest}?{tail} Nothing was created.")
            raise Stop("completed", f"Nothing new in {self.inputs['period']}: all {len(photos)} photos were already handled.{tail} "
                                    "Nothing was created.")
        return new

    def open_previous_items(self) -> tuple[list[str], list[str]]:
        """Unticked deadlines and events dated today or later in the previous digest."""
        if not self.prev_text:
            return [], []
        deadlines = [line for line in section_of(self.prev_text, "Deadlines").splitlines() if line.startswith("- [ ] ")]
        events = [line for line in section_of(self.prev_text, "Events").splitlines()
                  if line.startswith("- ") and line_date(line) != "needs check" and date.fromisoformat(line_date(line)) >= self.today]
        return deadlines, events

    def run_batch(self, b: Batch) -> None:
        candidates, texts = self.step_ocr(b)
        self.step_vlm(b, candidates, texts)
        self.step_structure(b, texts)
        self.step_carry_over(b)
        if not self.step_preview(b):
            return
        self.step_copy(b)
        self.step_album(b)
        self.step_save(b)
        self.step_tag(b)
        self.step_archive(b)
        self.step_translated_copy(b)
        b.report = self.compose_report(b)
        b.completion_card = self.render_completion_card(b)

    def step_ocr(self, b: Batch) -> tuple[list[str], dict[str, str]]:
        candidates: list[str] = []
        texts: dict[str, str] = {}
        overrides: dict[str, str] = self.llm.get("classify", {})
        for i, path in enumerate(b.photos, 1):
            b.progress.append(f"Reading photos {i}/{len(b.photos)}")
            status, result = self.delegate("ocr", name_of(path), {"photo_path": path})
            if status == "cancelled":
                raise Stop("cancelled", "Stopped while reading photos. Nothing was created.")
            if status == "failed":
                candidates.append(path)
                texts[path] = ""
                continue
            text = str(result.get("text", ""))
            texts[path] = text
            kind = overrides.get(name_of(path)) or classify(text)
            if kind == "notice":
                b.notices.append({"path": path})
            elif kind == "artwork_candidate":
                candidates.append(path)
            else:
                b.unrelated.append({"path": path, "reason": str(self.llm.get("unrelated_reason", {}).get(name_of(path), "unrelated"))})
        return candidates, texts

    def step_vlm(self, b: Batch, candidates: list[str], texts: dict[str, str]) -> None:
        for path in candidates:
            status, result = self.delegate("vlm", name_of(path), {"photo_path": path})
            if status == "cancelled":
                raise Stop("cancelled", "Stopped while checking pictures. Nothing was created.")
            if status == "failed":
                b.failed.append({"path": path, "reason": str(result.get("reason", "the expert failed"))})
                b.steps.append((f"read {name_of(path)}", "failed"))
                continue
            answer = str(result.get("answer", "")).strip()
            if not re.match(r"^(YES|NO)\b", answer):
                b.unreadable.append({"path": path, "reason": "could not be read"})
                continue
            if answer.startswith("NO"):
                if not texts.get(path) and any(w in answer.lower() for w in PAPER_WORDS):
                    b.unreadable.append({"path": path, "reason": "a paper document whose text could not be read"})
                else:
                    b.unrelated.append({"path": path, "reason": "not artwork"})
                continue
            caption = re.sub(r"^YES[.,:]?\s*", "", answer)
            child, how = self.match_child(texts.get(path, ""))
            b.artwork.append({"path": path, "caption": caption, "child": child, "how": how, "note": ""})

    def match_child(self, text: str) -> tuple[str | None, str]:
        for c in self.inputs.get("children", []):
            for spelling in [c["name"], *c.get("signs_as", [])]:
                if spelling and spelling in text:
                    return c["name"], f"name read on the drawing: {spelling}"
        return None, ""

    def step_structure(self, b: Batch, texts: dict[str, str]) -> None:
        """Step 6 is done by the parent itself: no delegation, summary already in the parent language."""
        entries: dict[str, Any] = self.llm.get("notices", {})
        for notice in b.notices:
            entry = entries.get(name_of(notice["path"]))
            if entry is None:
                raise DryRunError(f"parent_llm.notices has no entry for {name_of(notice['path'])}")
            notice.update(copy.deepcopy(entry))
            for d in notice.get("dates", []):
                d["needs_check"] = not d.get("date")
                d["past"] = bool(d.get("date")) and d["role"] in ("due", "payment") and date.fromisoformat(d["date"][:10]) < self.today

    def step_carry_over(self, b: Batch) -> None:
        """Step 7, no delegation: open deadlines and upcoming events of the previous digest."""
        b.carry_note, b.period_note = self.prev_note, self.period_note
        if self.prev_note:
            b.steps.append(("carry over", "missing value"))
            return
        b.steps.append(("carry over", "completed"))
        if not self.prev_text or not self.prev_name:
            return
        b.previous_digest = self.prev_name
        current = {name_of(n["path"]) for n in b.notices}
        suffix = re.compile(r"\s·\scarried over from \S+")
        for line in section_of(self.prev_text, "Deadlines").splitlines():
            if not line.startswith("- [ ] ") or any(src in line for src in current):
                continue  # "- [x]" lines are done
            item = re.sub(r"^⚠ ", "", suffix.sub("", line[6:]).strip())
            b.carried.append(f"{item} · carried over from {b.previous_digest}")
        for line in section_of(self.prev_text, "Events").splitlines():
            if not line.startswith("- ") or any(src in line for src in current):
                continue
            when = line_date(line)
            if when == "needs check" or date.fromisoformat(when) < self.today:
                continue  # past events are dropped
            b.carried_events.append(f"{suffix.sub('', line[2:]).strip()} · carried over from {b.previous_digest}")

    def children_with_artwork(self, b: Batch) -> list[str]:
        order: list[str] = []
        for a in b.artwork:
            if a["child"] and a["child"] not in order:
                order.append(a["child"])
        return order

    def keepsake(self, child: str) -> str:
        return f"{self.inputs['output_folder']}/Artwork - {child}"

    def check_albums(self, b: Batch) -> None:
        """Step 8 album check, for each child with artwork who has not been checked yet."""
        for child in self.children_with_artwork(b):
            if child in b.albums_existing:
                continue
            album = f"Artwork - {child}"
            status, result = self.delegate("album_lookup", child, {"album_name": album, "child": child,
                                                                   "keepsake_folder": self.keepsake(child)})
            if status == "completed" and result.get("albums"):
                b.albums_existing[child] = True
            elif status == "completed" and result.get("none"):
                b.albums_existing[child] = False
            else:
                b.albums_existing[child] = None  # unknown: never create, to avoid a duplicate

    def step_preview(self, b: Batch) -> bool:
        choices: dict[str, str] = self.user.get("child_choice", {})
        for a in b.artwork:
            if a["child"] is None:
                self.out.questions.append(f"Which child made {name_of(a['path'])}?")
        self.check_albums(b)  # the children known before the preview
        b.preview = self.render_preview(b)  # the first card, before the parent answers
        if b.artwork:
            self.out.questions.append("If your child said something about a drawing, tell me and I will keep it with the picture (optional).")
        if not (b.notices or b.artwork or b.carried or b.carried_events):
            if not self.ask("Nothing school-related in this batch. Shall I save a short digest that lists these photos, "
                            "so they are not read again?", "approve_preview", True):
                b.report = f"Nothing to save in this batch: {self.other_summary(b)}. Nothing was created."
                return False
            return True
        # the parent's corrections: children chosen at the preview are checked too, then the preview is shown again
        notes: dict[str, str] = self.user.get("child_notes", {})
        corrected = False
        for a in b.artwork:
            if a["child"] is None and name_of(a["path"]) in choices:
                a["child"], a["how"] = choices[name_of(a["path"])], "chosen by the parent"
                corrected = True
            a["note"] = notes.get(name_of(a["path"]), "")  # kept exactly as the parent wrote it
        if corrected or self.user.get("done_items"):
            self.check_albums(b)
            b.preview_again = self.render_preview(b)
        if not self.ask("Shall I copy the drawings, create the albums, save the digest and tag the handled photos?",
                        "approve_preview", True):
            b.digest = self.render_digest(b)
            b.digest_shown_in_conversation = True
            raise Stop("cancelled", "You declined the preview, so here is the digest text in the chat. Nothing was created.")
        return True

    def step_output_folder(self, b: Batch) -> bool:
        """Step 9, first delegation: the real path of the output folder, before anything is copied or saved."""
        status, result = self.delegate("ensure_folder", "", {})
        if status != "completed" or not result.get("path"):
            b.steps.append(("output folder", status if status != "completed" else "missing value"))
            self.inputs.pop("output_folder_path", None)
            return False
        b.steps.append(("output folder", "completed"))
        self.inputs["output_folder_path"] = str(result["path"])
        return True

    def step_copy(self, b: Batch) -> None:
        if not self.step_output_folder(b):
            for child in self.children_with_artwork(b):
                b.steps.append((f"copy drawings for {child}", "not run"))
            return
        folder_path = str(self.inputs["output_folder_path"])
        for child in self.children_with_artwork(b):
            paths = [a["path"] for a in b.artwork if a["child"] == child]
            status, result = self.delegate("copy_artwork", child, {"child": child, "output_folder_path": folder_path,
                                                                   "child_artwork_paths": paths})
            if status != "completed":
                b.steps.append((f"copy drawings for {child}", status))
                continue
            existing = self.keepsake_files.setdefault(child, set())
            reported = list(result.get("not_copied", []))
            same = {name_of(c["src"]) for c in reported if "exist" in str(c.get("reason", ""))}
            if result.get("copied") == "all":
                same |= {name_of(p) for p in paths if name_of(p) in existing}
                existing |= {name_of(p) for p in paths}
            else:
                existing |= {name_of(c["src"]) for c in result.get("copied", []) if isinstance(c, dict) and c.get("src")}
            b.steps.append((f"copy drawings for {child}", "completed"))
            # Step 9: the folder listing decides what is in the keepsake folder; the copy may report counts only
            status, listing = self.delegate("list_keepsake", child, {"child": child, "output_folder_path": folder_path})
            if status != "completed" or not listing.get("files"):
                b.steps.append((f"read keepsake folder for {child}", status if status != "completed" else "missing value"))
                continue
            b.steps.append((f"read keepsake folder for {child}", "completed"))
            if listing.get("folder_path"):
                b.keepsake_paths[child] = str(listing["folder_path"])
            if listing.get("folder_id"):
                b.keepsake_ids[child] = str(listing["folder_id"])
            if listing.get("storage_type"):
                b.keepsake_types[child] = str(listing["storage_type"])
            listed = {str(f["name"]): str(f["path"]) for f in listing["files"]}
            b.copies[child] = [{"src": p, "copy": listed[name_of(p)]} for p in paths if name_of(p) in listed and name_of(p) not in same]
            b.same_name[child] = [p for p in paths if name_of(p) in listed and name_of(p) in same]
            missing = [p for p in paths if name_of(p) not in listed]
            b.not_copied[child] = [{"src": p, "reason": next((c.get("reason", "") for c in reported if c.get("src") == p), "")}
                                   for p in missing]
            for p in missing:
                b.steps.append((f"copy {name_of(p)}", "missing value"))

    def step_album(self, b: Batch) -> None:
        for child in self.children_with_artwork(b):
            album = f"Artwork - {child}"
            existing = b.albums_existing.get(child)
            if existing:
                b.album_notes[child] = "already existed, new copies appear in it after indexing"
                continue
            if not b.copies.get(child):
                b.album_notes[child] = "not created, no copy was made"
                b.steps.append((f"album {album}", "not run"))
                continue
            if existing is None:
                b.album_notes[child] = "not created, could not check whether it exists"
                b.steps.append((f"album {album}", "not run"))
                continue
            if not (b.keepsake_paths.get(child) and b.keepsake_ids.get(child) and b.keepsake_types.get(child)):
                b.album_notes[child] = "not created, the folder path, id or storage type was not returned"
                b.steps.append((f"album {album}", "not run"))
                continue
            status, result = self.delegate("create_album", child, {"album_name": album, "keepsake_folder_path": b.keepsake_paths[child],
                                                                   "keepsake_folder_id": b.keepsake_ids[child],
                                                                   "keepsake_storage_type": b.keepsake_types[child]})
            if status == "completed" and result.get("album_id"):
                b.albums.append({"name": album, "id": result["album_id"], "count": int(result.get("count", 0)), "child": child})
                b.album_notes[child] = "created"
                b.steps.append((f"album {album}", "completed"))
            elif status == "completed":
                b.album_notes[child] = "not created, the folder could not be used as the album rule"
                b.steps.append((f"album {album}", "missing value"))
            else:
                b.album_notes[child] = f"not created ({status})"
                b.steps.append((f"album {album}", status))

    def in_keepsake(self, b: Batch) -> list[str]:
        return [c["src"] for items in b.copies.values() for c in items] + [p for items in b.same_name.values() for p in items]

    def planned_tags(self, b: Batch) -> list[str]:
        """What Step 12 tags after a verified save: every photo the digest lists, except drawings not copied."""
        listed = self.in_keepsake(b) + [n["path"] for n in b.notices] + [u["path"] for u in b.unrelated] + [u["path"] for u in b.unreadable]
        return [p for p in b.photos if p in set(listed)]

    def untagged_after(self, b: Batch) -> list[str]:
        """Photos of this run that no batch tags: left for later, failed, drawings not copied, in this batch or an earlier one."""
        handled = {p for earlier in self.out.batches if earlier is not b for p in earlier.handled} | set(self.planned_tags(b))
        return [p for p in self.out.new_photos if p not in handled]

    def compute_next_start(self, b: Batch) -> str:
        dates = [self.photo_dates.get(p, "") for p in self.untagged_after(b)]
        if self.listing_cut and self.listed_newest:
            dates.append(self.listed_newest)
        dates = [d for d in dates if d]
        if dates:
            return min(dates)
        return period_bounds(str(self.inputs["period"]))[1].isoformat()  # the last day; the tag keeps that day's photos from a second read

    def step_save(self, b: Batch) -> None:
        b.next_start = self.compute_next_start(b)
        b.digest = self.render_digest(b)
        if not any(name == "output folder" and state == "completed" for name, state in b.steps):
            b.steps.append(("save digest", "not run"))
            b.digest_shown_in_conversation = True
            return
        status, result = self.delegate("save_digest", "", {"digest_text": b.digest, "output_folder_path": self.inputs["output_folder_path"]})
        if status == "completed" and result.get("path") and result.get("verified"):
            b.saved_path = str(result["path"])
            self.write_counter += 1
            self.store[b.saved_path] = b.digest
            self.created[b.saved_path] = f"{self.fx.get('generated_at', self.today.isoformat())}#{self.write_counter:03d}"
            self.prev_text, self.prev_name, self.prev_note = b.digest, name_of(b.saved_path), ""
            b.steps.append(("save digest", "completed"))
        else:
            b.steps.append(("save digest", status if status != "completed" else "missing value"))
            b.digest_shown_in_conversation = True

    def step_tag(self, b: Batch) -> None:
        # without a verified save nothing is tagged; copies already made come back next run as same-name items
        b.handled = self.planned_tags(b) if b.saved_path else []
        if not b.handled:
            b.steps.append(("tag", "not run"))
            return
        status, result = self.delegate("tag_add", "", {"handled_paths": b.handled})
        if status == "completed" and "tagged" in result:
            # fixture shorthand "all": the expert reports every requested file as tagged
            b.tagged = list(b.handled) if result["tagged"] == "all" else list(result["tagged"])
            b.steps.append(("tag", "completed" if set(b.tagged) >= set(b.handled) else "missing value"))
        else:
            b.steps.append(("tag", status if status != "completed" else "missing value"))
        untagged = [p for p in b.handled if p not in set(b.tagged)]
        if untagged:
            self.out.messages.append(f"Not tagged: {', '.join(name_of(p) for p in untagged)}. The saved digest already starts the next run "
                                     "after them; if you rerun this period explicitly, these photos will be read again.")

    def past_notice_paths(self, b: Batch) -> list[str]:
        return [n["path"] for n in b.notices if any(d.get("past") for d in n.get("dates", []))]

    def archive_folder(self) -> str:
        return f"{self.inputs['output_folder']}/Archive {self.today:%Y-%m}"

    def step_archive(self, b: Batch) -> None:
        if not self.inputs.get("archive_past"):
            return
        past = self.past_notice_paths(b)
        if not past:
            return
        folder = self.archive_folder()
        if not self.ask(f"Move {len(past)} past notice photo(s) to {folder}?", "archive_yes", False):
            return
        status, result = self.delegate("archive", "", {"archive_folder": folder, "past_notice_paths": past, "year-month": f"{self.today:%Y-%m}"})
        if status == "completed" and "moved" in result:
            b.archived = list(result["moved"])
            b.steps.append(("archive", "completed"))
        else:
            b.steps.append(("archive", status if status != "completed" else "missing value"))

    def step_translated_copy(self, b: Batch) -> None:
        if not self.inputs.get("copy_language"):
            return
        if not b.saved_path:
            b.steps.append(("translated copy", "not run"))
            return
        status, result = self.delegate("translate_copy", "", {"saved_path": b.saved_path})
        if status == "completed" and result.get("path"):
            b.translated_copy = str(result["path"])
            self.store[b.translated_copy] = "(translated copy)"
            self.created[b.translated_copy] = f"{self.fx.get('generated_at', self.today.isoformat())}#{self.write_counter:03d}z"
            b.steps.append(("translated copy", "completed"))
        else:
            b.steps.append(("translated copy", status if status != "completed" else "missing value"))

    # -- question mode (needs only the output folder) --
    def output_folder_only(self, question: str) -> None:
        if not self.inputs.get("output_folder"):
            if not self.inputs.get("source_folder"):
                raise Stop("waiting_user", question)
            self.inputs["output_folder"] = f"{self.inputs['source_folder']}/Fridge Door"

    def run_question(self) -> None:
        self.output_folder_only("Which folder holds your Fridge Door digests?")
        status, result = self.delegate("find_digest", "", {})
        if status == "completed" and result.get("none"):
            self.out.answer = (f"I found no saved digest in {self.inputs['output_folder']}. "
                               "Shall I sort this week's photos?")
            self.out.report = self.out.answer
            return
        path = result.get("path") if status == "completed" else None
        if not path:
            self.out.answer = "I could not check for a saved digest, so I cannot answer from it."
            self.out.report = self.out.answer
            return
        status, result = self.delegate("read_digest", "", {"previous_digest_path": path})
        text = str(result.get("text", "")) if status == "completed" else ""
        if not text:
            self.out.answer = f"I could not read {name_of(path)}."
            self.out.report = self.out.answer
            return
        keywords = [k.lower() for k in self.llm.get("question_keywords", [])]
        hits = [line for title in ("Deadlines", "Events") for line in section_of(text, title).splitlines()
                if line.startswith("- ") and any(k in line.lower() for k in keywords)]
        if hits:
            body = "\n".join(re.sub(r"^- (\[[ x]\] )?", "- ", h) for h in hits)
            self.out.answer = f"From {name_of(path)}:\n{body}"
        else:
            self.out.answer = f"{name_of(path)} does not mention that."
        if result.get("complete") is not True:
            self.out.answer += "\nThe digest was cut short when read, so this answer may be incomplete."
        self.out.report = self.out.answer

    # -- artwork journal (needs only the output folder and the child) --
    def run_journal(self) -> None:
        self.output_folder_only("Which folder holds your Fridge Door digests?")
        child = self.inputs.get("child")
        if not child:
            raise Stop("waiting_user", "Whose art journal should I make?")
        status, result = self.delegate("find_digest", "", {})
        folder = result.get("folder_path") if status == "completed" else None
        if not folder:
            raise Stop("completed", f"I could not find the folder {self.inputs['output_folder']}, so there is no journal. Nothing was created.")
        self.inputs["output_folder_path"] = folder
        values = {"output_folder_path": folder, "child": child}
        status, result = self.delegate("journal_query", "", values)
        lines: list[dict[str, str]] = []
        for name in result.get("not_read_in_full", []) if status == "completed" else []:
            self.out.messages.append(f"{name} was not read in full, so its lines may be missing.")
        if status == "completed" and not result.get("cannot_read_markdown"):
            if result.get("lines"):
                lines = list(result["lines"])
            elif not result.get("none"):
                raise Stop("completed", "The document expert gave no lines and did not say that none was found. Nothing was created.")
        else:
            lines = self.journal_fallback(values)
        if not lines:
            raise Stop("completed", f"No artwork lines for {child} were found in the saved digests. Nothing was created.")
        self.out.journal = self.render_journal(str(child), lines)
        self.out.answer = self.out.journal
        if not self.ask("Shall I save this journal next to the digests?", "save_journal", False):
            self.out.report = "Journal shown in the chat. Nothing was created."
            return
        status, result = self.delegate("journal_save", "", {"journal_text": self.out.journal, "output_folder_path": folder})
        if status == "completed" and result.get("path") and result.get("verified"):
            self.out.journal_path = str(result["path"])
            self.out.report = f"Saved the journal · {self.out.journal_path}"
        else:
            self.out.report = "The journal was not saved; its text is shown above."

    def journal_fallback(self, values: dict[str, Any]) -> list[dict[str, str]]:
        status, result = self.delegate("journal_find", "", values)
        paths = list(result.get("paths", []))[:JOURNAL_FALLBACK_LIMIT] if status == "completed" else []
        self.out.messages.append(f"The document expert could not read the digests, so I checked only the {len(paths)} most recent digests "
                                 f"(at most {JOURNAL_FALLBACK_LIMIT}).")
        lines: list[dict[str, str]] = []
        for path in paths[:JOURNAL_FALLBACK_LIMIT]:
            status, read = self.delegate("read_digest", name_of(path), {"previous_digest_path": path})
            if status == "completed" and read.get("text"):
                lines += [{"line": line, "file": name_of(path)} for line in self.artwork_lines_for(str(read["text"]), str(values["child"]))]
        return lines

    def render_journal(self, child: str, lines: list[dict[str, str]]) -> str:
        entries = []
        for item in lines:
            parts = item["line"][2:].split(" · ")
            source, when = parts[0], parts[2] if len(parts) > 2 else "needs check"
            caption = parts[3] if len(parts) > 3 else ""
            said = next((p for p in parts if p.startswith("Said: ")), "")
            folder = f"{self.inputs['output_folder']}/Artwork - {child}"
            entries.append((when, f"- {when} · {caption}" + (f" · {said}" if said else "") + f" · {source} · {folder} · from {item['file']}"))
        entries.sort()
        return "\n".join([f"# Artwork journal - {child}", f"{entries[0][0]} to {entries[-1][0]}", "", *[e for _, e in entries]]) + "\n"

    # -- rendering --
    def deadline_lines(self, b: Batch) -> list[str]:
        done = set(self.user.get("done_items", []))
        rows: list[str] = []
        for n in b.notices:
            for d in n.get("dates", []):
                if d["role"] not in ("due", "payment"):
                    continue
                when = d.get("date") or "needs check"
                flag = f"{PAST_MARK} " if d.get("past") else ""
                child = n.get("child") or "all children"
                action = n["action"] + (f", {n['amount']}" if n.get("amount") else "")
                box = "[x]" if name_of(n["path"]) in done else "[ ]"
                rows.append(f"- {box} {flag}{when} — {action} · {child} · \"{d['quoted']}\" · {name_of(n['path'])}")
        for item in b.carried:
            when = line_date(f"- [ ] {item}")
            past = when != "needs check" and date.fromisoformat(when) < self.today
            box = "[x]" if any(src in item for src in done) else "[ ]"
            rows.append(f"- {box} {PAST_MARK + ' ' if past else ''}{item}")
        return sorted(rows, key=line_date)

    def open_deadlines(self, b: Batch) -> list[str]:
        return [line for line in self.deadline_lines(b) if line.startswith("- [ ] ")]

    def next_due(self, b: Batch) -> str | None:
        return next((line[6:] for line in self.open_deadlines(b) if line_date(line) != "needs check" and PAST_MARK not in line[:9]), None)

    def event_lines(self, b: Batch) -> list[str]:
        out = []
        for n in b.notices:
            for d in n.get("dates", []):
                if d["role"] == "event":
                    child = n.get("child") or "all children"
                    out.append((d.get("date") or "needs check", f"- {d.get('date') or 'needs check'} — {n['title']} · {child} · "
                                                                 f"\"{d['quoted']}\" · {name_of(n['path'])}"))
        out += [(line_date(f"- {e}"), f"- {e}") for e in b.carried_events]
        return [line for _, line in sorted(out)]

    def artwork_by_child(self, b: Batch) -> dict[str, list[dict[str, Any]]]:
        groups: dict[str, list[dict[str, Any]]] = {}
        for a in b.artwork:
            groups.setdefault(a["child"] or "Child not chosen", []).append(a)
        return groups

    def copy_state(self, b: Batch, a: dict[str, Any]) -> str:
        child = a["child"]
        if not child:
            return "not copied, child not chosen"
        if any(c["src"] == a["path"] for c in b.copies.get(child, [])):
            return "copied"
        if a["path"] in b.same_name.get(child, []):
            return "already in the folder (same name), not copied"
        reason = next((c.get("reason", "") for c in b.not_copied.get(child, []) if c.get("src") == a["path"]), "")
        return f"not copied, {reason}" if reason else "not copied"

    def artwork_line(self, b: Batch, a: dict[str, Any]) -> str:
        parts = [name_of(a["path"]), a["child"] or "child not chosen", self.photo_dates.get(a["path"], "") or "needs check", a["caption"]]
        if a.get("note"):
            parts.append(f"Said: \"{a['note']}\"")
        parts += [a["how"] or "child not chosen", self.copy_state(b, a)]
        if not a["child"]:
            parts = parts[:-2] + [parts[-1]]
        return "- " + " · ".join(parts)

    def run_status_line(self, b: Batch) -> str:
        bad = [f"{name} ({state})" for name, state in b.steps if state != "completed"]
        if bad:
            return "- Run status when saved: Partly done before saving: " + "; ".join(bad) + "."
        return "- Run status when saved: every step before saving completed."

    def other_summary(self, b: Batch) -> str:
        parts = [f"{name_of(u['path'])} ({u['reason']})" for u in b.unrelated]
        parts += [f"{name_of(u['path'])} (could not be read)" for u in b.unreadable]
        parts += [f"{name_of(u['path'])} (failed)" for u in b.failed]
        return ", ".join(parts) or "no photos"

    def render_digest(self, b: Batch) -> str:
        deadlines = self.deadline_lines(b)
        open_lines = [line for line in deadlines if line.startswith("- [ ] ")]
        past = sum(1 for line in open_lines if line.startswith(f"- [ ] {PAST_MARK} "))
        events = self.event_lines(b)
        groups = self.artwork_by_child(b)
        counts = ", ".join(f"{child} {len(items)}" for child, items in groups.items())
        nxt = self.next_due(b)
        carried = f", {len(b.carried)} carried over" if b.carried else ""
        carried_ev = f" ({len(b.carried_events)} carried over)" if b.carried_events else ""
        folders = ", ".join(f"Artwork - {c} ({len(b.copies.get(c, []))} copied)" for c in self.children_with_artwork(b)) or "none"
        albums = ", ".join(f"Artwork - {c} ({b.album_notes.get(c, 'planned')})" for c in self.children_with_artwork(b)) or "none"
        needs = [f"- {name_of(u['path'])}: {u['reason']}" for u in b.unreadable]
        needs += [f"- {name_of(u['path'])}: the expert failed ({u['reason']}); it will be read again next run" for u in b.failed]
        needs += [f"- {name_of(n['path'])}: date needs check" for n in b.notices if any(d["needs_check"] for d in n.get("dates", []))]
        needs += [f"- {name_of(a['path'])}: child not chosen" for a in b.artwork if not a["child"]]
        needs += [f"- {note}" for note in (b.carry_note, b.period_note) if note]
        artwork_lines: list[str] = []
        for child, items in groups.items():
            artwork_lines.append(f"### {child}")
            if child != "Child not chosen":
                artwork_lines.append(f"Keepsake folder: {self.keepsake(child)} · album Artwork - {child}: {b.album_notes.get(child, 'planned')}")
            artwork_lines += [self.artwork_line(b, a) for a in items]
        body: dict[str, list[str]] = {
            "At a glance": [
                f"- Next due: {nxt}" if nxt else "- Next due: none",
                f"- {plural(len(open_lines), 'deadline')} ({past} past{carried}), {plural(len(events), 'event')}{carried_ev}, "
                f"{plural(len(b.artwork), 'artwork')}" + (f" ({counts})" if counts else ""),
                f"- {plural(len(b.unrelated), 'photo')} left untouched, {len(self.out.already_done)} already handled on earlier runs, "
                f"{b.remaining} left for the next batch",
                f"- Keepsake folders: {folders}",
                f"- Albums: {albums}",
            ],
            "Deadlines": deadlines or ["No deadlines this time."],
            "Events": events or ["No events this time."],
            "Notices": ["| Source | Original key line | Summary | Due | Action |", "|---|---|---|---|---|"] + [
                f"| {name_of(n['path'])} | {n['key_line']} | {n['summary']} | "
                f"{next((d.get('date') or 'needs check' for d in n.get('dates', [])), '')} | {n['type']} |" for n in b.notices]
            if b.notices else ["No notices this time."],
            "Artwork": artwork_lines or ["No artwork this time."],
            "Needs your check": needs or ["Nothing to check this time."],
            "Left untouched and run details": [
                "- Left untouched: " + (", ".join(f"{name_of(u['path'])} ({u['reason']})" for u in b.unrelated) or "none"),
                "- Already handled on earlier runs: " + (", ".join(name_of(p) for p in self.out.already_done) or "none"),
                f"- Left for the next batch: {b.remaining or 'none'}",
                self.run_status_line(b),
                self.archive_line(b),
            ],
        }
        if list(body) != self.sections:
            raise DryRunError(f"digest renderer sections {list(body)} differ from digest-format.md {self.sections}")
        parts = [f"# Fridge Door – {self.inputs['period']}",
                 f"Source: {self.inputs['source_folder']} · {plural(len(b.photos), 'photo')} read · "
                 f"Generated on NAS {self.fx.get('generated_at', self.today.isoformat())} · {NEXT_START}{b.next_start or self.compute_next_start(b)}"]
        for title in self.sections:
            parts.append(f"\n## {title}\n" + "\n".join(body[title]))
        return "\n".join(parts) + "\n"

    def archive_line(self, b: Batch) -> str:
        past = self.past_notice_paths(b)
        if self.inputs.get("archive_past") and past:
            names = ", ".join(name_of(p) for p in past)
            return f"- To be moved after approval: {names} into {self.archive_folder()}"
        return "- Originals were not moved or deleted."

    def notice_line(self, n: dict[str, Any]) -> str:
        dates = n.get("dates", [])
        main = next((d for d in dates if d["role"] != "event"), dates[0] if dates else {})
        when = main.get("date") or "needs check"
        if main.get("past"):
            when = f"{PAST_MARK} {when} (past)"
        action = n["action"] + (f", {n['amount']}" if n.get("amount") else "")
        return f"- {name_of(n['path'])} · {n['title']} · {when} · {action} · {n.get('child') or 'all children'}"

    @staticmethod
    def first_date(notice: dict[str, Any]) -> str:
        return next((d.get("date") or "9999" for d in notice.get("dates", [])), "9999")

    def render_preview(self, b: Batch) -> str:
        """The preview card of SKILL.md Step 8, as first shown (before the parent answers). Empty parts are left out."""
        out = self.out
        lines = [f"{plural(len(b.photos), 'photo')} read. Please check before I save anything.",
                 f"{plural(out.photos_found, 'photo')} found · {len(out.already_done)} already done · "
                 f"{len(b.photos)} in this batch · {b.remaining} left for later",
                 f"{self.inputs['source_folder']} · {self.inputs['period']}"]
        for a in b.artwork:
            if not a["child"]:
                lines.append(f"Check needed · {name_of(a['path'])}: I could not tell whose drawing this is. Which child made it?")
        for u in b.unreadable:
            lines.append(f"Check needed · {name_of(u['path'])}: could not be read. Please retake the photo if it matters.")
        for u in b.failed:
            lines.append(f"Check needed · {name_of(u['path'])}: the photo expert failed; I will try it again next run.")
        if b.notices:
            lines += ["", f"School notices ({len(b.notices)})"]
            lines += [self.notice_line(n) for n in sorted(b.notices, key=self.first_date)]
        carried = [line[6:] for line in self.deadline_lines(b) if "carried over from" in line]
        carried += [line[2:] for line in self.event_lines(b) if "carried over from" in line]
        if carried:
            lines += ["", f"Carried over ({len(carried)})"] + [f"- {c}" for c in carried]
        if b.artwork:
            lines += ["", f"Artwork ({len(b.artwork)})"]
            lines += [f"- {name_of(a['path'])} · {a['child'] or 'unknown, please tell me'} · {a['caption']}" for a in b.artwork]
            lines.append("If your child said something about a drawing, tell me and I will keep it with the picture (optional).")
        other = [f"- {name_of(u['path'])} · {u['reason']} · left untouched" for u in b.unrelated]
        other += [f"- {name_of(u['path'])} · could not be read" for u in b.unreadable + b.failed]
        if other:
            lines += ["", f"Not related / unreadable ({len(other)})"] + other
        lines.append("")
        known = self.children_with_artwork(b)
        for child in known:
            n = sum(1 for a in b.artwork if a["child"] == child)
            lines.append(f"Will copy: {plural(n, 'drawing')} into {self.keepsake(child)} "
                         "(new copies, so a drawing can show twice in UGREEN Photos)")
            existing = b.albums_existing.get(child)
            if existing:
                lines.append(f"Album Artwork - {child} exists: the new copies will appear in it")
            elif existing is False:
                lines.append(f"Will create: album Artwork - {child}, which follows its keepsake folder")
            else:
                lines.append(f"Album Artwork - {child}: could not check, so I will not create one")
        if any(not a["child"] for a in b.artwork):
            lines.append("Drawings whose child you tell me are copied into that child's keepsake folder the same way")
        lines.append(f"Will save: a new digest in {self.inputs['output_folder']} · tag the photos it lists {TAG}")
        past = self.past_notice_paths(b)
        if self.inputs.get("archive_past") and past:
            lines.append(f"Will move after you agree: {plural(len(past), 'past notice photo')} into {self.archive_folder()}")
            lines.append("Apart from that move, originals stay where they are; nothing is deleted. "
                         "Proceed? (yes / or correct, e.g. 'IMG_0107 is Jun's' or 'the fee is already paid')")
        else:
            lines.append("Originals stay where they are; nothing is moved or deleted. "
                         "Proceed? (yes / or correct, e.g. 'IMG_0107 is Jun's' or 'the fee is already paid')")
        return "\n".join(lines)

    def is_done(self, b: Batch) -> bool:
        return all(state == "completed" for _, state in b.steps)

    def render_completion_card(self, b: Batch) -> str:
        """The completion card of SKILL.md Step 15, built only from real results."""
        open_lines = self.open_deadlines(b)
        head = "Done." if self.is_done(b) else "Partly done."
        lines = [f"{head} {plural(len(open_lines), 'deadline')}, {plural(len(self.event_lines(b)), 'event')}, "
                 f"{plural(len(b.artwork), 'artwork')}."]
        nxt = self.next_due(b)
        if nxt:
            m = re.match(r"(\S+) — (.+?) · (.+?) · \"[^\"]*\" · (\S+)", nxt)
            if m:
                lines.append("Next due: " + " · ".join(m.groups()))
        lines.append("Created:")
        for child, items in b.copies.items():
            if items:
                lines.append(f"- {len(items)} {'copy' if len(items) == 1 else 'copies'} in {b.keepsake_paths.get(child, self.keepsake(child))}")
        for album in b.albums:
            lines.append(f"- Album '{album['name']}' · {plural(int(album['count']), 'photo')} · id {album['id']}")
        if b.saved_path:
            lines.append(f"- Saved digest · {b.saved_path}")
        else:
            lines.append("- Digest was not saved; its text is shown above")
        if b.tagged:
            lines.append(f"- Tagged {plural(len(b.tagged), 'photo')} {TAG}")
        if b.translated_copy:
            lines.append(f"- Translated copy · {b.translated_copy}")
        if head == "Partly done.":
            failed = [f"{name} ({state})" for name, state in b.steps if state in ("failed", "cancelled", "missing value", "incomplete read")]
            waiting = [name for name, state in b.steps if state.startswith("waiting")]
            blocked = [name for name, state in b.steps if state == "not run"]
            lines.append("Not done:")
            lines.append("- Failed or cancelled: " + (", ".join(failed) or "none"))
            lines.append("- Waiting: " + (", ".join(waiting) or "none"))
            lines.append("- Not run because an earlier step did not complete: " + (", ".join(blocked) or "none"))
        status = []
        if self.out.already_done:
            status.append(f"{len(self.out.already_done)} already done")
        status.append(f"Left untouched {len(b.unrelated)}" + (f" ({', '.join(u['reason'] for u in b.unrelated)})" if b.unrelated else ""))
        status.append(f"Unreadable {len(b.unreadable)}")
        if b.failed:
            status.append(f"Failed {len(b.failed)}")
        status.append(f"{b.remaining} left for later")
        status.append(f"Moved {plural(len(b.archived), 'past notice photo')}" if b.archived else "Originals were not moved or deleted")
        status.append("This Skill asked only the NAS experts; the AI model they use is the one the NAS owner set up")
        lines.append(" · ".join(status))
        return "\n".join(lines)

    def compose_report(self, b: Batch) -> str:
        return self.render_completion_card(b).splitlines()[0]


def run_fixture(fixture: dict[str, Any]) -> Outcome:
    return DryRun(fixture).run()


def transcript(outcome: Outcome) -> str:
    lines = [f"status: {outcome.status}", "", "## Delegations"]
    lines += [f"{i}. [{c.status}] {c.command}" for i, c in enumerate(outcome.calls, 1)]
    lines += ["", "## Questions to the user"] + [f"- {q}" for q in outcome.questions]
    for b in outcome.batches:
        lines += ["", f"# Batch {b.number}"]
        if b.progress:
            lines += ["", "## Progress", *b.progress]
        if b.preview:
            lines += ["", "## Preview", b.preview]
        if b.preview_again:
            lines += ["", "## Preview after the corrections", b.preview_again]
        if b.digest:
            lines += ["", "## Digest", b.digest]
        if b.completion_card:
            lines += ["", "## Completion card", b.completion_card]
    if outcome.answer:
        lines += ["", "## Answer", outcome.answer]
    lines += ["", "## Report", outcome.report]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args(argv)
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    try:
        print(transcript(run_fixture(fixture)))
    except DryRunError as error:
        print(f"dry run error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
