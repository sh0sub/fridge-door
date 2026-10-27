#!/usr/bin/env python3
"""Dry run of the fridge-door workflow against simulated expert responses (fixtures).

The Skill is executed on the NAS by the Uliya parent agent (a local LLM). There is no NAS
here, so this harness plays both sides deterministically:

* Expert side: every delegate answer (file list, tags, OCR text, vision answer, album id,
  saved path, ...) comes from a JSON fixture. Formats of real answers are unknown (catalog
  returnSummary is "unknown"), so fixtures use a minimal shape. (미확인: 실호출로 확인 필요)
* Parent side: follows SKILL.md step by step. The delegate commands are taken verbatim from
  SKILL.md and every {value} is filled from upstream results, so a missing value, a leftover
  brace or broken shell quoting fails the run. Judgement calls the parent LLM would make
  (structuring a notice) are also fixture data under "parent_llm"; the rule-based parts
  (sorting, past flag, child matching, tagging only completed items) are computed here.

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
from datetime import date
from pathlib import Path
from typing import Any

from scripts.check import delegate_commands, full_instruction

ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = ROOT / "fridge-door" / "SKILL.md"
DIGEST_FORMAT = ROOT / "fridge-door" / "references" / "digest-format.md"
MAX_PHOTOS = 12
CONDENSE_WORDS = 400
SCHOOL_MARKERS = ("학교", "가정통신문", "학부모", "담임", "회신", "준비물", "납부", "school", "class", "parents", "teacher", "pta")

# (heading prefix, index of the delegate under that heading) -> step key
STEP_KEYS = {
    ("## Step 1", 0): "list_photos",
    ("## Step 1", 1): "list_photos_fallback",
    ("## Step 2", 0): "tag_lookup",
    ("## Step 3", 0): "ocr",
    ("## Step 4", 0): "vlm",
    ("## Step 5", 0): "condense",
    ("### Translation", 0): "translate",
    ("### Child fallback", 0): "figure_lookup",
    ("### Carry over open items", 0): "previous_digest",
    ("## Step 6", 0): "album_lookup",
    ("## Step 7", 0): "create_album",
    ("## Step 7", 1): "create_album_fallback",
    ("## Step 8", 0): "save_digest",
    ("## Step 9", 0): "tag_add",
    ("## Step 10", 0): "archive",
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
class Outcome:
    status: str = "completed"
    calls: list[Call] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)
    approvals: list[str] = field(default_factory=list)
    preview: str | None = None
    digest: str | None = None
    digest_shown_in_conversation: bool = False
    saved_path: str | None = None
    albums: list[dict[str, Any]] = field(default_factory=list)
    tagged: list[str] = field(default_factory=list)
    archived: list[str] = field(default_factory=list)
    report: str = ""
    notices: list[dict[str, Any]] = field(default_factory=list)
    artwork: list[dict[str, Any]] = field(default_factory=list)
    unrelated: list[dict[str, str]] = field(default_factory=list)
    unreadable: list[dict[str, str]] = field(default_factory=list)
    carried: list[str] = field(default_factory=list)
    already_done: list[str] = field(default_factory=list)

    def calls_for(self, key: str) -> list[Call]:
        return [c for c in self.calls if c.key == key]


# ---- SKILL.md parsing -----------------------------------------------------

def load_templates(skill_md: Path = SKILL_MD) -> dict[str, Template]:
    source = skill_md.read_text(encoding="utf-8")
    lines = source.splitlines()
    commands = dict(delegate_commands(source))
    heading = ""
    index_under: dict[str, int] = {}
    templates: dict[str, Template] = {}
    for number, line in enumerate(lines, 1):
        if line.startswith("## ") or line.startswith("### "):
            heading = line
            continue
        if number not in commands:
            continue
        command = commands[number]
        prefix = next((p for (p, _) in STEP_KEYS if heading == p or heading.startswith(p + ":") or heading == p), None)
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
    return value.replace("'", "'\\''")


def render(template: Template, values: dict[str, Any]) -> str:
    def fill(m: re.Match[str]) -> str:
        name = m.group(1)
        if name not in values or values[name] in (None, "", []):
            raise DryRunError(f"{template.key}: value {{{name}}} is missing (SKILL.md says stop the dependent step)")
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


def period_end(period: str) -> date:
    dates = re.findall(r"\d{4}-\d{2}-\d{2}", period)
    if not dates:
        raise DryRunError(f"period without ISO dates: {period}")
    return date.fromisoformat(dates[-1])


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
        self.out = Outcome()

    # -- delegate with the five states --
    def delegate(self, key: str, item: str, values: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        template = self.templates[key]
        command = render(template, {**self.base_values(), **values})
        response = self.experts.get(key)
        if isinstance(response, dict) and item and item in response:
            response = response[item]
        if not isinstance(response, dict) or "status" not in response:
            raise DryRunError(f"fixture has no expert response for {key}:{item}")
        while True:
            status = response["status"]
            self.out.calls.append(Call(key, item, template.target, command, status))
            if status == "waiting_approval":
                self.out.approvals.append(f"{key}:{item}")
                if not self.fx.get("approvals", {}).get(f"{key}:{item}", True):
                    self.out.messages.append(f"Approval denied for {key} {item}".strip())
                    return "cancelled", {}
                response = response["then"]
                continue
            if status == "waiting_user":
                self.out.questions.append(response.get("question", ""))
                response = response["then"]
                continue
            if status in ("completed", "failed", "cancelled"):
                return status, response.get("result", {}) or {}
            raise DryRunError(f"unknown status {status} for {key}:{item}")

    def base_values(self) -> dict[str, Any]:
        children = [c["name"] for c in self.inputs.get("children", [])]
        return {k: v for k, v in {**self.inputs, "children": children, "today": self.fx["today"]}.items()}

    def ask(self, question: str, answer_key: str, default: Any) -> Any:
        self.out.questions.append(question)
        return self.user.get(answer_key, default)

    # -- workflow --
    def run(self) -> Outcome:
        try:
            self._run()
        except Stop as stop:
            self.out.status = stop.status
            self.out.messages.append(stop.message)
        if not self.out.report:
            self.out.report = self.out.messages[-1] if self.out.messages else ""
        return self.out

    def _run(self) -> None:
        self.step_inputs()
        photos = self.step_list()
        new = self.step_tags(photos)
        candidates, ocr = self.step_ocr(new)
        self.step_vlm(candidates, ocr)
        self.step_structure(ocr)
        self.step_child_fallback()
        self.step_carry_over()
        albums = self.step_preview()
        self.step_albums(albums)
        self.step_save()
        self.step_tag()
        self.step_archive()
        self.out.report = self.compose_report()

    def step_inputs(self) -> None:
        if not self.inputs.get("source_folder"):
            raise Stop("waiting_user", "Which NAS folder does your phone back up photos to?")
        self.inputs.setdefault("output_folder", f"{self.inputs['source_folder']}/Fridge Door")
        self.inputs.setdefault("archive_past", False)
        names = " and ".join(c["name"] for c in self.inputs.get("children", [])) or "none"
        question = (f"Folder {self.inputs['source_folder']}, {self.inputs['period']}, children {names}, "
                    f"saving to {self.inputs['output_folder']}. Shall I go ahead?")
        if not self.ask(question, "proceed", True):
            raise Stop("cancelled", "Stopped before reading any photo. Nothing was created.")

    def step_list(self) -> list[dict[str, Any]]:
        status, result = self.delegate("list_photos", "", {})
        if status == "failed":
            self.out.messages.append("Listing by folder failed; asking photo-agent for the same folder.")
            status, result = self.delegate("list_photos_fallback", "", {})
            if status == "failed":
                raise Stop("failed", f"Step 1 failed: could not list photos in {self.inputs['source_folder']}.")
        if status == "cancelled":
            raise Stop("cancelled", "Stopped at Step 1. Nothing was created.")
        files: list[dict[str, Any]] = result.get("files", [])
        total = int(result.get("total", len(files)))
        if total == 0 or not files:
            raise Stop("completed", f"No photos were found in {self.inputs['source_folder']} for {self.inputs['period']} "
                                    "(no results). Tell me another folder or period. Nothing was created.")
        if total > MAX_PHOTOS:
            raise Stop("waiting_user", f"{total} photos match {self.inputs['period']}; one run handles up to {MAX_PHOTOS}. "
                                       "Please give me a shorter period.")
        return files

    def step_tags(self, photos: list[dict[str, Any]]) -> list[str]:
        paths = [p["path"] for p in photos]
        status, result = self.delegate("tag_lookup", "", {"photo_list": paths})
        if status == "cancelled":
            raise Stop("cancelled", "Stopped at Step 2. Nothing was created.")
        tagged = set(result.get("tagged", [])) if status == "completed" else set()
        if status == "failed":
            self.out.messages.append("Could not check earlier runs; photos handled before may appear again.")
        self.out.already_done = [p for p in paths if p in tagged]
        new = [p for p in paths if p not in tagged]
        if self.out.already_done:
            self.out.messages.append(f"{len(self.out.already_done)} already done")
        if not new:
            raise Stop("completed", f"Nothing new in {self.inputs['period']}: all {len(paths)} photos were already handled. "
                                    "Nothing was created.")
        return new

    def step_ocr(self, new: list[str]) -> tuple[list[str], dict[str, str]]:
        candidates: list[str] = []
        texts: dict[str, str] = {}
        overrides: dict[str, str] = self.llm.get("classify", {})
        for path in new:
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
                self.out.notices.append({"path": path})
            elif kind == "artwork_candidate":
                candidates.append(path)
            else:
                self.out.unrelated.append({"path": path, "reason": str(self.llm.get("unrelated_reason", {}).get(name_of(path), "unrelated"))})
        return candidates, texts

    def step_vlm(self, candidates: list[str], texts: dict[str, str]) -> None:
        for path in candidates:
            status, result = self.delegate("vlm", name_of(path), {"photo_path": path})
            if status == "cancelled":
                raise Stop("cancelled", "Stopped while checking pictures. Nothing was created.")
            answer = str(result.get("answer", "")).strip()
            if status == "failed" or not re.match(r"^(YES|NO)\b", answer):
                self.out.unreadable.append({"path": path, "reason": "could not be read"})
                continue
            if answer.startswith("NO"):
                self.out.unrelated.append({"path": path, "reason": "not artwork"})
                continue
            caption = re.sub(r"^YES[.,:]?\s*", "", answer)
            child, how = self.match_child(texts.get(path, ""))
            self.out.artwork.append({"path": path, "caption": caption, "child": child, "how": how})

    def match_child(self, text: str) -> tuple[str | None, str]:
        for c in self.inputs.get("children", []):
            for spelling in [c["name"], *c.get("signs_as", [])]:
                if spelling and spelling in text:
                    return c["name"], f"name read on the drawing: {spelling}"
        return None, ""

    def step_structure(self, texts: dict[str, str]) -> None:
        entries: dict[str, Any] = self.llm.get("notices", {})
        language = str(self.inputs.get("parent_language", ""))
        for notice in self.out.notices:
            path = notice["path"]
            text = texts[path]
            if len(text.split()) > CONDENSE_WORDS:
                status, result = self.delegate("condense", name_of(path), {"ocr_text": text})
                if status == "completed":
                    text = str(result.get("text", text))
            entry = entries.get(name_of(path))
            if entry is None:
                raise DryRunError(f"parent_llm.notices has no entry for {name_of(path)}")
            notice.update(copy.deepcopy(entry))
            for d in notice.get("dates", []):
                d["needs_check"] = not d.get("date")
                d["past"] = bool(d.get("date")) and d["role"] in ("due", "payment") and date.fromisoformat(d["date"][:10]) < self.today
            notice["translated"] = None
            if language and notice.get("language") and notice["language"] != language:
                status, result = self.delegate("translate", name_of(path), {"notice_summary": notice["summary"]})
                if status == "completed":
                    notice["translated"] = str(result.get("text", ""))
                else:
                    notice["translated"] = "translation unavailable"
                    self.out.messages.append(f"Translation unavailable for {name_of(path)}; kept the original summary.")

    def step_child_fallback(self) -> None:
        unknown = [a for a in self.out.artwork if a["child"] is None]
        if not unknown:
            return
        if self.inputs.get("children"):
            status, result = self.delegate("figure_lookup", "", {"unknown_artwork": [a["path"] for a in unknown]})
            matches: dict[str, str] = result.get("matches", {}) if status == "completed" else {}
            for a in unknown:
                if a["path"] in matches:
                    a["child"], a["how"] = matches[a["path"]], "people album"
        choices: dict[str, str] = self.user.get("child_choice", {})
        for a in self.out.artwork:
            if a["child"] is None:
                self.out.questions.append(f"Which child made {name_of(a['path'])}?")
                if name_of(a["path"]) in choices:
                    a["child"], a["how"] = choices[name_of(a["path"])], "chosen by the parent"

    def step_carry_over(self) -> None:
        status, result = self.delegate("previous_digest", "", {})
        text = str(result.get("text", "")) if status == "completed" else ""
        if not text:
            return
        title = text.splitlines()[0].lstrip("# ").strip()
        deadlines = text.split("## Deadlines", 1)[1].split("\n## ", 1)[0] if "## Deadlines" in text else ""
        current = {name_of(n["path"]) for n in self.out.notices}
        for line in deadlines.splitlines():
            if not line.startswith("- [ ] "):
                continue  # "- [x]" lines count as done
            if any(src in line for src in current):
                continue
            item = re.sub(r"\s·\scarried over from [^·]+", "", line[6:]).strip()
            self.out.carried.append(f"{item} · carried over from {title}")

    def planned_albums(self) -> list[dict[str, Any]]:
        albums: list[dict[str, Any]] = []
        end = period_end(str(self.inputs["period"]))
        if self.out.notices:
            albums.append({"name": f"School notices {end:%Y-%m}", "paths": [n["path"] for n in self.out.notices]})
        by_child: dict[str, list[str]] = {}
        for a in self.out.artwork:
            if a["child"]:
                by_child.setdefault(a["child"], []).append(a["path"])
        for child, paths in by_child.items():
            albums.append({"name": f"Artwork – {child} {end:%Y}", "paths": paths})
        return albums

    def step_preview(self) -> list[dict[str, Any]]:
        albums = self.planned_albums()
        for album in albums:
            status, result = self.delegate("album_lookup", album["name"], {"album_name": album["name"]})
            existing = result.get("albums", []) if status == "completed" else []
            album["existing"] = bool(existing)
            if existing:
                album["add_to_existing"] = self.ask(f"An album named {album['name']} already exists. Add the photos to it?",
                                                    "add_to_existing", True)
        self.out.preview = self.render_preview(albums)
        if not self.ask("Shall I create these albums, save the digest and tag the handled photos?", "approve_preview", True):
            self.out.digest = self.render_digest()
            self.out.digest_shown_in_conversation = True
            raise Stop("cancelled", "You declined the preview, so here is the digest text in the conversation. Nothing was created.")
        return albums

    def step_albums(self, albums: list[dict[str, Any]]) -> None:
        for album in albums:
            if album.get("existing") and not album.get("add_to_existing", True):
                album["status"] = "cancelled"
                continue
            status, result = self.delegate("create_album", album["name"], {"album_name": album["name"], "album_paths": album["paths"]})
            if status == "failed" and self.ask(
                    f"Adding photos by path failed. The fallback album {album['name']} would hold every photo of "
                    f"{self.inputs['period']} in {self.inputs['source_folder']}. Use it?", "use_album_fallback", False):
                status, result = self.delegate("create_album_fallback", album["name"], {"album_name": album["name"]})
            album["status"] = status
            if status == "completed":
                album["id"] = result.get("album_id")
                album["count"] = result.get("count")
                self.out.albums.append(album)
            elif status == "cancelled":
                if f"create_album:{album['name']}" not in self.out.approvals:
                    raise Stop("cancelled", self.created_so_far("Album creation was cancelled."))
                if not self.ask("The album was not created. Continue with saving the digest only?", "continue_without_albums", True):
                    raise Stop("cancelled", self.created_so_far("Stopped after the declined album."))
            else:
                self.out.messages.append(f"Album {album['name']} failed: {result.get('reason', 'no reason given')}")

    def step_save(self) -> None:
        self.out.digest = self.render_digest()
        period = str(self.inputs["period"])
        status, result = self.delegate("save_digest", "", {"digest_text": self.out.digest, "period": period})
        if status == "completed" and result.get("path"):
            self.out.saved_path = str(result["path"])
        elif status == "cancelled" and "save_digest:" not in self.out.approvals:
            raise Stop("cancelled", self.created_so_far("Saving was cancelled."))
        else:
            self.out.digest_shown_in_conversation = True
            self.out.messages.append("The digest could not be saved; here is its text in the conversation.")

    def step_tag(self) -> None:
        handled: list[str] = []
        for album in self.out.albums:
            handled += album["paths"]
        if self.out.saved_path:
            handled += [n["path"] for n in self.out.notices] + [a["path"] for a in self.out.artwork]
        handled = sorted(set(handled))
        if not handled:
            return
        status, result = self.delegate("tag_add", "", {"handled_paths": handled})
        if status == "completed":
            self.out.tagged = list(result.get("tagged", handled))
        else:
            self.out.messages.append("Tagging failed; the next run may show these photos again.")

    def step_archive(self) -> None:
        if not self.inputs.get("archive_past"):
            return
        past = self.past_notice_paths()
        if not past:
            return
        folder = self.archive_folder()
        if not self.ask(f"Move {len(past)} past notice photo(s) to {folder}?", "archive_yes", False):
            return
        status, result = self.delegate("archive", "", {"archive_folder": folder, "past_notice_paths": past})
        if status == "completed":
            self.out.archived = list(result.get("moved", past))
        else:
            self.out.messages.append(f"Archive step ended as {status}; the photos stay where they are.")

    # -- rendering --
    def deadlines(self) -> list[tuple[str, str]]:
        rows: list[tuple[str, str]] = []
        for n in self.out.notices:
            for d in n.get("dates", []):
                if d["role"] not in ("due", "payment"):
                    continue
                when = d.get("date") or "needs check"
                flags = " · past" if d.get("past") else ""
                child = n.get("child") or "all children"
                rows.append((when, f"- [ ] {when} — {n['action']} · {child} · \"{d['quoted']}\" · {name_of(n['path'])}{flags}"))
        rows.sort(key=lambda r: r[0])
        return rows

    def events(self) -> list[str]:
        out = []
        for n in self.out.notices:
            for d in n.get("dates", []):
                if d["role"] == "event":
                    child = n.get("child") or "all children"
                    out.append((d.get("date") or "needs check", f"- {d.get('date') or 'needs check'} — {n['title']} · {child} · "
                                                                 f"\"{d['quoted']}\" · {name_of(n['path'])}"))
        return [line for _, line in sorted(out)]

    def artwork_by_child(self) -> dict[str, list[dict[str, Any]]]:
        groups: dict[str, list[dict[str, Any]]] = {}
        for a in self.out.artwork:
            groups.setdefault(a["child"] or "Child not chosen", []).append(a)
        return groups

    def render_digest(self) -> str:
        deadlines = self.deadlines()
        past = sum(1 for _, line in deadlines if line.endswith(" · past"))
        events = self.events()
        groups = self.artwork_by_child()
        counts = ", ".join(f"{child} {len(items)}" for child, items in groups.items())
        nxt = next((line for when, line in deadlines if when != "needs check" and not line.endswith(" · past")), None)
        albums = ", ".join(f"{a['name']} ({a.get('count', len(a['paths']))} photos)" for a in self.out.albums) or "none created"
        needs = [f"- {name_of(u['path'])}: {u['reason']}" for u in self.out.unreadable]
        needs += [f"- {name_of(n['path'])}: date needs check" for n in self.out.notices if any(d["needs_check"] for d in n.get("dates", []))]
        needs += [f"- {name_of(a['path'])}: child not chosen" for a in self.out.artwork if not a["child"]]
        body: dict[str, list[str]] = {
            "At a glance": [
                f"- Next due: {nxt[6:]}" if nxt else "- Next due: none",
                f"- {plural(len(deadlines) + len(self.out.carried), 'deadline')} ({past} past), {plural(len(events), 'event')}, "
                f"{plural(len(self.out.artwork), 'artwork')}" + (f" ({counts})" if counts else ""),
                f"- {plural(len(self.out.unrelated), 'photo')} left untouched, {len(self.out.already_done)} already handled on earlier runs",
                f"- Albums: {albums}",
            ],
            "Deadlines": [line for _, line in deadlines] + [f"- [ ] {c}" for c in self.out.carried] or ["No deadlines this time."],
            "Events": events or ["No events this time."],
            "Notices": ["| Source | Original key line | Summary | Due | Action |", "|---|---|---|---|---|"] + [
                f"| {name_of(n['path'])} | {n['key_line']} | {self.summary_cell(n)} | "
                f"{next((d.get('date') or 'needs check' for d in n.get('dates', [])), '')} | {n['type']} |" for n in self.out.notices]
            if self.out.notices else ["No notices this time."],
            "Artwork": [line for child, items in groups.items()
                        for line in [f"### {child}"] + [f"- {name_of(a['path'])} — {a['caption']} ({a['how'] or 'child not chosen'})"
                                                        for a in items]] or ["No artwork this time."],
            "Needs your check": needs or ["Nothing to check this time."],
            "Left untouched and run details": [
                "- Left untouched: " + (", ".join(f"{name_of(u['path'])} ({u['reason']})" for u in self.out.unrelated) or "none"),
                "- Already handled on earlier runs: " + (", ".join(name_of(p) for p in self.out.already_done) or "none"),
                f"- Albums created: {albums}",
                *[f"- {m}" for m in self.out.messages if "denied" in m or "failed" in m or "unavailable" in m],
                self.archive_line(),
            ],
        }
        if list(body) != self.sections:
            raise DryRunError(f"digest renderer sections {list(body)} differ from digest-format.md {self.sections}")
        parts = [f"# Fridge Door – {self.inputs['period']}"]
        for title in self.sections:
            parts.append(f"\n## {title}\n" + "\n".join(body[title]))
        return "\n".join(parts) + "\n"

    @staticmethod
    def summary_cell(notice: dict[str, Any]) -> str:
        if notice.get("translated") == "translation unavailable":
            return f"{notice['summary']} (translation unavailable)"
        return str(notice.get("translated") or notice["summary"])

    def past_notice_paths(self) -> list[str]:
        return [n["path"] for n in self.out.notices if any(d.get("past") for d in n.get("dates", []))]

    def archive_folder(self) -> str:
        return f"{self.inputs['source_folder']}/Fridge Door/Archive {self.today:%Y-%m}"

    def archive_line(self) -> str:
        past = self.past_notice_paths()
        if self.inputs.get("archive_past") and past:
            names = ", ".join(name_of(p) for p in past)
            return f"- To be moved after approval: {names} into {self.archive_folder()}"
        return "- Originals were not moved or deleted."

    def render_preview(self, albums: list[dict[str, Any]]) -> str:
        lines = ["Preview (nothing has been created yet):"]
        lines += [line for _, line in self.deadlines()] + [f"- [ ] {c}" for c in self.out.carried]
        lines += self.events()
        for n in self.out.notices:
            if n.get("translated"):
                due = next((d.get("date") or "needs check" for d in n.get("dates", [])), "")
                lines.append(f"[{n['key_line']} / {n['translated']} / {due} / {n['action']}]")
        for a in self.out.artwork:
            lines.append(f"Artwork {name_of(a['path'])}: {a['caption']} — {a['child'] or 'which child?'}")
        lines += [f"Left alone: {name_of(u['path'])} ({u['reason']})" for u in self.out.unrelated]
        lines += [f"Could not read: {name_of(u['path'])}" for u in self.out.unreadable]
        lines += [f"Will create album {a['name']} ({len(a['paths'])} photos)" for a in albums]
        lines.append(f"Will save Fridge Door – {self.inputs['period']}.md in {self.inputs['output_folder']} and tag handled photos.")
        lines.append("Nothing will be moved or deleted.")
        return "\n".join(lines)

    def created_so_far(self, prefix: str) -> str:
        made = [f"album {a['name']}" for a in self.out.albums]
        return f"{prefix} Already created: {', '.join(made) if made else 'nothing'}. Nothing more will be created."

    def compose_report(self) -> str:
        deadlines = self.deadlines()
        past = sum(1 for _, line in deadlines if line.endswith(" · past"))
        upcoming = [(when, n) for when, n in self.deadline_items() if not n["past"]]
        groups = self.artwork_by_child()
        parts = [plural(len(deadlines), "deadline") + (f" ({past} past)" if past else "")]
        if upcoming:
            when, item = upcoming[0]
            parts[0] += f" (earliest: {item['action']}, {when[5:7]}/{when[8:10]})"
        parts.append(plural(len(self.events()), "event"))
        parts.append(plural(len(self.out.artwork), "artwork") + (" (" + ", ".join(
            f"{c}" if len(groups) == 1 else f"{c} {len(i)}" for c, i in groups.items()) + ")" if groups else ""))
        text = ", ".join(parts) + "."
        if self.out.albums:
            text += " Albums: " + ", ".join(f"{a['name']} ({a['count']})" for a in self.out.albums) + "."
        if self.out.saved_path:
            text += f" Digest saved to {self.out.saved_path}."
        elif self.out.digest_shown_in_conversation:
            text += " The digest was not saved; its text is shown above."
        if self.out.unrelated:
            reasons = ", ".join(u["reason"] for u in self.out.unrelated)
            text += f" {plural(len(self.out.unrelated), 'photo')} left untouched ({reasons})."
        if self.out.already_done:
            text += f" {len(self.out.already_done)} already done."
        if self.out.unreadable:
            text += " Could not read: " + ", ".join(name_of(u["path"]) for u in self.out.unreadable) + "."
        return text

    def deadline_items(self) -> list[tuple[str, dict[str, Any]]]:
        items = []
        for n in self.out.notices:
            for d in n.get("dates", []):
                if d["role"] in ("due", "payment") and d.get("date"):
                    items.append((d["date"], {"action": n["action"], "past": d["past"]}))
        return sorted(items, key=lambda x: x[0])


def run_fixture(fixture: dict[str, Any]) -> Outcome:
    return DryRun(fixture).run()


def transcript(outcome: Outcome) -> str:
    lines = [f"status: {outcome.status}", "", "## Delegations"]
    lines += [f"{i}. [{c.status}] {c.command}" for i, c in enumerate(outcome.calls, 1)]
    lines += ["", "## Questions to the user"] + [f"- {q}" for q in outcome.questions]
    if outcome.preview:
        lines += ["", "## Preview", outcome.preview]
    if outcome.digest:
        lines += ["", "## Digest", outcome.digest]
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
