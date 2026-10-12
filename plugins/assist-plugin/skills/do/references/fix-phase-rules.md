# Fix Phase Constraints

Rules governing the fix phase that follows a reviewer's request for changes. Applies to every review gate (Pre-Test, OWASP, Testing, Code Review, Planning Document).

---

## Rule 1: Build Tier for Fixes

Fix phase ALWAYS runs on the build tier (`flash` under the shipped `gemini` profile). Never the review tier. Never a lighter model than the build tier.

This applies regardless of:
- Which tier reviewed the code (reviewer and code-reviewer sit on the review tier; fixes still run on the build tier)
- Which tier wrote the original code (developer already sits on the build tier)
- How small or large the fix appears

Antigravity sets a subagent's model from its agent file, so the orchestrator meets this rule by routing fixes to a build-tier agent (developer, developer-tester, devops, planner, requirements-gatherer, or worker). When the reviewed document came from a review-tier creator (solutions-architect or researcher), the orchestrator routes the findings list to planner or developer instead, because the creator itself runs on the review tier. Under the `inherit` profile every agent shares the selected model, so the rule reduces to routing fixes to a build-tier agent.

### Why the Build Tier

1. **Cost and quota:** Fix phases repeat across iterations (up to 10 per gate). Running the review tier per iteration multiplies the most expensive tier across the highest-frequency step in the workflow.
2. **Speed:** The build tier returns fixes faster, reducing iteration latency. Fixes are narrow, well-defined tasks (not open-ended architecture), so the review tier's extra reasoning capacity is unnecessary.
3. **Precision:** A narrow, well-specified findings list benefits more from a fast, literal, constrained edit pass than from a heavier model's tendency to broaden scope or re-architect.

### Non-Negotiable

- Do not move a fix to the review tier even if it is described as "critical" or "security-related". The review gate (review tier) already gated on severity; the fix itself stays on the build tier.
- Do not route a fix to the fast tier (explore) even if it is a one-line change. Explore has no edit tools, and code edits need the build tier's scope discipline.

---

## Rule 1b: Route Each Finding to the Agent That May Write the File

The Write scope lets `developer` write source, config, and docs but not test paths, and lets `developer-tester` write test paths only. Route by the path a finding names:

| Finding path | Fixing agent |
|---|---|
| A test path (the globs in [developer-tester Write scope](../../../agents/developer-tester.md#write-scope)) | `developer-tester` |
| Any other path | The step's producing agent (developer, devops, planner, requirements-gatherer, worker); for a solutions-architect or researcher document, planner or developer (Rule 1) |
| Missing or failing tests reported by the Testing Gate | `developer-tester` |

A pass with findings of both kinds splits into one fix dispatch per agent, both on the build tier. The developer never adds tests, even when a finding says a test is missing. Findings from `/do`'s post-step write-path check route as the [do skill](../SKILL.md#write-path-check) says.

---

## Rule 2: Identified Items Only

"Identified items" means the reviewer's specific, itemized findings, nothing else.

### What Counts as an Identified Item

- A specific file + line number (or line range) + issue description from the reviewer's formal audit
- A specific OWASP category finding tied to a specific code location
- A specific test gap tied to a specific function/file
- A specific planning document section flagged as incomplete/incorrect

### What Does NOT Count

- Issues the developer personally notices while fixing (must be flagged, not fixed)
- Style preferences not raised by the reviewer
- Refactors that "would improve" the code but weren't requested
- Fixes to adjacent code that merely resembles the flagged issue (must be separately identified by reviewer first)

---

## Rule 3: Modification Checklist

Before submitting a fix, the fixing agent (developer, developer-tester, devops, planner, requirements-gatherer, worker) confirms ALL of the following:

1. Every changed line maps to a specific reviewer finding
2. No file is touched that wasn't named in a finding
3. No function/section is touched beyond what the finding's line range requires
4. No new files created unless the finding explicitly required one (e.g., a missing test file, which only `developer-tester` creates)
5. No formatting/linting changes outside the touched lines
6. No dependency, config, or unrelated import changes
7. Commit/diff reviewed line-by-line against the findings list before resubmitting

If any item fails this checklist, remove the unrelated change before resubmitting.

---

## Example

**Reviewer finding:**
```
File: src/services/user-service.ts
Line: 42
Issue: Null-pointer risk: `user.profile.email` accessed without checking `user.profile` exists
```

**Allowed fix:**
- Modify line 42 (and immediately adjacent lines strictly required to add the null check, e.g., wrapping in an `if` block)
- Example: change `user.profile.email` to `user.profile?.email` or add a guard clause directly around that access

**Not allowed in the same fix pass:**
- Renaming `user` to `currentUser` elsewhere in the file
- Adding null checks to other functions in `user-service.ts` not flagged by the reviewer
- Reformatting the file
- Adding new tests. The developer never adds tests; a finding about missing test coverage for this line goes to `developer-tester`
- Touching `src/services/order-service.ts` even if it has a similar pattern (must be a separate, reviewer-identified finding first)

---

## Hard Constraint: Fix Phase Failure

If the fixing agent adds unrelated changes:

1. Fix phase FAILS automatically, regardless of whether the identified items were also correctly fixed
2. Reviewer rejects the entire fix submission (not just the unrelated portion)
3. Fix phase re-iterates: fixing agent resubmits with ONLY the identified items addressed
4. The failed attempt counts toward the gate's iteration limit (max 10, see review-protocol.md)
5. Repeated scope violations (2+ in the same gate) escalate to code-reviewer for review of the fixing agent's output before continuing
6. A gate that reaches its bound ends as review-protocol.md describes: one code-reviewer pass with a binding verdict, and `returned` fails the step

---

## Procedure Summary

1. Reviewer issues itemized findings (file, line, issue)
2. Orchestrator waits for running code-writing subagents to finish and pauses new ones, takes the pre-fix tree snapshot, then assigns each finding to the build-tier agent that may write its path (Rule 1b; `Model: flash` in the plan under the `gemini` profile)
3. Fixing agent runs the Modification Checklist before submitting
4. Fixing agent submits diff scoped strictly to findings
5. Orchestrator passes the Relevant Files' diff sections (selected by the path-matching rule from the fixed `git diff` output, see [review-protocol.md](review-protocol.md#path-matching)), the fix delta (`git --no-pager -c core.fsmonitor=false -c core.hooksPath=/dev/null -c safe.bareRepository=explicit diff --no-ext-diff --no-textconv <before> <after> -- . ':(exclude).agent' ':(exclude)DECISIONS.md'`, minus the prefixed `.agent` and `DECISIONS.md` paths per [Path matching](review-protocol.md#path-matching), between the pre-fix and post-fix tree snapshots, see [review-protocol.md](review-protocol.md#fix-delta-snapshots) for fallbacks without `HEAD` or without git), and the findings list to the reviewer; reviewer re-audits: verifies findings resolved AND scans the fix delta for unrelated changes
6. Unrelated changes present: reject, re-iterate (step 2)
7. Diff scoped correctly and findings resolved: proceed to next review iteration

---

## See Also

- [review-protocol.md](review-protocol.md): Full review gate workflow and iteration tracking
- [model-routing.md](model-routing.md): Model tier assignment for all agents
- [developer-self-review.md](developer-self-review.md): Pre-review self-audit checklist
