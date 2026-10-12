# Agent Registry

Source of truth for all agents in assist-plugin. Used by `do` skill for routing.

## All Agents (14)

Tool shorthand (the authoritative list is each agent file's `tools` frontmatter):
- **read** = `view_file`, `list_dir`, `grep_search`, `find_by_name`
- **edit** = `write_to_file`, `replace_file_content`, `multi_replace_file_content`
- **shell** = `run_command` (granted only with `commandExecutionPolicy: sandbox`; every other agent has `commandExecutionPolicy: off`)
- **web** = `search_web`, `read_url_content`

Tier values are for the shipped `gemini` profile; see [model-routing.md](model-routing.md) for the `inherit` profile.

| Agent | Responsibilities | Tier (`gemini`) | Tools | Primary Intent Match |
|-------|------------------|-----------------|-------|----------------------|
| **ask** | Answer questions using repo search + web research | build (`flash`) | read, web | "answer my question", "research this in repo", "find documentation" |
| **developer** | Write/fix/refactor code; implement features; apply approved fixes; apply code skill standards (logging, error-handling, traceability) | build (`flash`) | read, edit, shell | "implement X", "fix bug in Y", "refactor Z" |
| **developer-tester** | Create black-box tests from acceptance criteria; test input/output only, never implementation knowledge; use create-test skill | build (`flash`) | read, `write_to_file` | "write tests for X", "create test plan from acceptance criteria" |
| **reviewer** | Code review for bugs/security/quality; OWASP checks; approve/revise | review (`pro`) | read | "review this PR", "check for security", "OWASP compliance" |
| **planner** | Architecture design; roadmap; dependency analysis; risk assessment | build (`flash`) | read, edit | "design architecture", "create roadmap", "how should we structure" |
| **qa** | Test planning; manual/automated test design; acceptance validation; coverage; orchestrate pentest, integrated-test, and run-test skills | build (`flash`) | read, edit, shell | "create test plan", "write automated tests", "validate acceptance" |
| **solutions-architect** | API/schema design; data flows; error handling; specs; Mermaid diagram source embedded in specs (PNG rendering with `mmdc` is left to the user or devops) | review (`pro`) | read, edit | "design API", "what should schema be", "data flow for X" |
| **requirements-gatherer** | Requirements elicitation; BRD/URD; FR+NFR; acceptance criteria | build (`flash`) | read, edit | "gather requirements", "create BRD", "define acceptance criteria" |
| **devops** | CI/CD pipelines; infrastructure (Terraform/Docker); deployment; monitoring | build (`flash`) | read, edit, shell | "set up CI/CD", "create Terraform", "deploy X" |
| **researcher** | Web research; documentation audit; best practices; competitive analysis | review (`pro`) | read, edit, web | "research X library", "best practices for Y", "compare solutions" |
| **code-reviewer** | Formal line-by-line review; critical sign-off; architectural evaluation | review (`pro`) | read | "formal review", "critical change approval", "senior review needed" |
| **explore** | Code search; find definitions; grep symbols; locate callers | fast (`flash`) | read | "find where X defined", "who calls this", "search for pattern" |
| **general-purpose** | Catch-all for unmatched tasks; ad-hoc analysis; experimentation | build (`flash`) | read, edit, shell | "what's the best approach", "help me understand X" |
| **worker** | Multi-discipline: code + test + review combined for small features | build (`flash`) | read, edit, shell | "implement and test", "quick fix with tests", "add logging to X" |

---

## Agent-Specific Skills

Skills the orchestrator should name in the task prompt when it routes to these agents.

| Agent | Skill | What it provides |
|-------|-------|------------------|
| **requirements-gatherer** | `gather-requirements` (`skills/gather-requirements`) | Elicitation methodology, BRD/URD/FR-NFR templates, quality checklist, `BR/UR/FR/NFR-NNN` IDs, GIVEN/WHEN/THEN acceptance criteria, JSON output |
| **solutions-architect** | `spec-from-requirements` (`skills/spec-from-requirements`) | Classify-first spec templates (Architecture, API endpoint, Frontend action, Functionality, UI/UX design, General), Requirement/Scenario format, ADDED/MODIFIED/REMOVED delta mode, OpenAPI and JSON output, cloud patterns |
| **developer** | `task-plan` (`skills/task-plan`) | Spec-to-task-plan converter: ordered implementation steps with decision trees, dependency graphs, critical path; loads code skill references for the developer to apply |
| **developer** | `code` (`skills/code/references`) | Language/framework standards, logging patterns, error-handling conventions, and traceability markers per [TRACING_MARKERS.md](../../../docs/TRACING_MARKERS.md); loaded by developer during implementation |
| **developer-tester** | `create-test` (`skills/create-test`) | Black-box test generation from acceptance criteria and spec scenarios; never uses implementation knowledge; produces unit/integration/E2E skeletons |
| **qa** | `pentest` (`skills/pentest`) | OWASP Top 10 + LLM OWASP testing; vulnerability discovery and reporting; dependency security audit; compliance checks |
| **qa** | `integrated-test` (`skills/integrated-test`) | Integration and E2E testing; Playwright patterns and container test fixtures; test environment setup and teardown |
| **qa** | `run-test` (`skills/run-test`) | Test execution orchestration; coverage capture and analysis; consolidated test report generation |

The chain: `gather-requirements` → `spec-from-requirements` → `task-plan`. Requirements emits `BR/UR/FR/NFR-NNN` IDs that specs cite in **Requirement refs**, and `task-plan` uses them to trace implementation steps per [TRACING_MARKERS.md](../../../docs/TRACING_MARKERS.md). Route requirements before specs before task-plans in multi-step work.

---

## Routing Decision Tree

```
User task → /do
  ↓
Classify primary intent:

Is it a QUESTION, or does it need REPO/WEB RESEARCH TO ANSWER (not implement)?
  └─ Answer question / find documentation / look something up? → ask

Is it about CODE IMPLEMENTATION?
  ├─ Need a development task-plan before coding? → task-plan (then route implementation to developer)
  ├─ Large feature? → developer + qa + reviewer (split)
  ├─ Small feature? → worker (end-to-end)
  ├─ Quick fix? → developer
  └─ Refactor? → developer

Is it about CODE REVIEW?
  ├─ Formal approval? → code-reviewer
  ├─ Standard review? → reviewer
  └─ Just check? → reviewer

Is it about ARCHITECTURE/DESIGN?
  ├─ System design? → planner
  ├─ API/schema design? → solutions-architect
  └─ Feature spec? → solutions-architect

Is it about REQUIREMENTS?
  └─ Gather/document? → requirements-gatherer

Is it about TESTING?
  ├─ Black-box test design from acceptance criteria? → developer-tester
  ├─ Security/pentest? → qa
  ├─ Integration/E2E testing? → qa
  ├─ Test execution + coverage? → qa
  ├─ Test plan? → qa
  └─ Acceptance? → qa

Is it about INFRASTRUCTURE/DEVOPS?
  └─ CI/CD/deployment/monitoring? → devops

Is it about RESEARCH/DISCOVERY?
  ├─ Technical research? → researcher
  ├─ Find code location? → explore
  └─ Learn best practices? → researcher

Is it about MULTI-DISCIPLINE or SMALL TASKS?
  ├─ Code + test + review combined? → worker
  └─ Unmatched/ad-hoc? → general-purpose

No clear match?
  └─ general-purpose (fallback)
```

---

## Model Tier Guidance

| Tier | `gemini` profile | When to Use | Agents |
|------|------------------|-------------|--------|
| **fast** | `flash` | Simple operations, pure search | explore |
| **build** | `flash` | Most development work, analysis, planning | ask, developer, developer-tester, planner, qa, requirements-gatherer, devops, general-purpose, worker |
| **review** | `pro` | Complex decisions, security, formal review | reviewer, code-reviewer, solutions-architect, researcher |

The orchestrator (`do`) runs on the model the user selected in Antigravity's model selector, not on a tier. Planner sits on the build tier; see [model-routing.md](model-routing.md#planner-on-the-build-tier) for rationale. Move it to `pro` for high-stakes or highly ambiguous architecture (see Model Tier Changes below).

---

## Model Tier Changes

Before plan approval, the `do` orchestrator reports each planned agent's tier, read from the `model` field in its agent file:

```
Plan includes these agents:
- developer [build: flash]
- reviewer [review: pro]
- qa [build: flash]

Change model tiers? (y/n)
```

The agent file's `model:` line overrode `invoke_subagent`'s per-call `Model` parameter in every test on `agy` 1.3.3, so the orchestrator omits `Model`, and a change means editing the agent file's `model:` line or running `scripts/set-model-profile.sh <gemini|inherit|gemini-pro|gemini-flash> [plugin-dir]` from the assist-antigravity repository before execution starts.

**Guidance:**
- Prefer the build tier plus one extra review iteration over moving work to `pro`
- Move to `pro` for security-critical or architectural decisions
- Keep pure search and lookup (explore agent) on the fast tier
