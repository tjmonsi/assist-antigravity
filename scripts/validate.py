#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Toni-Jan Keith Monserrat
"""Validate assist-plugin against the documented Antigravity plugin formats.

Usage: python3 scripts/validate.py [plugin-dir]

Standard library only; requires Python 3.9 or later. Prints `ERROR <file>: <reason>` and
`WARN <file>: <reason>` lines, then a summary. Exits 1 if any ERROR was reported.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_PLUGIN_DIR = SCRIPT_DIR.parent / "plugins" / "assist-plugin"
PROFILE_SCRIPT = SCRIPT_DIR / "set-model-profile.sh"
SYNC_SCRIPT = SCRIPT_DIR / "sync-writing-standard.py"

PLUGIN_JSON_KEYS = {"name", "description", "version", "$schema"}
VALID_TOOLS = {
    "view_file", "write_to_file", "replace_file_content", "multi_replace_file_content",
    "list_dir", "find_by_name", "grep_search", "search_web", "read_url_content",
    "run_command", "manage_task", "schedule", "list_permissions", "ask_permission",
    "invoke_subagent", "define_subagent", "send_message", "manage_subagents",
    "ask_question", "generate_image",
}
VALID_MODELS = {"inherit", "flash", "pro"}
VALID_POLICIES = {"off", "auto", "eager", "sandbox"}
AGENT_FORBIDDEN_KEYS = {"type", "effort"}
AGENT_REQUIRED_KEYS = ("subagent", "commandExecutionPolicy")
SKILL_FORBIDDEN_KEYS = {"allowed-tools", "effort", "argument-hint", "user-invocable", "disable-model-invocation"}
VALID_TRIGGERS = {"always_on", "model_decision", "glob", "manual"}
RULE_MAX_BYTES = 24000
# agy 1.3.3 injects a skill's body (the text after the frontmatter) when its slash command runs and
# cuts it at about 24,000 bytes, marking the cut `<truncated N bytes>`; the model never sees the rest.
# The error level leaves 2,000 bytes and the warning level 4,000 bytes for agy's own preamble.
SKILL_BODY_CUT_BYTES = 24000
SKILL_BODY_MAX_BYTES = 22000
SKILL_BODY_WARN_BYTES = 20000

CLAUDE_ISMS = [
    ("AskUserQuestion", re.compile(r"AskUserQuestion")),
    ("Agent tool", re.compile(r"Agent tool")),
    ("run_in_background", re.compile(r"run_in_background")),
    ("CLAUDE.md", re.compile(r"CLAUDE\.md")),
    (".claude/", re.compile(r"\.claude/")),
    ("subagent_type", re.compile(r"subagent_type")),
    ("Opus|Sonnet|Haiku", re.compile(r"\b(?:Opus|Sonnet|Haiku)\b")),
    ("ToolSearch", re.compile(r"ToolSearch")),
    ("TodoWrite", re.compile(r"TodoWrite")),
    ("WebFetch", re.compile(r"WebFetch")),
    ("WebSearch", re.compile(r"WebSearch")),
    ("LSP", re.compile(r"\bLSP\b")),
    ("$ARGUMENTS", re.compile(r"\$ARGUMENTS")),
    ("CLAUDE_PLUGIN_ROOT", re.compile(r"CLAUDE_PLUGIN_ROOT")),
    (".claude-plugin", re.compile(r"\.claude-plugin")),
    ("$0/$1 positional args", re.compile(r"\$[0-9]\b(?!\.\d)")),
    ("!`cmd` dynamic context", re.compile(r"(?<![\w`!])!`[^`\n]+`")),
    ("allowed-tools", re.compile(r"allowed-tools")),
    ("pre-approved", re.compile(r"\bpre-approv", re.I)),
    ("Bash(...) permission rule", re.compile(r"\b(?:Bash|PowerShell)\([^)\n]*\)")),
    ("PowerShell tool", re.compile(r"\bPowerShell tool\b")),
    ("EnterWorktree/ExitWorktree", re.compile(r"\b(?:Enter|Exit)Worktree\b")),
    ('isolation: "worktree"', re.compile(r"isolation:\s*\"?worktree")),
    ("CLAUDE_PLUGIN_DATA", re.compile(r"CLAUDE_PLUGIN_DATA")),
    ("systemMessage", re.compile(r"systemMessage")),
    # Upstream v1.8.0 hooks and output style that the port does not ship.
    ("upstream hook name", re.compile(r"\b(?:prose-gate|prose-advisor|writing-context|injection-filter)\b")),
    ("prose-rules.js", re.compile(r"prose-(?:rules|diff)\.js")),
    ("output style", re.compile(r"output-styles?/|\bterse\.md\b")),
    # Upstream v1.9.0 tools, events, hooks, and script that the port does not ship.
    ("SendMessage", re.compile(r"\bSendMessage\b")),
    ("SubagentStop/SubagentHandback", re.compile(r"\bSubagent(?:Stop|Handback)\b")),
    ("FSA hook name", re.compile(r"\bfsa-(?:write-bar|log)\b")),
    ("check-fsa-tables", re.compile(r"check-fsa-tables")),
    ("Base directory for this skill", re.compile(r"Base directory for this skill")),
    # Upstream v1.10.0 hook, health report, settings, and permission rules that the port does not ship.
    ("commit-attribution-guard", re.compile(r"commit-attribution-guard")),
    ("assist-plugin:health", re.compile(r"assist-plugin:health")),
    ("attribution.commit/pr setting", re.compile(r"\battribution\.(?:commit|pr)\b")),
    ("hooks-disabled.json", re.compile(r"hooks-disabled\.json")),
    ("Edit(...) permission rule", re.compile(r"\b(?:Edit|Write|Read)\([^)\n]*\)")),
    ("through Other", re.compile(r"\bthrough Other\b")),
]
# These two patterns also occur legitimately inside fenced code (SQL placeholders such as $1,
# Rust macros), so they are checked outside fenced code blocks only.
PROSE_ONLY_ISMS = {"$0/$1 positional args", "!`cmd` dynamic context"}
# Lines carrying this marker (upstream-to-Antigravity mapping tables, attribution) are skipped.
CLAUDE_REF_OK = "<!-- claude-ref-ok -->"

LINK_RE = re.compile(r"(?<!!)\[[^\]\n]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
# A fence closes only on a line of the same character, at least as long as the opener, with nothing
# after it but whitespace (CommonMark), so a ```` block can hold ``` lines.
FENCE_CLOSE_RE = re.compile(r"^\s*(`{3,}|~{3,})\s*$")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
POLICY_LINE_RE = re.compile(r"^commandExecutionPolicy:\s*(?:off|Off|OFF)\s*(?:#.*)?$", re.M)
TIER_RE = re.compile(r"^(REVIEW|BUILD|FAST)_TIER=\(([^)]*)\)\s*$", re.M)
# C0 control bytes other than TAB (0x09) and LF (0x0a). CR is included: plugin files use LF only,
# and a stray CR (or BS/FF) usually means a "\r"/"\b"/"\f" escape was interpreted while writing.
CONTROL_BYTES_RE = re.compile(rb"[\x00-\x08\x0b-\x1f]")
# Invisible Unicode in plugin markdown and plugin.json can hide instructions from reviewers. Bidi
# controls (including the LRM, RLM, and ALM marks) and tag characters are errors; zero-width
# characters and the BOM are warnings because they have a few legitimate uses.
BIDI_TAG_RE = re.compile("[\u200e\u200f\u061c\u202a-\u202e\u2066-\u2069\U000e0000-\U000e007f]")
ZERO_WIDTH_RE = re.compile("[\u200b-\u200d\u2060\ufeff]")
# (path relative to the plugin root, character) pairs that are allowed without a warning.
ZERO_WIDTH_ALLOWED = {("skills/ask/references/answer-format.md", "\u200b")}  # escapes nested fences
MAX_LOCATIONS = 5
# Writing-standard block-tier characters: em dash, horizontal bar, curly quotes. Checked outside
# fenced code, inline code, and straight double-quoted spans (quoted examples stay as written).
PROSE_TELL_RE = re.compile("[\u2014\u2015\u2018\u2019\u201c\u201d]")
DOUBLE_QUOTED_RE = re.compile(r'"[^"\n]{0,300}"')


def fence_step(line: str, fence: tuple[str, int] | None) -> tuple[bool, tuple[str, int] | None]:
    """(is_fence_line, new_state) for one line; state is None outside a fence, else (char, length)."""
    if fence is None:
        m = FENCE_RE.match(line)
        return (True, (m.group(1)[0], len(m.group(1)))) if m else (False, None)
    m = FENCE_CLOSE_RE.match(line)
    if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= fence[1]:
        return True, None
    return False, fence


# FSA state tables and terminal blocks (rules in skills/do/references/fsa-template.md).
STATES_HEADER_RE = re.compile(r"^\|\s*State\s*\|\s*Kind\s*\|\s*Does\s*\|\s*Outcome -> next state\s*\|\s*$")
FSA_FIELDS = ("fsa", "state", "trace", "artifact", "verdict", "skipped", "out_of_scope",
              "error_class", "questions", "resume_at")
FSA_STATES = {"Done", "NeedsInput", "Error"}
FSA_ERROR_CLASSES = {"missing-input", "precondition-failed", "policy-rejection", "budget-exhausted",
                     "tool-missing", "tool-failed", "out-of-scope", "none"}
FSA_PLACEHOLDER = "<agent>/<version>"
FSA_KINDS = {"check", "model", "terminal"}
DO_SKILL = "skills/do/SKILL.md"
FSA_TEMPLATE = "skills/do/references/fsa-template.md"
CREATE_TEST_SKILL = "skills/create-test/SKILL.md"
EDGE_TARGET_RE = re.compile(r"->\s*([A-Za-z][A-Za-z0-9]*)(?:\(([a-z-]+)\))?")


class Report:
    def __init__(self, root: Path):
        self.root = root
        self.errors = 0
        self.warnings = 0

    def _rel(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)

    def error(self, path: Path, reason: str) -> None:
        self.errors += 1
        print(f"ERROR {self._rel(path)}: {reason}")

    def warn(self, path: Path, reason: str) -> None:
        self.warnings += 1
        print(f"WARN {self._rel(path)}: {reason}")


# --- Frontmatter parsing -------------------------------------------------------

class FrontmatterError(ValueError):
    pass


def _scalar(raw: str):
    """Parse a scalar or inline list value."""
    raw = raw.strip()
    if raw == "":
        return ""
    if raw[0] == '"':
        if len(raw) < 2 or raw[-1] != '"':
            raise FrontmatterError(f"unterminated double-quoted string: {raw}")
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise FrontmatterError(f"bad double-quoted string {raw}: {exc}") from exc
    if raw[0] == "'":
        if len(raw) < 2 or raw[-1] != "'":
            raise FrontmatterError(f"unterminated single-quoted string: {raw}")
        return raw[1:-1].replace("''", "'")
    if raw[0] == "[":
        if raw[-1] != "]":
            raise FrontmatterError(f"unterminated inline list: {raw}")
        inner = raw[1:-1].strip()
        return [_scalar(item) for item in inner.split(",")] if inner else []
    if raw in ("true", "false"):
        return raw == "true"
    return raw


def _block_scalar(lines: list[str], style: str) -> str:
    texts = [ln.strip() for ln in lines]
    while texts and texts[-1] == "":
        texts.pop()
    if style.startswith("|"):
        return "\n".join(texts)
    # Folded: join non-empty lines with spaces, blank lines become newlines.
    out, para = [], []
    for t in texts:
        if t == "":
            out.append(" ".join(para))
            para = []
        else:
            para.append(t)
    out.append(" ".join(para))
    return "\n".join(p for p in out if p)


def parse_frontmatter(text: str) -> tuple[dict, str] | None:
    """Return (fields, body) or None when the file has no frontmatter.

    Supports `key: value`, quoted strings, `>-`/`|` block scalars, inline `[a, b]`
    lists, block `- item` lists, and one-level nested maps.
    """
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 3)
    if end == -1:
        if text.endswith("\n---"):
            end = len(text) - 4
        else:
            raise FrontmatterError("unterminated frontmatter")
    lines = text[4:end].split("\n")
    body = text[end + 5:]

    fields: dict = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip() == "" or line.lstrip().startswith("#"):
            i += 1
            continue
        if line[0].isspace():
            raise FrontmatterError(f"unexpected indentation: {line!r}")
        if ":" not in line:
            raise FrontmatterError(f"expected 'key: value': {line!r}")
        key, _, rest = line.partition(":")
        key = key.strip()
        rest = rest.strip()
        if key in fields:
            raise FrontmatterError(f"duplicate key '{key}'")
        i += 1
        # Collect indented continuation lines.
        child = []
        while i < len(lines) and (lines[i].strip() == "" or lines[i][0].isspace()):
            child.append(lines[i])
            i += 1
        if rest in (">", ">-", ">+", "|", "|-", "|+"):
            fields[key] = _block_scalar(child, rest)
        elif rest == "":
            items = [c for c in child if c.strip()]
            if not items:
                fields[key] = ""
            elif all(c.lstrip().startswith("- ") or c.strip() == "-" for c in items):
                fields[key] = [_scalar(c.lstrip()[1:]) for c in items]
            else:
                nested = {}
                for c in items:
                    ck, sep, cv = c.strip().partition(":")
                    if not sep:
                        raise FrontmatterError(f"expected nested 'key: value' under {key}: {c!r}")
                    nested[ck.strip()] = _scalar(cv)
                fields[key] = nested
        else:
            if any(c.strip() for c in child):
                raise FrontmatterError(f"unexpected indented lines after '{key}: {rest}'")
            fields[key] = _scalar(rest)
    return fields, body


def frontmatter_text(path: Path) -> str:
    """Raw frontmatter block, for checks that need the unparsed (unquoted) source."""
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---", 4)
    return text[4:end] if text.startswith("---\n") and end != -1 else ""


def load_frontmatter(path: Path, report: Report) -> tuple[dict, str] | None:
    try:
        parsed = parse_frontmatter(path.read_text(encoding="utf-8"))
    except FrontmatterError as exc:
        report.error(path, f"frontmatter parse error: {exc}")
        return None
    if parsed is None:
        report.error(path, "missing YAML frontmatter")
    return parsed


# --- Checks --------------------------------------------------------------------

def check_plugin_json(root: Path, report: Report) -> None:
    path = root / "plugin.json"
    if not path.is_file():
        report.error(path, "missing plugin.json")
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report.error(path, f"invalid JSON: {exc}")
        return
    if not isinstance(data, dict):
        report.error(path, "top level must be an object")
        return
    extra = set(data) - PLUGIN_JSON_KEYS
    if extra:
        report.error(path, f"keys not allowed by schema: {sorted(extra)}")
    name = data.get("name")
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        report.error(path, f"name must match ^[A-Za-z0-9_-]+$ (got {name!r})")


def as_list(value) -> list | None:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return None


def check_agents(root: Path, report: Report) -> tuple[list[str], dict[str, str]]:
    names = []
    models: dict[str, str] = {}
    agents_dir = root / "agents"
    if not agents_dir.is_dir():
        report.error(agents_dir, "missing agents/ directory")
        return names, models
    for path in sorted(agents_dir.glob("*.md")):
        names.append(path.stem)
        parsed = load_frontmatter(path, report)
        if parsed is None:
            continue
        fm, _ = parsed
        for key in ("name", "description"):
            if not fm.get(key):
                report.error(path, f"missing required '{key}'")
        if fm.get("name") and fm["name"] != path.stem:
            report.error(path, f"name '{fm['name']}' does not match filename '{path.stem}'")
        for key in sorted(AGENT_FORBIDDEN_KEYS & set(fm)):
            report.error(path, f"Claude-only key '{key}'")

        tools = as_list(fm.get("tools"))
        if tools is None:
            report.error(path, "tools must be a list")
            tools = []
        for tool in tools:
            if tool not in VALID_TOOLS:
                report.error(path, f"unknown tool '{tool}'")
        if len(set(tools)) != len(tools):
            report.error(path, "duplicate tool entries")

        model = fm.get("model")
        if model is not None and model not in VALID_MODELS:
            report.error(path, f"model '{model}' not in {sorted(VALID_MODELS)}")
        if model is None:
            report.error(path, "missing 'model' (set-model-profile.sh needs it)")
        else:
            models[path.stem] = model

        for key in AGENT_REQUIRED_KEYS:
            if key not in fm:
                report.error(path, f"missing required '{key}'")

        policy = fm.get("commandExecutionPolicy")
        if POLICY_LINE_RE.search(frontmatter_text(path)):
            report.error(path, 'commandExecutionPolicy: off is a YAML 1.1 boolean; quote it as commandExecutionPolicy: "off"')
        if policy is not None and policy not in VALID_POLICIES:
            report.error(path, f"commandExecutionPolicy '{policy}' not in {sorted(VALID_POLICIES)}")
        if "run_command" in tools and policy != "sandbox":
            report.error(path, f"run_command granted but commandExecutionPolicy is {policy!r}; it must be 'sandbox'")
        if (
            "run_command" not in tools
            and policy is not None
            and policy is not False  # unquoted off, already reported above
            and policy != "off"
        ):
            report.error(path, f"no run_command granted but commandExecutionPolicy is {policy!r}; it must be \"off\"")

        for key in ("mainAgent", "subagent"):
            if key in fm and not isinstance(fm[key], bool):
                report.error(path, f"{key} must be true or false")
        # Antigravity: mainAgent = selectable as the primary chat agent. No plugin agent holds
        # invoke_subagent/ask_question, and routing sends prompts to /do, so none may be a main agent.
        if fm.get("mainAgent") is not False:
            report.error(path, "mainAgent must be false (agents are subagents only; /do is the entry point)")

        skills = as_list(fm.get("skills"))
        if skills is None:
            report.error(path, "skills must be a list")
            skills = []
        for skill in skills:
            if not (root / str(skill) / "SKILL.md").is_file():
                report.error(path, f"skill path '{skill}' has no SKILL.md")
    return names, models


def check_skills(root: Path, report: Report) -> None:
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        report.error(skills_dir, "missing skills/ directory")
        return
    for folder in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
        path = folder / "SKILL.md"
        if not path.is_file():
            report.error(folder, "skill folder has no SKILL.md")
            continue
        parsed = load_frontmatter(path, report)
        if parsed is None:
            continue
        fm, body = parsed
        size = len(body.encode("utf-8"))
        if size >= SKILL_BODY_MAX_BYTES:
            report.error(path, f"body after frontmatter is {size} bytes; agy truncates skill bodies at about "
                               f"{SKILL_BODY_CUT_BYTES} bytes, so keep it under {SKILL_BODY_WARN_BYTES} and move "
                               "detail to references/")
        elif size >= SKILL_BODY_WARN_BYTES:
            report.warn(path, f"body after frontmatter is {size} bytes; agy truncates skill bodies at about "
                              f"{SKILL_BODY_CUT_BYTES} bytes, so keep it under {SKILL_BODY_WARN_BYTES} to leave "
                              "room for agy's preamble")
        desc = fm.get("description")
        if not isinstance(desc, str) or not desc.strip():
            report.error(path, "missing or empty 'description'")
        name = fm.get("name")
        if name is not None:
            if name != folder.name:
                report.error(path, f"name '{name}' does not match folder '{folder.name}'")
            if not re.fullmatch(r"[a-z0-9-]+", str(name)):
                report.error(path, f"name '{name}' must match ^[a-z0-9-]+$")
        for key in sorted(SKILL_FORBIDDEN_KEYS & set(fm)):
            report.error(path, f"top-level key '{key}' is Claude-only (move under metadata: or drop)")
        meta = fm.get("metadata")
        if meta is not None and not (isinstance(meta, dict) and all(isinstance(v, str) for v in meta.values())):
            report.error(path, "metadata must be a map of string values")
    for meta_json in sorted(skills_dir.rglob("metadata.json")):
        report.error(meta_json, "Claude-only metadata.json must be removed")


def check_rules(root: Path, report: Report) -> None:
    rules_dir = root / "rules"
    if not rules_dir.is_dir():
        return
    for path in sorted(rules_dir.glob("*.md")):
        size = path.stat().st_size
        if size >= RULE_MAX_BYTES:
            report.error(path, f"{size} bytes; rule files must be under {RULE_MAX_BYTES}")
        parsed = load_frontmatter(path, report)
        if parsed is None:
            continue
        fm, _ = parsed
        trigger = fm.get("trigger")
        if trigger not in VALID_TRIGGERS:
            report.error(path, f"trigger {trigger!r} not in {sorted(VALID_TRIGGERS)}")
        if trigger == "model_decision" and not fm.get("description"):
            report.error(path, "model_decision rules need a 'description'")
        if trigger == "glob" and not (fm.get("globs") or fm.get("glob")):
            report.error(path, "glob rules need 'globs'")


def check_profile_table(root: Path, agent_names: list[str], models: dict[str, str], report: Report) -> None:
    if not PROFILE_SCRIPT.is_file():
        report.error(PROFILE_SCRIPT, "missing set-model-profile.sh")
        return
    text = PROFILE_SCRIPT.read_text(encoding="utf-8")
    tiers = {m.group(1): m.group(2).split() for m in TIER_RE.finditer(text)}
    for tier in ("REVIEW", "BUILD", "FAST"):
        if tier not in tiers:
            report.error(PROFILE_SCRIPT, f"tier table {tier}_TIER=(...) not found")
    listed = [a for names in tiers.values() for a in names]
    for dup in sorted({a for a in listed if listed.count(a) > 1}):
        report.error(PROFILE_SCRIPT, f"agent '{dup}' appears in more than one tier")
    for tier, names in sorted(tiers.items()):
        tier_models = {a: models[a] for a in names if a in models}
        if len(set(tier_models.values())) > 1:
            detail = ", ".join(f"{a}={m}" for a, m in sorted(tier_models.items()))
            report.error(PROFILE_SCRIPT, f"agents in the {tier} tier have different models ({detail})")
    for name in sorted(set(agent_names) - set(listed)):
        report.error(root / "agents" / f"{name}.md", "agent missing from set-model-profile.sh tier table")
    for name in sorted(set(listed) - set(agent_names)):
        report.error(PROFILE_SCRIPT, f"tier table lists '{name}' but agents/{name}.md does not exist")


def iter_prose_lines(text: str):
    """Yield (line_no, line) outside fenced code blocks, with inline code removed."""
    fence = None
    for no, line in enumerate(text.split("\n"), 1):
        is_fence, fence = fence_step(line, fence)
        if not is_fence and fence is None:
            yield no, INLINE_CODE_RE.sub("", line)


def check_links(root: Path, report: Report) -> None:
    for path in sorted(root.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for no, line in iter_prose_lines(text):
            for target in LINK_RE.findall(line):
                if re.match(r"^(https?:|mailto:|#)", target):
                    continue
                rel = target.split("#", 1)[0]
                if not rel:
                    continue
                resolved = (path.parent / rel).resolve()
                if not resolved.is_relative_to(root):
                    report.error(path, f"line {no}: link '{target}' resolves outside the plugin root")
                elif not resolved.exists():
                    report.error(path, f"line {no}: broken link '{target}'")


def check_control_bytes(root: Path, report: Report) -> None:
    """ERROR on control bytes other than TAB/LF in markdown; WARN on TAB outside fenced code.

    Reads raw bytes: read_text() would turn CR LF into LF and hide the CR.
    """
    for path in sorted(root.rglob("*.md")):
        data = path.read_bytes()
        bad, tabs = [], []
        fence = None
        for no, line in enumerate(data.split(b"\n"), 1):
            for m in CONTROL_BYTES_RE.finditer(line):
                bad.append(f"{no}:0x{m.group()[0]:02x}")
            is_fence, fence = fence_step(line.decode("utf-8", "replace"), fence)
            if not is_fence and fence is None and b"\t" in line:
                tabs.append(str(no))
        if bad:
            shown = ", ".join(bad[:MAX_LOCATIONS]) + (" ..." if len(bad) > MAX_LOCATIONS else "")
            report.error(path, f"{len(bad)} control byte(s) other than TAB/LF (line:byte {shown})")
        if tabs:
            shown = ", ".join(tabs[:MAX_LOCATIONS]) + (" ..." if len(tabs) > MAX_LOCATIONS else "")
            report.warn(path, f"literal TAB outside fenced code on {len(tabs)} line(s) (lines {shown})")


def check_invisible_unicode(root: Path, report: Report) -> None:
    """ERROR on bidi controls and tag characters in markdown and plugin.json; WARN on zero-width characters and BOM."""
    paths = sorted(root.rglob("*.md"))
    if (root / "plugin.json").is_file():
        paths.append(root / "plugin.json")
    for path in paths:
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        bad, zero = [], []
        for no, line in enumerate(text.split("\n"), 1):
            for m in BIDI_TAG_RE.finditer(line):
                bad.append(f"{no}:U+{ord(m.group()):04X}")
            for m in ZERO_WIDTH_RE.finditer(line):
                if (rel, m.group()) not in ZERO_WIDTH_ALLOWED:
                    zero.append(f"{no}:U+{ord(m.group()):04X}")
        if bad:
            shown = ", ".join(bad[:MAX_LOCATIONS]) + (" ..." if len(bad) > MAX_LOCATIONS else "")
            report.error(path, f"{len(bad)} invisible bidi/tag character(s) (line:codepoint {shown})")
        if zero:
            shown = ", ".join(zero[:MAX_LOCATIONS]) + (" ..." if len(zero) > MAX_LOCATIONS else "")
            report.warn(path, f"{len(zero)} zero-width character(s) (line:codepoint {shown})")


def check_claude_isms(root: Path, report: Report) -> None:
    files = []
    for sub in ("agents", "skills", "rules"):
        d = root / sub
        if d.is_dir():
            files += sorted(d.rglob("*.md"))
    docs = root / "docs"
    if docs.is_dir():
        history = docs / "history"
        files += sorted(p for p in docs.rglob("*.md") if history not in p.parents)
    readme = root / "README.md"
    if readme.is_file():
        files.append(readme)
    for path in files:
        lines = [ln for ln in path.read_text(encoding="utf-8").split("\n") if CLAUDE_REF_OK not in ln]
        text = "\n".join(lines)
        fence, outside = None, []
        for ln in lines:
            is_fence, fence = fence_step(ln, fence)
            if not is_fence and fence is None:
                outside.append(ln)
        prose = "\n".join(outside)
        counts = {
            label: len(rx.findall(prose if label in PROSE_ONLY_ISMS else text)) for label, rx in CLAUDE_ISMS
        }
        found = {k: v for k, v in counts.items() if v}
        if found:
            detail = ", ".join(f"{k}={v}" for k, v in found.items())
            report.warn(path, f"Claude-isms remaining ({sum(found.values())}): {detail}")


def check_writing_standard_sync(root: Path, report: Report) -> None:
    """ERROR on every Report Writing Standard block that differs from the compact rule."""
    if not SYNC_SCRIPT.is_file():
        report.error(SYNC_SCRIPT, "writing-standard sync script not found")
        return
    spec = importlib.util.spec_from_file_location("sync_writing_standard", SYNC_SCRIPT)
    if spec is None or spec.loader is None:
        report.error(SYNC_SCRIPT, "cannot load the writing-standard sync script")
        return
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except (Exception, SystemExit) as exc:  # a broken sync script must yield an ERROR line, not a traceback or a silent exit
        report.error(SYNC_SCRIPT, f"cannot load ({exc.__class__.__name__}: {exc})")
        return
    missing = [name for name in ("load_compact", "drifted_files", "SyncError", "COMPACT_REL")
               if not hasattr(module, name)]
    if missing:
        report.error(SYNC_SCRIPT, f"missing {', '.join(missing)}")
        return
    try:
        bullets = module.load_compact(root)
        drifted, _, _ = module.drifted_files(root, bullets)
    except module.SyncError as exc:
        report.error(root / module.COMPACT_REL, str(exc))
        return
    except (Exception, SystemExit) as exc:
        report.error(SYNC_SCRIPT, f"failed ({exc.__class__.__name__}: {exc})")
        return
    for path, _ in drifted:
        report.error(path, f"Report Writing Standard block differs from {module.COMPACT_REL} "
                           "(run python3 scripts/sync-writing-standard.py)")


def split_row(line: str) -> list[str]:
    """Split a markdown table row on pipes outside backtick spans; strip each cell."""
    cells, current, in_code = [], [], False
    for char in line.strip().strip("|"):
        if char == "`":
            in_code = not in_code
        if char == "|" and not in_code:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    cells.append("".join(current).strip())
    return cells


def section_lines(lines: list[str], heading: str) -> list[str]:
    """Lines after the first exact `heading` line, up to the next heading of the same or higher level."""
    level = len(heading) - len(heading.lstrip("#"))
    for index, line in enumerate(lines):
        if line.rstrip() == heading:
            out, fence = [], None
            for later in lines[index + 1:]:
                _, fence = fence_step(later, fence)
                stripped = later.lstrip("#")
                if (fence is None and later.startswith("#") and stripped.startswith(" ")
                        and len(later) - len(stripped) <= level):
                    break
                out.append(later)
            return out
    return []


def parse_states_table(lines: list[str]) -> list[list[str]] | None:
    """Rows of the `## States` table, or None when the file has no such table."""
    section = section_lines(lines, "## States")
    for index, line in enumerate(section):
        if STATES_HEADER_RE.match(line.strip()):
            rows = []
            for row in section[index + 1:]:
                if not row.startswith("|"):
                    break
                cells = split_row(row)
                if all(set(c) <= set("-: ") for c in cells):
                    continue
                rows.append(cells)
            return rows
    return None


class FsaTable:
    """A parsed States table: ordered states, terminal names, and outcome edges."""

    def __init__(self, rows: list[list[str]]):
        self.order: list[str] = []
        self.kinds: dict[str, str] = {}
        self.terminals: list[str] = []
        self.edges: dict[str, list[tuple[str, str | None]]] = {}
        for cells in rows:
            if len(cells) != 4:
                continue
            name, kind, _, outcome = cells
            if kind == "terminal":
                self.terminals += [t.strip() for t in name.split(",") if t.strip()]
                continue
            self.order.append(name)
            self.kinds[name] = kind
            targets = []
            for edge in outcome.split(";"):
                match = EDGE_TARGET_RE.search(edge)
                if match:
                    targets.append((match.group(1), match.group(2)))
            self.edges[name] = targets


def check_fsa_table(rel: str, table: FsaTable, raw_rows: list[list[str]], report: Report, path: Path) -> None:
    is_do = rel == DO_SKILL
    first, kinds = ("Ingest", FSA_KINDS | {"call", "ask"}) if is_do else ("Intake", FSA_KINDS)
    classes = FSA_ERROR_CLASSES | ({"plan-invalid"} if is_do else set())
    for cells in raw_rows:
        if len(cells) != 4:
            report.error(path, f"States table row has {len(cells)} cells, expected 4: {cells[0] if cells else ''}")
        elif cells[1] not in kinds:
            report.error(path, f"States table: state {cells[0]} has unknown kind {cells[1]!r}")
    if not table.order or table.order[0] != first or table.kinds.get(first) != "check":
        report.error(path, f"States table: the first state must be {first} with kind check")
    if not table.terminals:
        report.error(path, "States table: no terminal row")
    known = set(table.order) | set(table.terminals) | {"NeedsInput"}
    for state, targets in table.edges.items():
        if not targets:
            report.error(path, f"States table: state {state} has no outcome edge")
        for target, error_class in targets:
            if target == "Error":
                if error_class is None or error_class not in classes - {"none"}:
                    report.error(path, f"States table: {state} -> Error needs a class from the closed list "
                                       f"(got {error_class!r})")
            elif error_class is not None or target not in known:
                report.error(path, f"States table: {state} -> {target} is not a state, a terminal, or NeedsInput")


def fsa_blocks(lines: list[str]) -> list[tuple[int, list[str]]]:
    """(1-based line of the fence, block lines) for every ```fsa fenced block."""
    blocks, index = [], 0
    while index < len(lines):
        if lines[index].strip() == "```fsa":
            start, body = index + 1, []
            index += 1
            while index < len(lines) and lines[index].strip() != "```":
                body.append(lines[index])
                index += 1
            if index >= len(lines):
                body.append(None)  # unclosed
            blocks.append((start, body))
        index += 1
    return blocks


