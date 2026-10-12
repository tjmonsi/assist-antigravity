#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Toni-Jan Keith Monserrat
"""Rewrite every "## Report Writing Standard" block from rules/writing-standard-compact.md.

Usage: python3 scripts/sync-writing-standard.py [--check] [plugin-dir]

  (no flag)  rewrite drifted blocks in agents/*.md and skills/**/*.md, print a summary
  --check    change nothing; exit 1 if any block differs

The bullets come from the compact rule: YAML frontmatter and the scoping paragraph before
the first bullet are skipped, and every later non-blank line must start with "- ".
A block is the heading line plus everything up to the next level-1 or level-2 heading
outside a code fence, or the end of the file. The heading line is kept as written, and so
is a trailing horizontal rule before the next heading.

A block whose body holds anything other than bullets, blank lines, and one trailing
horizontal rule is an operational error: move that text under another heading.

Exit codes: 0 in sync (or synced), 1 drift found by --check, 2 operational error.
Standard library only; requires Python 3.9 or later. Port of upstream
scripts/sync-writing-standard.js (v1.8.0).
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_PLUGIN_DIR = SCRIPT_DIR.parent / "plugins" / "assist-plugin"
COMPACT_REL = "rules/writing-standard-compact.md"
HEADING_RE = re.compile(r"^## Report Writing Standard\b")
BLOCK_END_RE = re.compile(r"^#{1,2} ")
FENCE_RE = re.compile(r"^[ \t]{0,3}(`{3,40}|~{3,40})")
FENCE_CLOSE_RE = re.compile(r"^[ \t]{0,3}[`~]{3,40}[ \t]{0,40}$")
RULE_LINE_RE = re.compile(r"^[ \t]{0,3}(?:-{3,40}|\*{3,40}|_{3,40})[ \t]{0,40}$")
MAX_COMPACT_CHARS = 1400


class SyncError(Exception):
    """Operational error: the compact rule is malformed or no blocks exist."""


def load_compact(root: Path) -> list[str]:
    """Return the compact rule's bullet lines, or raise SyncError."""
    path = root / COMPACT_REL
    try:
        text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    except OSError as exc:
        raise SyncError(f"{COMPACT_REL}: {exc.strerror or exc}") from exc
    lines = text.split("\n")
    if lines and lines[0].strip() == "---":
        try:
            end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
        except StopIteration as exc:
            raise SyncError(f"{COMPACT_REL}: unterminated YAML frontmatter") from exc
        lines = lines[end + 1:]
    bullets: list[str] = []
    for line in lines:
        if line.startswith("- "):
            bullets.append(line.rstrip())
        elif bullets and line.strip():
            raise SyncError(f"{COMPACT_REL}: non-bullet line after the first bullet: {line!r}")
    if not bullets:
        raise SyncError(f"{COMPACT_REL}: no \"- \" bullet lines found")
    size = len("\n".join(bullets))
    if size > MAX_COMPACT_CHARS:
        raise SyncError(f"{COMPACT_REL}: bullets are {size} characters; the limit is {MAX_COMPACT_CHARS}")
    return bullets


def target_files(root: Path) -> list[Path]:
    """agents/*.md (not recursive) and skills/**/*.md.

    Skips symlinked files and any file whose resolved path lies outside the plugin root,
    which covers a symlinked agents/ or skills/ directory.
    """
    real_root = root.resolve()
    found: list[Path] = []

    def keep(path: Path) -> bool:
        if not path.is_file() or path.is_symlink():
            return False
        try:
            path.resolve().relative_to(real_root)
        except ValueError:
            return False
        return True

    agents = root / "agents"
    if agents.is_dir():
        found += sorted(p for p in agents.glob("*.md") if keep(p))
    skills = root / "skills"
    if skills.is_dir():
        for dirpath, dirnames, filenames in os.walk(skills, followlinks=False):
            dirnames.sort()
            for name in sorted(filenames):
                path = Path(dirpath) / name
                if name.lower().endswith(".md") and keep(path):
                    found.append(path)
    return found


