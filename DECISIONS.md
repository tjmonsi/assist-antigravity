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
