# Constraints

The full constraint list for the `do` skill ([../SKILL.md](../SKILL.md)). Hard rule 6 in SKILL.md opens this file with the other five reference files on the first entry to Preflight or Dispatch; do not re-open it later in the run. The Hard rules in SKILL.md restate the most important of these.

- Never skip user approval. The single exception: a plan of exactly one step whose effect is `read` and whose agent is ask or explore goes straight to Preflight.
- Never resume a plan whose Status is not `Paused` or `In Progress` or whose approval is not recorded.
- Never do delivery work in the main agent. An unmatched intent goes to Clarify.
- Never run project code, tests, or builds in the main agent. Test execution belongs to qa at the Testing Gate; a step's `skipped:` marker stays in the plan and at Display until a gate's agent runs that check.
- Never write a gate result into the plan without that gate reviewer's terminal block; write `not-run` instead.
- Never start a write step before its intake review step has finished, or before the user waived the review at approval.
- Never invoke an agent without a task breakdown and context files.
- Never proceed past a failed review without re-invoking the agent. The one exception: a Testing Gate that ends `Testing Gate not-run (skipped: command denied)` is not a pass, and its step's dependents are skipped (see Review gates in [dispatch.md](dispatch.md)).
- Never dispatch an agent that is not in the approved plan. The only dispatch before approval is a read-only intake review by intake-reviewer.
- Never apply intake review findings without a user edit.
- Never add a Recommended mark or a widening option to a relayed question, and never extend an approved step with an answer.
- Never put a subagent-chosen path or string into a command.
- Keep each agent's task focused.
- Never force-remove worktrees (`git worktree remove --force`) or force-delete branches (`git branch -D`).
- Never remove worktrees or delete branches as part of a plan; worktree cleanup belongs to `/branch cleanup`, which the user runs.
- Never rewrite or delete an existing `DECISIONS.md` entry, and never write to it before approval.