def check_fsa_block(path: Path, line_no: int, body: list, table: FsaTable | None, report: Report) -> None:
    where = f"fsa block at line {line_no}"
    if body and body[-1] is None:
        report.error(path, f"{where}: fence is not closed")
        return
    fields = []
    for line in body:
        key, sep, value = line.partition(":")
        if not sep:
            report.error(path, f"{where}: line {line!r} is not a 'field: value' pair")
            return
        fields.append((key.strip(), value.strip()))
    values = dict(fields)
    if values.get("fsa") == FSA_PLACEHOLDER:
        return
    if tuple(k for k, _ in fields) != FSA_FIELDS:
        report.error(path, f"{where}: fields must be {', '.join(FSA_FIELDS)} in that order")
        return
    state, error_class = values["state"], values["error_class"]
    if state not in FSA_STATES:
        report.error(path, f"{where}: state {state!r} is not Done, NeedsInput, or Error")
    if error_class not in FSA_ERROR_CLASSES:
        report.error(path, f"{where}: error_class {error_class!r} is not in the closed list")
    elif (error_class == "none") != (state != "Error"):
        report.error(path, f"{where}: error_class must be none unless state is Error, and set when it is")
    if state != "NeedsInput":
        for key in ("questions", "resume_at"):
            if values[key] != "none":
                report.error(path, f"{where}: {key} must be none unless state is NeedsInput")
    if table is None:
        return
    trace = [t.strip() for t in values["trace"].split(">")]
    if not table.order or trace[0] != table.order[0]:
        report.error(path, f"{where}: trace must start at {table.order[0] if table.order else 'the first state'}")
    if trace[-1] != state:
        report.error(path, f"{where}: trace must end at the block's state ({state})")
    for current, following in zip(trace, trace[1:]):
        targets = {t for t, _ in table.edges.get(current, [])}
        if following not in targets:
            report.error(path, f"{where}: trace step {current} > {following} follows no outcome edge")


