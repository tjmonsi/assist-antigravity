# Decisions

## 2026-10-12: Review gates end in a binding code-reviewer pass

Decision: A `/do` review gate that reaches its iteration bound without approval ends with one code-reviewer pass whose verdict is binding (`approved` completes the step, `returned` fails it), following upstream v1.9.0. The port no longer asks the user to escalate, accept, or abort at the cap.
Plan: .agent/main-plan/plan-sync-1-9-0-20261012-1104.md

## 2026-10-12: developer-tester never writes agent context files

Decision: developer-tester's instructions deny writes to `CLAUDE.md`, `AGENTS.md`, and `GEMINI.md`, in addition to non-test paths and dot folders.
Plan: .agent/main-plan/plan-sync-1-9-0-20261012-1104.md

## 2026-10-12: /do checks write paths after each step

Decision: `/do` compares the files each step changed against the step's approved Writes after the step reports, and treats a write outside them as a finding.
Plan: .agent/main-plan/plan-sync-1-9-0-20261012-1104.md

## 2026-10-12: Commit attribution rule ships as text, no hook

Decision: The port carries upstream v1.10.0's no-AI-attribution rule in `assist-plugin-rule.md`, `commit`, and `bump`, plus a one-line always-on reminder in `assist-routing.md`. It ships no `hooks.json`: agy documents no pass-through result for a PreToolUse hook, and a failing plugin hook can block every tool call.
Plan: .agent/main-plan/plan-sync-1-10-0-20261012-1554.md

## 2026-10-12: Write agents never touch agent context files

Decision: developer, devops, and worker deny writes to `AGENTS.md`, `GEMINI.md`, and `CLAUDE.md` at any depth and to any path with a `.agents` segment, with no exception for a step's approved Writes.
Plan: .agent/main-plan/plan-sync-1-10-0-20261012-1554.md

## 2026-10-12: voice-script uses its catalog first

Decision: `/voice-script` works from its built-in model catalog and fetches the OpenRouter model list only when the user asks for a live check.
Plan: .agent/main-plan/plan-sync-1-10-0-20261012-1554.md

## 2026-10-12: Write agents never touch Antigravity settings

Decision: Every write-capable agent denies writes to Antigravity settings and permission files (`~/.gemini/**`), and general-purpose, planner, researcher, requirements-gatherer, and solutions-architect join developer, devops, and worker in denying writes to `AGENTS.md`, `GEMINI.md`, `CLAUDE.md`, and `.agents` paths.
Plan: .agent/main-plan/plan-follow-ups-1-10-0-20261012-182442.md

## 2026-10-12: /commit and /bump ask before running repo git hooks

Decision: `/commit` and `/bump` always run git with `core.fsmonitor=false`. When `core.hooksPath` is set or `.git/hooks` holds non-sample files, they list them and ask whether to run with the hooks or with `core.hooksPath=/dev/null`.
Plan: .agent/main-plan/plan-follow-ups-1-10-0-20261012-182442.md

## 2026-10-12: Port-only fix releases bump the patch version

Decision: A port release with no upstream sync bumps the patch version (1.10.0 to 1.10.1) in `plugin.json` and the CHANGELOG (`[1.10.1-antigravity]`).
Plan: .agent/main-plan/plan-follow-ups-1-10-0-20261012-182442.md

## 2026-10-13: qa also denies agent context-file writes

Decision: qa joins the eight write agents that deny writes to `AGENTS.md`, `GEMINI.md`, `CLAUDE.md`, and `.agents` paths, because it holds write tools and `run_command` and reads untrusted scanner output.
Plan: .agent/main-plan/plan-follow-ups-1-10-0-20261012-182442.md

## 2026-10-13: /do loads its reference files once and appends decisions at Preflight

Decision: Because agy cuts a skill body at about 24,000 bytes, `/do` keeps Preflight, Dispatch, Display, Cleanup, Constraints, and decision records in `skills/do/references/` and opens all six files once, on first entry to Preflight or Dispatch, ending in Error(tool-failed) if one cannot be opened. The approved architectural decisions are appended to `DECISIONS.md` at the start of Preflight, after `decision-records.md` is open, instead of at Approve.
Plan: .agent/main-plan/plan-skill-size-fix-20261013-124234.md

## 2026-10-13: /do appends decisions after the Preflight disk check

Decision: Refines the entry above: `/do` appends only this run's approved architectural decisions, after the Preflight free-space check and just before setting `In Progress`, so a stop at the disk prompt leaves `DECISIONS.md` unchanged; it never appends on the direct path or from a resumed plan file.
Plan: .agent/main-plan/plan-skill-size-fix-20261013-124234.md
