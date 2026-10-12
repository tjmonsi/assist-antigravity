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