def check_fsa(root: Path, report: Report) -> None:
    """ERROR on malformed States tables and fsa terminal blocks (port of upstream check-fsa-tables.js)."""
    def rel(path: Path) -> str:
        return path.relative_to(root).as_posix()

    files = sorted((root / "agents").glob("*.md")) if (root / "agents").is_dir() else []
    if (root / "skills").is_dir():
        files += sorted((root / "skills").rglob("*.md"))
    tables: dict[str, FsaTable] = {}
    text_lines: dict[str, list[str]] = {}
    for path in files:
        lines = path.read_text(encoding="utf-8").split("\n")
        text_lines[rel(path)] = lines
        is_owner = path.parent.name == "agents" or path.name == "SKILL.md"
        rows = parse_states_table(lines) if is_owner else None
        if rows is None:
            continue
        table = FsaTable(rows)
        tables[rel(path)] = table
        check_fsa_table(rel(path), table, rows, report, path)
        if rel(path) == DO_SKILL:
            continue
        expected = ("developer-tester" if rel(path) == CREATE_TEST_SKILL
                    else path.stem if path.parent.name == "agents" else path.parent.name)
        example = fsa_blocks(section_lines(lines, "### Terminal block"))
        if not example:
            report.error(path, "has a States table but no ### Terminal block section with an fsa block")
            continue
        name = next((ln.partition(":")[2].strip() for ln in example[0][1] if ln and ln.startswith("fsa:")), "")
        if name.split("/")[0] != expected:
            report.error(path, f"### Terminal block example names fsa {name!r}; expected {expected}/N")
    for key, lines in text_lines.items():
        for line_no, body in fsa_blocks(lines):
            name = next((ln.partition(":")[2].strip() for ln in body if ln and ln.startswith("fsa:")), "")
            table = tables.get(CREATE_TEST_SKILL) if name.startswith("developer-tester/") else tables.get(key)
            check_fsa_block(root / key, line_no, body, table, report)
    template = text_lines.get(FSA_TEMPLATE)
    if template is None:
        report.error(root / FSA_TEMPLATE, "fsa template not found")
        return
    terminal = fsa_blocks(section_lines(template, "## Terminal block"))
    dispatch = fsa_blocks(section_lines(template, "### Dispatch prompt text"))
    if not terminal or not dispatch or terminal[0][1] != dispatch[0][1]:
        report.error(root / FSA_TEMPLATE, "the Dispatch prompt text block must equal the Terminal block template")


