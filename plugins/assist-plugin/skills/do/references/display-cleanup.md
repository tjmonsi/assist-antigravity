# Display and Cleanup

Detail for the `do` skill's Display and Cleanup states ([../SKILL.md](../SKILL.md)). Hard rule 6 in SKILL.md opens this file with the other five reference files on the first entry to Preflight or Dispatch; do not re-open it later in the run. Cleanup follows from the same file. The Hard rules in SKILL.md apply throughout.

## Display

Present each agent's output; do not redo their work. Light formatting and stitching only. Order the reply:

1. **Failures:** each failed step with its `error_class` and reason, each step skipped because of it, each step skipped because a Testing Gate ended not-run ("Skipped: Testing Gate of step N not-run") with that reason, and each write-path finding.
2. **Results:** each completed step with its artifact paths as sources, and its `skipped:` markers.
3. **Out-of-scope requests:** each item agents reported in `out_of_scope`, as a proposed new request that needs its own approval. A test path becomes a developer-tester request. Do not dispatch any of them.
4. **Remaining steps:** when the plan is paused, the steps not yet run and the `resume <plan>` command.

Display never re-delegates. A failure stays a failure; the user decides whether a new request follows.

## Cleanup

`/do` creates no worktrees, so Cleanup only chooses the outcome and sets the plan **Status** to its terminal. Test in this order and take the first match:

1. `stopped`: a stop arrived and a step is still `pending`, the Git config guard tripped, a git command reported `git` missing, or Hard rule 6's reference text was lost. The terminal is `Paused`.
2. `some-failed-or-skipped`: no stop, and at least one step is `failed` or `skipped`, or a step's Testing Gate ended `not-run` (command denied). The terminal is `Partial`.
3. `all-completed`: every step is `completed`. The terminal is `Complete`.
