#!/usr/bin/env python3
"""Static checker for the fridge-door Uliya Skill package.

Two layers:

1. ``official``: a line-by-line Python port of ``scripts/check-lib.mjs`` from
   uliya-skill-kit 0.7.7 (CHECK_FORMAT_VERSION 2.0.0, capability catalog
   structure 2.2.0). Diagnostic codes, severities and status values are kept
   identical so results can be compared with
   ``node uliya-skill-kit/scripts/check-skill.mjs fridge-door``.
   The official kit is not vendored here (its catalog licence is unclear); it
   was read as untrusted data and never executed. Pass the kit's
   ``data/capability-catalog.json`` with ``--catalog`` to validate it with the
   same ownership contract as ``loadCatalogContract()`` and to take the
   CLI-to-agent map for the evidence check from it.
2. ``plan``: extra rules from docs/plan.md (submission checklist, {value} lint,
   forbidden-term grep, body length target, references set, evidence set).

Usage:
    python3 scripts/check.py fridge-door            # both layers, JSON on stdout
    python3 scripts/check.py fridge-door --official # official port only
    python3 scripts/check.py fridge-door --catalog path/to/capability-catalog.json

Exit code: 0 when there are no errors, 1 when there are errors, 2 on usage errors.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

CHECK_FORMAT_VERSION = "2.0.0"
CATALOG_VERSION = "2.2.0"

SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SKILL_NAME_MIN = 2
SKILL_NAME_MAX = 64
DESCRIPTION_MAX = 1024
SINGLE_FILE_MAX_BYTES = 1024 * 1024
PACKAGE_MAX_BYTES = 10 * 1024 * 1024
PACKAGE_MAX_FILES = 100
SKILL_BODY_RECOMMENDED_LINES = 500

FULL_PROFILE_CLI_AGENTS: dict[str, str] = {
    "ug-music": "media-agent",
    "ug-video": "media-agent",
    "ug-surveillance": "security-monitor-agent",
    "ug-filesystem": "file-agent",
    "ug-filemgr": "file-agent",
    "file-workflow": "file-agent",
    "ug-document": "document-agent",
    "ug-knowledge": "knowledge-agent",
    "ug-photo": "photo-agent",
}
ALLOWED_AGENTS = set(FULL_PROFILE_CLI_AGENTS.values())
REQUIRED_STATUS_TOKENS = ["completed", "failed", "cancelled", "waiting_user", "waiting_approval"]

# JS regexes without the `u` flag use ASCII \b and \w, hence re.ASCII. JS \s is still Unicode-aware
# (NBSP, U+2000-U+200A, U+3000, BOM, ...), while Python's \s under re.ASCII is not, so every kit pattern
# is compiled with js_re(), which writes \s and \S out as the explicit JS whitespace class.
A = re.ASCII
I = re.IGNORECASE
JS_WHITESPACE = "\t\n\v\f\r \u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff"
JS_WHITESPACE_CHARS = "\t\n\v\f\r \u00a0\u1680" + "".join(map(chr, range(0x2000, 0x200B))) + "\u2028\u2029\u202f\u205f\u3000\ufeff"


def js_pattern(pattern: str) -> str:
    r"""Rewrite \s and \S in a regex source so they match exactly what JavaScript's \s matches."""
    out: list[str] = []
    in_class = False
    i = 0
    while i < len(pattern):
        ch = pattern[i]
        if ch == "\\" and i + 1 < len(pattern):
            nxt = pattern[i + 1]
            if nxt == "s":
                out.append(JS_WHITESPACE if in_class else f"[{JS_WHITESPACE}]")
            elif nxt == "S" and in_class:
                if pattern[i - 2:i] != "\\s":
                    raise ValueError(f"\\S inside a character class is only supported as [\\s\\S]: {pattern}")
                out.append("\\S")  # [\s\S] (written out) still matches any character
            elif nxt == "S":
                out.append(f"[^{JS_WHITESPACE}]")
            else:
                out.append(ch + nxt)
            i += 2
            continue
        if ch == "[" and not in_class:
            in_class = True
        elif ch == "]" and in_class and out and out[-1] not in ("[", "[^"):
            in_class = False
        out.append(ch)
        i += 1
    return "".join(out)


def js_re(pattern: str, flags: int = 0) -> re.Pattern[str]:
    return re.compile(js_pattern(pattern), flags)


def js_trim(value: str) -> str:
    """String.prototype.trim(): strips JS whitespace and line terminators only."""
    return value.strip(JS_WHITESPACE_CHARS)