def check_prose_tells(root: Path, report: Report) -> None:
    """WARN on em dashes and curly quotes in plugin markdown prose."""
    for path in sorted(root.rglob("*.md")):
        if path.name == "CHANGELOG.md":
            continue
        hits = []
        for no, line in iter_prose_lines(path.read_text(encoding="utf-8")):
            if PROSE_TELL_RE.search(DOUBLE_QUOTED_RE.sub("", line)):
                hits.append(str(no))
        if hits:
            shown = ", ".join(hits[:MAX_LOCATIONS]) + (" ..." if len(hits) > MAX_LOCATIONS else "")
            report.warn(path, f"em dash or curly quote in prose on {len(hits)} line(s) (lines {shown}); "
                              "see rules/writing-standard.md")


def main(argv: list[str]) -> int:
    if len(argv) > 2 or (len(argv) == 2 and argv[1] in ("-h", "--help")):
        print(__doc__.strip())
        return 0 if len(argv) == 2 else 2
    root = Path(argv[1]).resolve() if len(argv) == 2 else DEFAULT_PLUGIN_DIR.resolve()
    if not root.is_dir():
        print(f"ERROR {root}: plugin directory not found")
        return 1
    report = Report(root)
    check_plugin_json(root, report)
    agent_names, agent_models = check_agents(root, report)
    check_skills(root, report)
    check_rules(root, report)
    check_profile_table(root, agent_names, agent_models, report)
    check_links(root, report)
    check_control_bytes(root, report)
    check_invisible_unicode(root, report)
    check_claude_isms(root, report)
    check_writing_standard_sync(root, report)
    check_fsa(root, report)
    check_prose_tells(root, report)
    print(f"\n{report.errors} error(s), {report.warnings} warning(s) in {root}")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
