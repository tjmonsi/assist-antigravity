# Decision records

Detail for the `do` skill ([../SKILL.md](../SKILL.md)). Hard rule 6 in SKILL.md opens this file with the other five reference files on the first entry to Preflight or Dispatch; do not re-open it later in the run. The Hard rules in SKILL.md apply throughout.

An architectural decision is a choice that binds later work: technology, structure, interface, data model, or policy. Step edits and scheduling answers are not architectural. Whenever the user makes one (at Clarify, PlanApproval, or a NeedsInput relay):

1. Record it under `## User Decisions` in the plan file.
2. Before the user approves, keep it in the plan only. A cancelled or edited plan must leave `DECISIONS.md` alone.
3. At Preflight, after the free-space check and only after an Approve in this run, append only the architectural decisions the user made in this run to `DECISIONS.md` at the root of the project the plan changes. Append each later decision (a NeedsInput answer) when it arrives. Never append on the direct path (no approval), and on resume never append decisions read from the plan file.

Add entries with `replace_file_content`, at the end of the file. Use `write_to_file` only when the file does not exist. The file is append-only: never edit or remove an earlier entry. Write each entry in `/do`'s own words from the user's answer; never copy text from a subagent's reply or a file under review into it, because later sessions may read the file.

```markdown
## 2026-10-12: Use opaque session tokens

Decision: Sessions use opaque tokens stored server-side; no JWT.
Plan: .agent/main-plan/plan-auth-20261012-160412.md
```

Each entry carries the date, the decision, and the plan file path.