PRIVATE_KEY = js_re(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", A)
CREDENTIAL_ASSIGNMENT = js_re(
    r"\b(?:password|passwd|token|api[_-]?key|secret)\s*[:=]\s*[\"'][^\"'\n]+[\"']", A | I
)
REMOTE_DOWNLOAD = js_re(r"\b(?:curl|wget)\b|https?://\S+\s*\|\s*(?:sh|bash)\b", A | I)
RUNTIME_FENCE = js_re(
    r"^```\s*(?:bash|sh|shell|python|py|javascript|js|node|typescript|ts)\b", A | I
)
DIRECT_FILE_API = js_re(
    r"\b(?:readFile|writeFile|unlink|pathlib|fs\.|open\s*\(|cp\s+|mv\s+|rm\s+|cat\s+)\b", A | I
)
HTTP_CALL = js_re(
    r"\b(?:fetch|axios|XMLHttpRequest|http\.request|https\.request)\s*\(", A | I
)
NAS_PATH = js_re(r"(?:^|[\s\"'])/(?:nas|mnt|volume\d*|shares?)(?:/|\b)", A | I)
BYPASS = js_re(
    r"\b(?:bypass|skip|disable|ignore|绕过|跳过|关闭)\b[^\n]{0,40}"
    r"\b(?:gateway|approval|permission|audit|审批|权限|审计)\b",
    A | I,
)
DESCRIPTION_TRIGGER = js_re(
    r"(?:当用户|用户(?:说|问|要|需要|希望|要求|提到)|适用于|使用于|用于|供[^，。;；]{1,40}使用|when\b|use when\b)",
    A | I,
)
DESCRIPTION_SPLIT = js_re(r"(?:当用户|用户(?:说|问|要|需要|希望|要求|提到)|when\b|use when\b)", A | I)
DESCRIPTION_EXECUTION_DETAIL = js_re(
    r"(?:先[^，。;；]{0,24}(?:再|然后)|保存到|存到|输出到|按[^，。;；]{0,20}(?:排序|分组|归档)|不要|不得|不删除|只报告)"
)
DESCRIPTION_IMPERATIVE = js_re(r"^\s*(?:生成|创建|整理出|产出|输出|汇总出|做一份|出一份)")
HARDCODED_HOME = js_re(
    r"/home/(?!<|\{|\$|某个?用户|用户名|user(?:name)?\b)[A-Za-z0-9._-]+(?:/|\b)", A | I
)
UNRESOLVED_DYNAMIC_VALUE = js_re(
    r"<[^>\n]{1,80}>|(?:该路径|该目录|上一步(?:的)?(?:路径|目录|结果|文件|文本|内容|ID|标识)|刚才(?:的)?(?:结果|路径|目录|内容))",
    I,
)
QUERY_INTENT = js_re(
    r"(?:查询|查找|搜索|筛选|扫描|盘点|检索|列出|浏览|query|search|find|scan|filter|list|report)", I
)
EMPTY_RESULT_HANDLING = js_re(
    r"(?:空结果|空列表|空集合|无结果|无匹配(?:结果|项)?|没有匹配|没有找到|未找到|目录为空|返回为空|no results?|empty (?:result|list|set)|zero matches?)",
    I,
)
INTERNAL_CAPABILITY = js_re(
    r"\b(?:ug-ai|HERMES(?:\s+action)?|Host CLI|expert[-_ ]?id|correlation[-_ ]?id|request[-_ ]?id)\b", A | I
)
COMPACT_PROFILE = js_re(r"\b(?:compact-main-agent|compact-unified-agent|compact profile)\b", A | I)
CLI_INVOKE = js_re(r"\bcli\.invoke\b", A)
CLI_INVOKE_NEGATED = js_re(
    r"(?:不|不要|不得|禁止|避免)[^\n]{0,24}(?:直接)?(?:执行|调用|使用)?\s*`?cli\.invoke\b"
    r"|(?:do not|don't|never|must not|without)[^\n]{0,24}\bcli\.invoke\b",
    A | I,
)
DELEGATE_CHAINING = js_re(r"\$\(|`[^`]+`|\|\||&&|\s[|<>]\s", A)
TARGET_ARG = js_re(r"(?:^|\s)--target(?:\s+(\S+))?", A)
INSTRUCTION_ARG = js_re(r"(?:^|\s)--instruction(?:\s+('(?:[^']|'\"'\"')*'|\"[^\"]*\"|\S+))?", A)
EXTRA_FLAG = js_re(r"\s--(?!target\b|instruction\b)[a-z0-9-]+", A | I)
SINGLE_QUOTED = js_re(r"^'(?:[^']|'\"'\"')*'$", A)
REAL_RESULT = js_re(r"(真实|real)[^\n]{0,40}(结果|result)|上一步|upstream|下游|downstream", A | I)
REFERENCE_LINK = js_re(r"\]\((references/[A-Za-z0-9._/-]+\.md)(?:#[^)\s]+)?\)")
EVIDENCE_HEADING = js_re(r"^# (?:生成期能力依据|Generation-time capability evidence)\s*$", re.M | I)
NEXT_HEADING = js_re(r"^#\s+", re.M)
EVIDENCE_LINE = js_re(r"^\s*-\s+`([a-z][a-z0-9-]*)`\s+→\s+`([a-z][a-z0-9-]*)`\s*$", re.M | A)
PLACEHOLDER = js_re(r"replace-with-|\bTODO\b|\bTBD\b|待定", A)
FRONTMATTER = js_re(r"^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|\Z)")
REQUIRED_SECTIONS = [
    (js_re(r"^# (?:目标|Goal)\s*$", re.M | I), "目标"),
    (js_re(r"^# (?:必需输入|Required input)\s*$", re.M | I), "必需输入"),
    (js_re(r"^# (?:专家编排|Workflow|Orchestration)\s*$", re.M | I), "专家编排"),
    (js_re(r"^# (?:完成与失败|Failure handling|Completion and failure)\s*$", re.M | I), "完成与失败"),
]

# ---- plan.md extras -------------------------------------------------------
# Submission checklist grep, verbatim (case-sensitive substring search):
# grep -nE "curl|wget|cat |cp |mv |rm |/nas|/volume|/mnt|/share|request-id|TODO|TBD|<[^>]{1,80}>"
PLAN_FORBIDDEN = re.compile(
    r"curl|wget|cat |cp |mv |rm |/nas|/volume|/mnt|/share|request-id|TODO|TBD|<[^>]{1,80}>"
)
PLAN_BODY_LINES_TARGET = 300
PLAN_REFERENCES = (
    "references/README.md",
    "references/digest-format.md",
    "references/disclosures.md",
    "references/test-plan.md",
)
PLAN_EVIDENCE = {
    "ug-filesystem": "file-agent",
    "ug-filemgr": "file-agent",
    "file-workflow": "file-agent",
    "ug-photo": "photo-agent",
    "ug-document": "document-agent",
    "ug-knowledge": "knowledge-agent",
}
VALUE_TOKEN = re.compile(r"\{([A-Za-z][A-Za-z0-9_-]*)\}")
VALUE_NAME = re.compile(r"^[a-z][a-z0-9_-]*$")
VAGUE_REFERENCE = re.compile(
    r"\b(?:that (?:folder|file|path|album|photo|list)|the (?:previous|earlier|last) (?:result|step|path|folder|output)"
    r"|the (?:folder|file|path) (?:above|before)|the same (?:folder|path)|from before)\b",
    A | I,
)
# check-lib.mjs accepts only the '"'"' sequence inside a single-quoted instruction.
QUOTE_ESCAPES = ("'\"'\"'",)


def diagnostic(code: str, severity: str, message: str, suggestion: str, **location: Any) -> dict[str, Any]:
    return {"code": code, "severity": severity, **location, "message": message, "suggestion": suggestion}


def line_for_offset(source: str, offset: int) -> int:
    return len(re.split(r"\r?\n", source[: max(0, offset)]))


def line_count(value: str) -> int:
    if not value:
        return 0
    return len(re.split(r"\r?\n", re.sub(r"\r?\n\Z", "", value)))


def sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def sort_diagnostics(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for item in items:
        key = "|".join(str(item.get(k, "")) for k in ("code", "severity", "file", "line", "path", "message"))
        seen.setdefault(key, item)
    big = sys.maxsize
    return sorted(
        seen.values(),
        key=lambda d: (d.get("file") or "", d.get("line") if d.get("line") is not None else big, d["code"]),
    )


def finalize(target: dict[str, Any], files: list[dict[str, str]], diagnostics: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sort_diagnostics(diagnostics)
    summary = {
        "errors": sum(1 for d in ordered if d["severity"] == "error"),
        "warnings": sum(1 for d in ordered if d["severity"] == "warning"),
        "info": sum(1 for d in ordered if d["severity"] == "info"),
    }
    if summary["errors"]:
        status = "not-uploadable"
    elif summary["warnings"]:
        status = "static-pass-needs-target-validation"
    else:
        status = "static-pass"
    return {
        "checkFormatVersion": CHECK_FORMAT_VERSION,
        "status": status,
        "target": target,
        "catalog": {"checkedVersion": CATALOG_VERSION},
        "files": sorted(files, key=lambda f: f["path"]),
        "summary": summary,
        "diagnostics": ordered,
    }


def validate_catalog(catalog_path: Path) -> dict[str, str]:
    """Same ownership contract as loadCatalogContract() in check-lib.mjs 0.7.7; the catalog is untrusted JSON.

    Returns the CLI -> agent map read from the catalog.
    """
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    if not isinstance(catalog, dict) or not isinstance(catalog.get("catalogVersion"), str) \
            or not isinstance(catalog.get("clis"), list):
        raise ValueError("capability catalog has an invalid structure")
    if catalog["catalogVersion"] != CATALOG_VERSION:
        raise ValueError(f"capability catalog version must be {CATALOG_VERSION}")
    seen: dict[str, str] = {}
    for cli in catalog["clis"]:
        name = cli.get("name") if isinstance(cli, dict) else None
        agent = cli.get("agent") if isinstance(cli, dict) else None
        if not isinstance(name, str) or not isinstance(agent, str):
            raise ValueError("capability catalog has an invalid CLI ownership contract")
        if agent not in ALLOWED_AGENTS:
            raise ValueError("capability catalog references an unsupported full-profile subagent")
        if FULL_PROFILE_CLI_AGENTS.get(name) != agent:
            raise ValueError("capability catalog has an invalid full-profile CLI ownership mapping")
        if name in seen:
            raise ValueError("capability catalog has duplicate CLI names")
        seen[name] = agent
    if len(seen) != len(FULL_PROFILE_CLI_AGENTS):
        raise ValueError("capability catalog has an incomplete full-profile CLI ownership mapping")
    return seen


# ---- package reading ------------------------------------------------------

def read_markdown(path: Path, package_path: str, sources: dict[str, str], files: list[dict[str, str]],
                  diagnostics: list[dict[str, Any]]) -> None:
    try:
        if path.lstat().st_size > SINGLE_FILE_MAX_BYTES:
            return
        raw = path.read_bytes()
        source = raw.decode("utf-8", errors="replace")
    except OSError:
        diagnostics.append(diagnostic("TARGET_NOT_READABLE", "error", "目标文件不可读。", "修复文件读取权限后重新检查。",
                                      file=package_path))
        return
    if "\0" in source or "�" in source:
        diagnostics.append(diagnostic("RESOURCE_UNSUPPORTED", "error", "资源不是受支持的普通文本 Markdown。",
                                      "只保留可正常读取的 Markdown 文本资源。", file=package_path))
        return
    sources[package_path] = source
    files.append({"path": package_path, "sha256": sha256(source)})


def check_package_limits(root: Path) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    count = 0
    total = 0
    for path in sorted(root.rglob("*")):
        if path.is_dir() and not path.is_symlink():
            continue
        count += 1
        size = path.lstat().st_size
        total += size
        if size > SINGLE_FILE_MAX_BYTES:
            diagnostics.append(diagnostic("PACKAGE_FILE_SIZE_EXCEEDED", "error",
                                          f"单文件大小超限（当前 {size} 字节，上限 {SINGLE_FILE_MAX_BYTES} 字节）。",
                                          "压缩或拆分该文件，使单文件不超过 1 MB。",
                                          file=path.relative_to(root).as_posix()))
    if count > PACKAGE_MAX_FILES:
        diagnostics.append(diagnostic("PACKAGE_FILE_COUNT_EXCEEDED", "error",
                                      f"Skill 文件数量超限（当前 {count} 个，上限 {PACKAGE_MAX_FILES} 个）。",
                                      "删除不必要文件或合并参考内容，使文件数量不超过 100 个。"))
    if total > PACKAGE_MAX_BYTES:
        diagnostics.append(diagnostic("PACKAGE_TOTAL_SIZE_EXCEEDED", "error",
                                      f"Skill 总包大小超限（当前 {total} 字节，上限 {PACKAGE_MAX_BYTES} 字节）。",
                                      "压缩或删除不必要内容，使总包大小不超过 10 MB。"))
    return diagnostics


def walk_references(root: Path, rel: str, sources: dict[str, str], files: list[dict[str, str]],
                    diagnostics: list[dict[str, Any]]) -> None:
    for entry in sorted((root / rel).iterdir(), key=lambda p: p.name):
        package_path = f"{rel}/{entry.name}"
        if entry.is_symlink():
            diagnostics.append(diagnostic("RESOURCE_PATH_INVALID", "error", "references 不允许符号链接。",
                                          "改为包内普通 Markdown 文件。", file=package_path))
            continue
        if entry.is_dir():
            walk_references(root, package_path, sources, files, diagnostics)
            continue
        if not entry.is_file() or not entry.name.endswith(".md"):
            diagnostics.append(diagnostic("RESOURCE_UNSUPPORTED", "error", "references 只允许普通 Markdown 文件。",
                                          "删除脚本、可执行文件、二进制或其他扩展名资源。", file=package_path))
            continue
        read_markdown(entry, package_path, sources, files, diagnostics)


# ---- SKILL.md checks (official) -------------------------------------------

def parse_frontmatter(source: str) -> tuple[dict[str, str] | None, str, list[dict[str, Any]]]:
    match = FRONTMATTER.match(source)
    if not match:
        return None, source, [diagnostic("SKILL_FRONTMATTER_INVALID", "error", "SKILL.md 缺少有效的起始 frontmatter。",
                                         "在文件开头使用 --- 包围 name 和 description。", file="SKILL.md", line=1)]
    issues: list[dict[str, Any]] = []
    value: dict[str, str] = {}
    allowed = ("name", "description")
    for index, line in enumerate(re.split(r"\r?\n", match.group(1))):
        number = index + 2
        sep = line.find(":")
        if sep <= 0:
            issues.append(diagnostic("SKILL_FRONTMATTER_INVALID", "error", "frontmatter 行不是简单键值格式。",
                                     "使用 name: value 或 description: value。", file="SKILL.md", line=number))
            continue
        key = js_trim(line[:sep])
        raw = js_trim(line[sep + 1:])
        if key not in allowed or key in value or not raw or re.match(r"^[\[{&*!>|]", raw):
            issues.append(diagnostic("SKILL_FRONTMATTER_INVALID", "error",
                                     "frontmatter 只允许非空、不重复的单行 name 和 description。", "删除额外或复杂字段。",
                                     file="SKILL.md", line=number))
            continue
        quoted = re.fullmatch(r"\"([\s\S]*)\"|'([\s\S]*)'", raw, re.S)
        value[key] = (quoted.group(1) or quoted.group(2) or "") if quoted else raw
    for key in allowed:
        if key not in value:
            issues.append(diagnostic("SKILL_FRONTMATTER_INVALID", "error", "frontmatter 缺少 " + key + "。", "补充必需字段。",
                                     file="SKILL.md", line=1))
    return value, source[match.end():], issues


def check_skill_markdown(source: str) -> tuple[dict[str, str] | None, str, list[dict[str, Any]]]:
    frontmatter, body, issues = parse_frontmatter(source)
    for pattern, label in REQUIRED_SECTIONS:
        if not pattern.search(body):
            issues.append(diagnostic("SKILL_REQUIRED_SECTION_MISSING", "error", "SKILL.md 缺少必需章节：" + label + "。",
                                     "按编排型 Skill 契约补充该章节。", file="SKILL.md"))
    for m in PLACEHOLDER.finditer(source):
        issues.append(diagnostic("SKILL_PLACEHOLDER_REMAINS", "error", "SKILL.md 仍包含未完成占位标记。",
                                 "替换为当前 Skill 的真实内容。", file="SKILL.md", line=line_for_offset(source, m.start())))
    if frontmatter and frontmatter.get("name"):
        n = len(frontmatter["name"])
        if n < SKILL_NAME_MIN or n > SKILL_NAME_MAX:
            issues.append(diagnostic("SKILL_NAME_LENGTH_INVALID", "error", f"name 长度不合规（当前 {n} 字符）。",
                                     "将 name 调整为 2-64 个字符，并保持与目录名一致。", file="SKILL.md", line=2))
    if frontmatter and frontmatter.get("description"):
        desc = frontmatter["description"]
        if len(desc) > DESCRIPTION_MAX:
            issues.append(diagnostic("DESCRIPTION_LENGTH_EXCEEDED", "error",
                                     f"description 长度超限（当前 {len(desc)} 字符，上限 {DESCRIPTION_MAX} 字符）。",
                                     "精简 description，只保留用户可见产出和触发场景。", file="SKILL.md", line=3))
        if not DESCRIPTION_TRIGGER.search(desc):
            issues.append(diagnostic("DESCRIPTION_TRIGGER_MISSING", "warning", "description 没有明确说明用户触发场景。",
                                     "补充用户实际会说的触发表达。", file="SKILL.md", line=3))
        head = DESCRIPTION_SPLIT.split(desc)[0]
        if DESCRIPTION_EXECUTION_DETAIL.search(head):
            issues.append(diagnostic("DESCRIPTION_EXECUTION_DETAIL", "warning", "description 的能力部分包含执行顺序、保存位置或否定规则。",
                                     "把执行细节移到正文，只保留独有产出和触发场景。", file="SKILL.md", line=3))
        if DESCRIPTION_IMPERATIVE.search(head):
            issues.append(diagnostic("DESCRIPTION_IMPERATIVE_STYLE", "warning", "description 像一条可直接执行的指令。",
                                     "改成陈述性名词短语。", file="SKILL.md", line=3))
    body_lines = line_count(body)
    if body_lines > SKILL_BODY_RECOMMENDED_LINES:
        issues.append(diagnostic("SKILL_BODY_LINES_RECOMMENDATION_EXCEEDED", "warning",
                                 f"SKILL.md 正文 {body_lines} 行，超过建议的 {SKILL_BODY_RECOMMENDED_LINES} 行。",
                                 "只保留核心流程，将细节拆到 references。", file="SKILL.md"))
    return frontmatter, body, issues


def check_references(skill_source: str, sources: dict[str, str]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    links = set(REFERENCE_LINK.findall(skill_source))
    for package_path in sources:
        if package_path != "SKILL.md" and package_path not in links:
            issues.append(diagnostic("RESOURCE_UNREFERENCED", "warning", "Markdown resource 没有被 SKILL.md 直接导航。",
                                     "从 SKILL.md 直接链接该资源并说明何时读取，或删除它。", file=package_path))
    for linked in links:
        if linked not in sources:
            issues.append(diagnostic("RESOURCE_PATH_INVALID", "error", "SKILL.md 链接的 reference 不存在或不可读。",
                                     "修正链接或补充包内 Markdown 文件。", file="SKILL.md"))
    return issues


def strip_markdown_suffix(value: str) -> str:
    return re.sub(r"[`),.;，。；]+$", "", js_trim(value))


def delegate_command_on_line(line: str, start: int) -> str:
    if line.rfind("`", 0, start + 1) != -1:
        closing = line.find("`", start)
        if closing != -1:
            return line[start:closing]
    return strip_markdown_suffix(line[start:])


def delegate_commands(source: str) -> list[tuple[int, str]]:
    """Every delegate command as the official checker sees it: (line number, command)."""
    out = []
    for index, line in enumerate(re.split(r"\r?\n", source)):
        start = line.find("delegate --")
        if start != -1:
            out.append((index + 1, delegate_command_on_line(line, start)))
    return out


def instruction_of(command: str) -> str:
    matches = list(INSTRUCTION_ARG.finditer(command))
    return (matches[0].group(1) or "") if matches else ""


def check_delegates(source: str) -> tuple[list[dict[str, Any]], list[tuple[str, int]]]:
    issues: list[dict[str, Any]] = []
    targets: list[tuple[str, int]] = []
    commands = delegate_commands(source)
    for line_no, command in commands:
        loc = {"file": "SKILL.md", "line": line_no}
        if DELEGATE_CHAINING.search(command):
            issues.append(diagnostic("DELEGATE_FORMAT_INVALID", "error", "delegate 命令包含管道、重定向、命令替换或拼接。",
                                     "只保留单条标准 delegate 命令。", **loc))
            continue
        target_matches = list(TARGET_ARG.finditer(command))
        instruction_matches = list(INSTRUCTION_ARG.finditer(command))
        if len(target_matches) != 1 or len(instruction_matches) != 1 or EXTRA_FLAG.search(command):
            issues.append(diagnostic("DELEGATE_FORMAT_INVALID", "error", "delegate 必须且只能包含一次 --target 和 --instruction。",
                                     "使用 delegate --target {agent-id} --instruction '{task}'。", **loc))
            continue
        target = strip_markdown_suffix(target_matches[0].group(1) or "")
        raw = instruction_matches[0].group(1) or ""
        if not target:
            issues.append(diagnostic("DELEGATE_FORMAT_INVALID", "error", "delegate 缺少 target。", "提供已注册子专家 ID。", **loc))
        elif target not in ALLOWED_AGENTS:
            issues.append(diagnostic("DELEGATE_TARGET_UNKNOWN", "error", "delegate target 不是 full 主专家已注册子专家。",
                                     "改用六个公开目标之一。", **loc))
            issues.append(diagnostic("SECURITY_UNREGISTERED_AGENT", "error", "Skill 使用了未注册 Agent。",
                                     "删除或替换为公开子专家 target。", **loc))
        else:
            targets.append((target, line_no))
        if raw in ("", "''", '""'):
            issues.append(diagnostic("DELEGATE_INSTRUCTION_EMPTY", "error", "delegate instruction 缺失或为空。",
                                     "提供包含用户目标和约束的自包含任务。", **loc))
        if not SINGLE_QUOTED.match(raw):
            issues.append(diagnostic("DELEGATE_FORMAT_INVALID", "error", "delegate instruction 必须使用 Shell 单引号。",
                                     "使用 --instruction '{task}'。", **loc))
        if HARDCODED_HOME.search(raw):
            issues.append(diagnostic("DELEGATE_HARDCODED_HOME_PATH", "warning", "delegate instruction 写死了具体用户的个人目录。",
                                     "只传递上一步返回的真实业务路径。", **loc))
        if UNRESOLVED_DYNAMIC_VALUE.search(raw):
            issues.append(diagnostic("DELEGATE_DYNAMIC_VALUE_UNRESOLVED", "warning", "delegate instruction 含未解析占位符或跨步骤指代。",
                                     "组装最终命令时替换为真实 delegation 结果。", **loc))
    if not commands:
        issues.append(diagnostic("DELEGATION_WORKFLOW_STATIC_VALIDATION_INCOMPLETE", "warning",
                                 "正文中没有可机械识别的标准 delegate 命令。", "补充标准 delegate 命令。", file="SKILL.md"))
    missing = [t for t in REQUIRED_STATUS_TOKENS if t not in source]
    if missing:
        issues.append(diagnostic("DELEGATION_RESULT_HANDLING_MISSING", "error",
                                 "正文没有覆盖全部 delegation 公开状态：" + ", ".join(missing) + "。",
                                 "补充 completed、failed、cancelled、waiting_user、waiting_approval 的处理。", file="SKILL.md"))
    if len(commands) > 1 and not REAL_RESULT.search(source):
        issues.append(diagnostic("DELEGATION_WORKFLOW_STATIC_VALIDATION_INCOMPLETE", "warning",
                                 "多委托正文缺少可机械识别的真实结果传递说明。", "人工确认下游只使用上游真实业务结果。", file="SKILL.md"))
    if commands and QUERY_INTENT.search(source) and not EMPTY_RESULT_HANDLING.search(source):
        issues.append(diagnostic("EMPTY_RESULT_HANDLING_MISSING", "warning", "查询、筛选或批量流程没有明确空结果处理。",
                                 "说明无匹配时如实报告并停止。", file="SKILL.md"))
    return issues, targets


def evidence_entries(source: str) -> list[tuple[str, str, int]]:
    heading = EVIDENCE_HEADING.search(source)
    if not heading:
        return []
    start = heading.end()
    rest = source[start:]
    nxt = NEXT_HEADING.search(rest)
    section = rest if nxt is None else rest[: nxt.start()]
    return [(m.group(1), m.group(2), line_for_offset(source, start + m.start())) for m in EVIDENCE_LINE.finditer(section)]


def check_capability_evidence(source: str, targets: list[tuple[str, int]],
                              cli_agents: dict[str, str] | None = None) -> list[dict[str, Any]]:
    cli_agents = FULL_PROFILE_CLI_AGENTS if cli_agents is None else cli_agents
    issues: list[dict[str, Any]] = []
    evidence = evidence_entries(source)
    if targets and not evidence:
        return [diagnostic("CAPABILITY_EVIDENCE_MISSING", "error", "委托型 Skill 缺少可机械核对的生成期 CLI 唯一归属依据。",
                           "添加 Generation-time capability evidence 章节。", file="SKILL.md")]
    evidenced: set[str] = set()
    seen: set[str] = set()
    for cli, agent, line in evidence:
        loc = {"file": "SKILL.md", "line": line}
        if cli in seen:
            issues.append(diagnostic("CAPABILITY_EVIDENCE_DUPLICATE", "error", "生成期能力依据重复声明 CLI。", "每个 CLI 只保留一条。", **loc))
            continue
        seen.add(cli)
        expected = cli_agents.get(cli)
        if not expected:
            issues.append(diagnostic("CAPABILITY_EVIDENCE_CLI_UNKNOWN", "error", "生成期能力依据引用了 catalog 中不存在的 CLI。",
                                     "改用 catalog 中的准确名称。", **loc))
            continue
        if agent != expected:
            issues.append(diagnostic("CAPABILITY_EVIDENCE_AGENT_MISMATCH", "error", f"CLI {cli} 的唯一子专家应为 {expected}。",
                                     "修正映射。", **loc))
            continue
        evidenced.add(agent)
    for target, line in targets:
        if target not in evidenced:
            issues.append(diagnostic("DELEGATE_TARGET_EVIDENCE_MISSING", "error", "delegate target 没有对应的 CLI 唯一归属依据。",
                                     "补充归属到该 target 的真实 CLI 依据。", file="SKILL.md", line=line))
    return issues


def scan_security(file_name: str, source: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for index, line in enumerate(re.split(r"\r?\n", source)):
        loc = {"file": file_name, "line": index + 1}
        if RUNTIME_FENCE.search(line):
            issues.append(diagnostic("SECURITY_SCRIPT_EXECUTION_UNSUPPORTED", "error", "Skill 包含不受支持的运行时脚本代码块。",
                                     "删除脚本。", **loc))
        if PRIVATE_KEY.search(line) or CREDENTIAL_ASSIGNMENT.search(line):
            issues.append(diagnostic("SECURITY_CREDENTIAL_LITERAL", "error", "Skill 包含高置信度凭据字面量。", "删除凭据。", **loc))
        if REMOTE_DOWNLOAD.search(line):
            issues.append(diagnostic("SECURITY_REMOTE_DOWNLOAD", "error", "Skill 包含远端下载或下载后执行模式。", "删除远端下载。", **loc))
        if CLI_INVOKE.search(line) and not CLI_INVOKE_NEGATED.search(line):
            issues.append(diagnostic("RUNTIME_DIRECT_CLI_INVOKE", "error", "full 主专家 Skill 要求父层直接执行 cli.invoke。",
                                     "改为委托已注册子专家。", **loc))
        if INTERNAL_CAPABILITY.search(line):
            issues.append(diagnostic("SECURITY_INTERNAL_CAPABILITY", "error", "Skill 引用了内部能力或关联标识。",
                                     "只使用公开 delegate target 和业务结果。", **loc))
        if COMPACT_PROFILE.search(line):
            issues.append(diagnostic("RUNTIME_PROFILE_UNSUPPORTED", "error", "生成物声称支持当前未实证的 compact profile。",
                                     "只声明支持 full main-agent。", **loc))
        if BYPASS.search(line):
            issues.append(diagnostic("SECURITY_GATEWAY_BYPASS", "error", "Skill 明确要求绕过审批、权限或审计。", "删除绕过指令。", **loc))
        if "delegate --" not in line and (DIRECT_FILE_API.search(line) or HTTP_CALL.search(line) or NAS_PATH.search(line)):
            issues.append(diagnostic("SECURITY_DIRECT_FILE_ACCESS", "error", "Skill 使用了 allowlist 外的文件、网络或 NAS 访问方式。",
                                     "通过已注册子专家完成真实 NAS 工作流。", **loc))
    return issues


# ---- plan.md extras -------------------------------------------------------

def section_text(body: str, title: str) -> str:
    m = re.search(rf"^# {re.escape(title)}\s*$", body, re.M)
    if not m:
        return ""
    rest = body[m.end():]
    nxt = NEXT_HEADING.search(rest)
    return rest if nxt is None else rest[: nxt.start()]


def declared_values(body: str) -> set[str]:
    return set(re.findall(r"`\{([A-Za-z][A-Za-z0-9_-]*)\}`", section_text(body, "Required input")))


def unescaped_quote(raw_instruction: str) -> bool:
    """True when a single quote inside the instruction is not one of the shell escapes."""
    if len(raw_instruction) < 2 or not (raw_instruction.startswith("'") and raw_instruction.endswith("'")):
        return False  # reported by the official layer
    inner = raw_instruction[1:-1]
    for esc in QUOTE_ESCAPES:
        inner = inner.replace(esc, "")
    return "'" in inner


def full_instruction(command: str) -> str:
    idx = command.find("--instruction ")
    return command[idx + len("--instruction "):].strip() if idx != -1 else ""


def check_plan(sources: dict[str, str], body: str, skill_source: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for file_name, source in sources.items():
        for index, line in enumerate(source.splitlines()):
            for m in PLAN_FORBIDDEN.finditer(line):
                issues.append(diagnostic("PLAN_FORBIDDEN_TERM", "error", f"plan.md 금지어 grep 적중: {m.group(0)!r}",
                                         "단어를 바꾼다 (예: 'confirm ' -> 'confirm,' 또는 'approve').",
                                         file=file_name, line=index + 1))
    n = line_count(body)
    if n > PLAN_BODY_LINES_TARGET:
        issues.append(diagnostic("PLAN_BODY_LINES_TARGET", "warning", f"SKILL.md 본문 {n}행, plan 목표 {PLAN_BODY_LINES_TARGET}행 초과.",
                                 "세부 내용을 references로 옮긴다.", file="SKILL.md"))
    for ref in PLAN_REFERENCES:
        if ref not in sources:
            issues.append(diagnostic("PLAN_REFERENCE_MISSING", "warning", f"plan.md references 4종 중 {ref} 없음.",
                                     "references 4종을 작성한다.", file=ref))
    evidence = {cli: agent for cli, agent, _ in evidence_entries(skill_source)}
    if evidence != PLAN_EVIDENCE:
        issues.append(diagnostic("PLAN_EVIDENCE_SET", "warning", "capability evidence가 계획한 6줄과 다르다.",
                                 "ug-filesystem, ug-filemgr, file-workflow, ug-photo, ug-knowledge, ug-document 6줄.", file="SKILL.md"))
    declared = declared_values(body)
    used: set[str] = set()
    body_start = len(skill_source) - len(body)
    required = section_text(body, "Required input")
    for m in VALUE_TOKEN.finditer(skill_source):
        name = m.group(1)
        line_no = line_for_offset(skill_source, m.start())
        if m.start() < body_start:
            continue
        if not VALUE_NAME.match(name):
            issues.append(diagnostic("PLAN_VALUE_NAME", "error", f"{{{name}}}: 소문자·숫자·_·- 만 쓴다.", "이름을 바꾼다.",
                                     file="SKILL.md", line=line_no))
        if name not in declared:
            issues.append(diagnostic("PLAN_VALUE_UNDECLARED", "error", f"{{{name}}}가 Required input에 선언되지 않았다.",
                                     "Required input 목록에 `{name}`으로 선언한다.", file="SKILL.md", line=line_no))
        used.add(name)
    outside = body.replace(required, "", 1) if required else body
    for name in sorted(declared):
        if "{" + name + "}" not in outside:
            issues.append(diagnostic("PLAN_VALUE_UNUSED", "warning", f"{{{name}}}가 선언만 되고 쓰이지 않는다.", "선언을 지우거나 쓴다.",
                                     file="SKILL.md"))
    for line_no, command in delegate_commands(skill_source):
        instruction = full_instruction(command)
        if unescaped_quote(instruction):
            issues.append(diagnostic("PLAN_QUOTE_UNESCAPED", "error", "instruction 안 작은따옴표가 이스케이프되지 않았다.",
                                     "'\"'\"' 로 쓰거나 작은따옴표 없는 문장으로 바꾼다.", file="SKILL.md", line=line_no))
        if VAGUE_REFERENCE.search(instruction):
            issues.append(diagnostic("PLAN_VAGUE_REFERENCE", "warning", "instruction에 'that folder' 식 지칭이 있다.",
                                     "{value} 중괄호 값으로 바꾼다.", file="SKILL.md", line=line_no))
    return issues


# ---- entry point ----------------------------------------------------------

def check_skill(target: Path, plan: bool = True, catalog: Path | None = None) -> dict[str, Any]:
    cli_agents = validate_catalog(catalog) if catalog is not None else None
    target = target.resolve()
    if not target.exists():
        return finalize({}, [], [diagnostic("TARGET_NOT_FOUND", "error", "目标 Skill 目录不存在。", "提供一个存在的目录。")])
    if not target.is_dir():
        return finalize({}, [], [diagnostic("TARGET_NOT_DIRECTORY", "error", "检查目标不是目录。", "提供包含 SKILL.md 的目录。")])
    diagnostics = check_package_limits(target)
    sources: dict[str, str] = {}
    files: list[dict[str, str]] = []
    names = {p.name for p in target.iterdir()}
    if "SKILL.md" not in names:
        diagnostics.append(diagnostic("FILE_REQUIRED_MISSING", "error", "缺少唯一必需入口 SKILL.md。", "在 Skill 根目录添加 SKILL.md。",
                                      file="SKILL.md"))
    for entry in target.iterdir():
        if entry.name == "SKILL.md" or (entry.name == "references" and entry.is_dir() and not entry.is_symlink()):
            continue
        diagnostics.append(diagnostic("RESOURCE_PATH_INVALID" if entry.is_symlink() else "RESOURCE_UNSUPPORTED", "error",
                                      "Skill 根目录只允许 SKILL.md 和 references/。", "删除其他根级项目。", file=entry.name))
    skill_path = target / "SKILL.md"
    if skill_path.exists():
        if skill_path.is_symlink() or not skill_path.is_file():
            diagnostics.append(diagnostic("RESOURCE_PATH_INVALID", "error", "SKILL.md 必须是普通文件。", "使用普通文件。", file="SKILL.md"))
        else:
            read_markdown(skill_path, "SKILL.md", sources, files, diagnostics)
    refs = target / "references"
    if refs.exists() or refs.is_symlink():
        if refs.is_symlink() or not refs.is_dir():
            diagnostics.append(diagnostic("RESOURCE_PATH_INVALID", "error", "references 必须是包内普通目录。", "删除符号链接。",
                                          file="references"))
        else:
            walk_references(target, "references", sources, files, diagnostics)
    result_target: dict[str, Any] = {}
    skill_source = sources.get("SKILL.md")
    if skill_source is not None:
        frontmatter, body, issues = check_skill_markdown(skill_source)
        diagnostics += issues
        name = (frontmatter or {}).get("name")
        if name and SKILL_NAME_PATTERN.match(name):
            result_target["skillName"] = name
            if name != target.name:
                diagnostics.append(diagnostic("SKILL_NAME_MISMATCH", "error", "目录名与 frontmatter name 不一致。", "统一名称。",
                                              file="SKILL.md", line=2))
        elif name:
            diagnostics.append(diagnostic("SKILL_NAME_INVALID", "error", "Skill 名称格式无效。", "使用小写字母、数字和单个短横线分段。",
                                          file="SKILL.md", line=2))
        diagnostics += check_references(skill_source, sources)
        delegate_issues, targets = check_delegates(skill_source)
        diagnostics += delegate_issues
        diagnostics += check_capability_evidence(skill_source, targets, cli_agents)
        if plan:
            diagnostics += check_plan(sources, body, skill_source)
    for file_name, source in sources.items():
        diagnostics += scan_security(file_name, source)
    return finalize(result_target, files, diagnostics)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", type=Path)
    parser.add_argument("--official", action="store_true", help="official check-lib.mjs port only")
    parser.add_argument("--catalog", type=Path,
                        help="capability-catalog.json from uliya-skill-kit 0.7.7 (untrusted JSON, read only); validates it and "
                             "checks the evidence lines against its CLI -> agent map")
    parser.add_argument("--summary", action="store_true", help="print one line per diagnostic instead of JSON")
    args = parser.parse_args(argv)
    try:
        result = check_skill(args.target, plan=not args.official, catalog=args.catalog)
    except (OSError, ValueError) as error:
        print(f"check failed: {error}", file=sys.stderr)
        return 2
    if args.summary:
        for d in result["diagnostics"]:
            print(f"{d['severity']:7} {d['code']} {d.get('file', '')}:{d.get('line', '')} {d['message']}")
        s = result["summary"]
        print(f"{result['status']}: {s['errors']} error, {s['warnings']} warning")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "not-uploadable" else 0


if __name__ == "__main__":
    sys.exit(main())