def find_blocks(lines: list[str]) -> list[tuple[int, int]]:
    """Return (start, end) line ranges: start is the heading, end is one past the last line."""
    blocks: list[tuple[int, int]] = []
    fence: str | None = None
    start: int | None = None
    for index, line in enumerate(lines):
        marker = FENCE_RE.match(line)
        if fence:
            if (marker and marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence)
                    and FENCE_CLOSE_RE.match(line)):
                fence = None
            continue
        if marker:
            fence = marker.group(1)
            continue
        if start is not None and BLOCK_END_RE.match(line):
            blocks.append((start, index))
            start = None
        if HEADING_RE.match(line):
            start = index
    if start is not None:
        blocks.append((start, len(lines)))
    return blocks


def render_block(heading: str, old_body: list[str], bullets: list[str], at_end: bool) -> list[str]:
    body = list(old_body)
    while body and not body[-1].strip():
        body.pop()
    rule = body[-1] if body and RULE_LINE_RE.match(body[-1]) else None
    out = [heading, "", *bullets]
    if not at_end:
        out.append("")
        if rule:
            out += [rule, ""]
    return out


def check_block_body(path: Path | str, start: int, body: list[str]) -> None:
    """Raise SyncError if a block body holds a line that is not a bullet.

    Trailing blank lines and one trailing horizontal rule are allowed. `start` is the
    0-based index of the heading line, so body[i] sits on line start + i + 2.
    """
    end = len(body)
    while end and not body[end - 1].strip():
        end -= 1
    if end and RULE_LINE_RE.match(body[end - 1]):
        end -= 1
    for index in range(end):
        line = body[index]
        if line.strip() and not line.startswith("- "):
            raise SyncError(
                f"{path}: line {start + index + 2}: Report Writing Standard block holds "
                "non-bullet text; move it under another heading"
            )


def sync_text(text: str, bullets: list[str], path: Path | str = "<text>") -> tuple[str, int]:
    """Return (synced text, number of blocks) for one file's contents."""
    eol = "\r\n" if "\r\n" in text else "\n"  # text was read with newline="" so CRLF survives
    lines = re.split(r"\r?\n", text)
    final_newline = len(lines) > 1 and lines[-1] == ""
    if final_newline:
        lines.pop()
    blocks = find_blocks(lines)
    for start, end in blocks:
        check_block_body(path, start, lines[start + 1:end])
    for start, end in reversed(blocks):
        at_end = end == len(lines)
        lines[start:end] = render_block(lines[start], lines[start + 1:end], bullets, at_end)
    return eol.join(lines) + (eol if final_newline else ""), len(blocks)


def drifted_files(root: Path, bullets: list[str]) -> tuple[list[tuple[Path, str]], int, int]:
    """Return ([(path, synced text)] for drifted files, block count, file count)."""
    drifted: list[tuple[Path, str]] = []
    block_count = file_count = 0
    for path in target_files(root):
        with open(path, encoding="utf-8", newline="") as handle:
            original = handle.read()
        synced, blocks = sync_text(original, bullets, path.relative_to(root).as_posix())
        if not blocks:
            continue
        file_count += 1
        block_count += blocks
        if synced != original:
            drifted.append((path, synced))
    if block_count == 0:
        raise SyncError("no \"## Report Writing Standard\" blocks found under agents/ or skills/")
    return drifted, block_count, file_count


def main(argv: list[str]) -> int:
    args = argv[1:]
    if any(a in ("-h", "--help") for a in args):
        print(__doc__.strip())
        return 0
    check = "--check" in args
    rest = [a for a in args if a != "--check"]
    if len(rest) > 1 or any(a.startswith("-") for a in rest):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    root = Path(rest[0]).resolve() if rest else DEFAULT_PLUGIN_DIR.resolve()
    try:
        if not root.is_dir():
            raise SyncError(f"{root}: plugin directory not found")
        bullets = load_compact(root)
        drifted, block_count, file_count = drifted_files(root, bullets)
        if not check:
            for path, synced in drifted:
                with open(path, "w", encoding="utf-8", newline="") as handle:
                    handle.write(synced)
    except (SyncError, OSError, UnicodeDecodeError) as exc:
        print(f"sync-writing-standard: {exc}", file=sys.stderr)
        return 2
    verb = "differ from" if check else "rewritten from"
    print(f"{block_count} block(s) in {file_count} file(s); {len(drifted)} {verb} {COMPACT_REL}.")
    for path, _ in drifted:
        print(f"  {path.relative_to(root).as_posix()}")
    return 1 if check and drifted else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
