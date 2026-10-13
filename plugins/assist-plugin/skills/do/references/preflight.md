# Preflight

Detail for the `do` skill's Preflight state ([../SKILL.md](../SKILL.md)). Hard rule 6 in SKILL.md opens this file with the other five reference files on the first entry to Preflight or Dispatch; do not re-open it later in the run. The Hard rules in SKILL.md apply throughout. See also [constraints.md](constraints.md).

Before dispatching any agent, check free space on the repo filesystem from the main worktree with `run_command`:

```bash
df -h .
```

If available space is under 2G, tell the user how much is free and ask with `ask_question` whether to continue. Mention ways the user can free space (for example `go clean -cache`, or `/branch cleanup --dry-run` to preview finished worktrees). Do not delete anything as part of the preflight. If the user stops here, set the plan **Status** to `Cancelled`.

Then, just before setting the plan **Status** to `In Progress`, append to `DECISIONS.md` as [decision-records.md](decision-records.md) says, only after an Approve in this run and only the architectural decisions the user made in this run (nothing to append when there are none). Never append on the direct path (no approval), and on resume never append decisions read from the plan file. A stop at the disk prompt leaves `DECISIONS.md` alone. Then set the plan **Status** to `In Progress`.
