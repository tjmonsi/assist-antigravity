#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Toni-Jan Keith Monserrat
"""Validate assist-plugin against the documented Antigravity plugin formats.

Usage: python3 scripts/validate.py [plugin-dir]

Standard library only. Prints `ERROR <file>: <reason>` and `WARN <file>: <reason>`
lines, then a summary. Exits 1 if any ERROR was reported.
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
]
# These two patterns also occur legitimately inside fenced code (SQL placeholders such as $1,
# Rust macros), so they are checked outside fenced code blocks only.
PROSE_ONLY_ISMS = {"$0/$1 positional args", "!`cmd` dynamic context"}
# Lines carrying this marker (upstream-to-Antigravity mapping tables, attribution) are skipped.
CLAUDE_REF_OK = "<!-- claude-ref-ok -->"

LINK_RE = re.compile(r"(?<!!)\[[^\]\n]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
POLICY_LINE_RE = re.compile(r"^commandExecutionPolicy:\s*(?:off|Off|OFF)\s*(?:#.*)?$", re.M)
TIER_RE = re.compile(r"^(REVIEW|BUILD|FAST)_TIER=\(([^)]*)\)\s*$", re.M)
# C0 control bytes other than TAB (0x09) and LF (0x0a). CR is included: plugin files use LF only,
# and a stray CR (or BS/FF) usually means a "\r"/"\b"/"\f" escape was interpreted while writing.
CONTROL_BYTES_RE = re.compile(rb"[\x00-\x08\x0b-\x1f]")
FENCE_BYTES_RE = re.compile(rb"^\s*(```|~~~)")
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
        fm, _ = parsed
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
    in_fence = False
    for no, line in enumerate(text.split("\n"), 1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
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
        in_fence = False
        for no, line in enumerate(data.split(b"\n"), 1):
            for m in CONTROL_BYTES_RE.finditer(line):
                bad.append(f"{no}:0x{m.group()[0]:02x}")
            if FENCE_BYTES_RE.match(line):
                in_fence = not in_fence
            elif not in_fence and b"\t" in line:
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
        in_fence, outside = False, []
        for ln in lines:
            if FENCE_RE.match(ln):
                in_fence = not in_fence
            elif not in_fence:
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
    spec.loader.exec_module(module)
    try:
        bullets = module.load_compact(root)
        drifted, _, _ = module.drifted_files(root, bullets)
    except module.SyncError as exc:
        report.error(root / module.COMPACT_REL, str(exc))
        return
    for path, _ in drifted:
        report.error(path, f"Report Writing Standard block differs from {module.COMPACT_REL} "
                           "(run python3 scripts/sync-writing-standard.py)")


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
    check_prose_tells(root, report)
    print(f"\n{report.errors} error(s), {report.warnings} warning(s) in {root}")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
