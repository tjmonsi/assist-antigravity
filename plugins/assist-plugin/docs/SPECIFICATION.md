# assist-plugin Specification

## Overview

assist-plugin is a token-optimized Google Antigravity plugin providing orchestration, 14 specialized subagents, and 18 focused skills for end-to-end software development workflows. It is the Antigravity port of the Claude Code plugin of the same name ([assist-marketplace-plugin](https://github.com/tjmonsi/assist-marketplace-plugin)).

**Models:** Each subagent's `model` field sets its tier. The shipped `gemini` profile puts reviewer, code-reviewer, researcher, and solutions-architect on `pro` and every other agent on `flash`; the `inherit` profile makes every subagent follow Antigravity's model selector. Skills run on the main agent's selected model. See [model-routing.md](../skills/do/references/model-routing.md).

**Philosophy:** Route tasks to the right agent, enable parallel execution, reduce context switching, and maintain governance gates (security + testing).

---

## Agents (14 Total)

### Core Development Agents (4)

#### developer
- **Purpose:** Write, fix, and refactor code
- **Responsibilities:**
  - Implement features from specs
  - Bug fixes from approved RCAs
  - Refactoring for clarity/performance
  - Local testing before review
  - Apply task-plan and code skill standards
- **Model default:** build tier (`flash`)
- **Tools:** `view_file`, `list_dir`, `grep_search`, `find_by_name`, `write_to_file`, `replace_file_content`, `multi_replace_file_content`, `run_command` (`commandExecutionPolicy: sandbox`)

#### developer-tester
- **Purpose:** Create black-box tests from acceptance criteria
- **Responsibilities:**
  - Write tests based only on spec acceptance criteria
  - Test input/output behavior, never implementation
  - No reading implementation files
  - Enumerate input space per acceptance criterion (valid, invalid, boundary, null/empty, type-mismatch, security-adjacent)
  - Apply traceability markers to test cases
- **Model default:** build tier (`flash`)
- **Tools:** `view_file`, `list_dir`, `grep_search`, `find_by_name`, `write_to_file` (no shell, no replace tools)

#### reviewer
- **Purpose:** Code review, quality, and security checks
- **Responsibilities:**
  - Detect bugs, architectural issues
  - Security/OWASP analysis
  - Performance and scalability review
  - Approve or request revisions
- **Model default:** review tier (`pro`)
- **Tools:** `view_file`, `list_dir`, `grep_search`, `find_by_name` (no write, no shell)

#### planner
- **Purpose:** Architecture, design, and planning
- **Responsibilities:**
  - System design and architecture
  - Implementation roadmaps
  - Dependency analysis
  - Risk assessment
- **Model default:** build tier (`flash`)
- **Tools:** `view_file`, `list_dir`, `grep_search`, `find_by_name`, `write_to_file`, `replace_file_content`, `multi_replace_file_content` (no shell)

### Testing & Quality Agents (2)

#### qa
- **Purpose:** Testing, validation, acceptance criteria, security testing
- **Responsibilities:**
  - Orchestrate test execution (unit, integration, e2e, security)
  - Run pentest (via `pentest` skill)
  - Run integration/E2E tests (via `integrated-test` skill)
  - Run all test suites and collect coverage (via `run-test` skill)
  - Acceptance criteria validation
  - Regression detection
  - Playwright availability check before frontend testing
  - Report output uses consolidated test report template
- **Model default:** build tier (`flash`)
- **Tools:** `view_file`, `list_dir`, `grep_search`, `find_by_name`, `write_to_file`, `replace_file_content`, `multi_replace_file_content`, `run_command` (`commandExecutionPolicy: sandbox`)

#### solutions-architect
- **Purpose:** Feature spec, data flow, API contracts
- **Responsibilities:**
  - Translate requirements to detailed specs
  - API/schema design
  - Data flow diagrams
  - Error handling strategy
  - Mermaid diagram source in specs (PNG rendering with `mmdc` is left to the user or devops)
- **Model default:** review tier (`pro`)
- **Tools:** `view_file`, `list_dir`, `grep_search`, `find_by_name`, `write_to_file`, `replace_file_content`, `multi_replace_file_content` (no shell; `commandExecutionPolicy: off`)

### Planning & Requirements Agents (2)

#### requirements-gatherer
- **Purpose:** Requirements elicitation and documentation
- **Responsibilities:**
  - Gather business/user requirements
  - Create BRD/URD documents
  - Define FR + NFR
  - Acceptance criteria specification
- **Model default:** build tier (`flash`)
- **Tools:** `view_file`, `list_dir`, `grep_search`, `find_by_name`, `write_to_file`, `replace_file_content`, `multi_replace_file_content` (no shell)

#### devops
- **Purpose:** CI/CD, infrastructure, deployment
- **Responsibilities:**
  - Pipeline configuration
  - Infrastructure setup (Terraform/Docker)
  - Deployment automation
  - Monitoring & alerting
- **Model default:** build tier (`flash`)
- **Tools:** `view_file`, `list_dir`, `grep_search`, `find_by_name`, `write_to_file`, `replace_file_content`, `multi_replace_file_content`, `run_command` (`commandExecutionPolicy: sandbox`)

### Specialized & Support Agents (6)

#### researcher
- **Purpose:** Web research, documentation audit
- **Responsibilities:**
  - Technical research on topics
  - Library/framework documentation audit
  - Best-practice discovery
  - Competitive analysis
- **Model default:** review tier (`pro`)
- **Tools:** `search_web`, `read_url_content`, `view_file`, `list_dir`, `grep_search`, `find_by_name`, `write_to_file`, `replace_file_content`, `multi_replace_file_content` (no shell; `commandExecutionPolicy: off`)

#### code-reviewer
- **Purpose:** Formal code review (specialized)
- **Responsibilities:**
  - Detailed line-by-line review
  - Architectural evaluation
  - Best-practice enforcement
  - Sign-off on critical changes
- **Model default:** review tier (`pro`)
- **Tools:** `view_file`, `list_dir`, `grep_search`, `find_by_name` (no write, no shell)

#### explore
- **Purpose:** Fast read-only code search
- **Responsibilities:**
  - Find files by pattern
  - Search for symbols/keywords
  - Locate definitions/callers
  - Code location discovery
- **Model default:** fast tier (`flash`)
- **Tools:** `view_file`, `list_dir`, `grep_search`, `find_by_name` (no write, no shell)

#### ask
- **Purpose:** Answer questions using repo search and optional web research
- **Responsibilities:**
  - Accept a question from the orchestrator or a direct `/ask` invocation
  - Search the repo first; search the web only when the repo is insufficient
  - Cite every file or URL the answer relies on
- **Model default:** build tier (`flash`)
- **Tools:** `view_file`, `list_dir`, `grep_search`, `find_by_name`, `search_web`, `read_url_content` (no write, no shell)

#### general-purpose
- **Purpose:** Catch-all for unmatched tasks
- **Responsibilities:**
  - Tasks that don't fit other agents
  - Ad-hoc analysis
  - Experimentation
  - Fallback orchestration
- **Model default:** build tier (`flash`)
- **Tools:** `view_file`, `list_dir`, `grep_search`, `find_by_name`, `write_to_file`, `replace_file_content`, `multi_replace_file_content`, `run_command` (`commandExecutionPolicy: sandbox`)

#### worker
- **Purpose:** Multi-discipline generalist
- **Responsibilities:**
  - Code + review + testing (combined)
  - Small feature end-to-end
  - Cross-cutting concerns
  - When coordination overhead exceeds benefit
- **Model default:** build tier (`flash`)
- **Tools:** `view_file`, `list_dir`, `grep_search`, `find_by_name`, `write_to_file`, `replace_file_content`, `multi_replace_file_content`, `run_command` (`commandExecutionPolicy: sandbox`)

---

## Skills (18 Total)

The full skill list appears in the [README.md](../README.md) table. Below are skill categories with detailed specifications.

### do
**Command:** `/do <task description>`  
**Purpose:** Orchestrate task routing to best agent

**Workflow:**
1. Classify the incoming task (primary intent, scope, output type)
2. Match to agent using registry
3. Create execution plan with each agent's tier
4. Get approval with `ask_question` (tier changes go through `set-model-profile.sh`)
5. Delegate with `invoke_subagent`, concurrently where steps are independent, with review loops
6. Synthesize results

**Model:** Orchestrator on the user's selected model; subagents per their `model` field
**Effort:** xhigh

**Key features:**
- Concurrent subagents (max 3) for non-overlapping or read-only steps; overlapping code writes run sequentially in workspace `inherit` (`branch` is not used until worktree merge-back is verified)
- Tier reporting before approval
- Plan-based execution
- Review gate enforcement

---

### debug
**Command:** `/debug [analyze | fix | review] [description | file:line]`  
**Purpose:** Root cause analysis and iterative fix cycles

**Subcommands:**

| Mode | Action | Output |
|------|--------|--------|
| `analyze` | Investigate bug, gather context | RCA report |
| `fix` | Apply fix (requires approved RCA) | Code changes |
| `review` | Verify fix is correct | Verification report |

**Runs on:** main agent (selected model)  
**Effort:** high

**Constraints:**
- `fix` requires approved RCA or human-report
- No broad try/catch patches
- Find root cause, don't patch symptoms

---

### commit
**Command:** `/commit`  
**Purpose:** Create conventional commits with git

**Features:**
- Conventional Commits format (feat/fix/refactor/docs/test)
- Scoped commits (scope:subject format)
- Multi-file staging
- Squash/amend support
- No LLM co-author trailers

**Runs on:** main agent (selected model)  
**Effort:** low

---

### branch
**Command:** `/branch [create | switch | list | cleanup] [branch-name | --dry-run]`  
**Purpose:** Branch creation, switching, and merged worktree cleanup

**Features:**
- Create feature/bugfix/release branches
- Naming conventions (feature/*, bugfix/*, release/*)
- Switch with stash support
- Track remote branches
- Clean up merged worktrees, their branches, and Go build caches (`cleanup`); shows a dry-run listing and asks for confirmation with `ask_question` before removing anything

**Runs on:** main agent (selected model)  
**Effort:** low

---

### map-project
**Command:** `/map-project`  
**Purpose:** Discover and document repo structure

**Features:**
- Scan for key directories (src, tests, config)
- Identify stack (language, framework, tools)
- Document module/package structure
- Generate architecture diagram

**Runs on:** main agent (selected model)  
**Effort:** medium

---

### technical-writing
**Command:** `/technical-writing [docs | readme]`  
**Purpose:** Generate and update documentation

**Subcommands:**
- `docs` — Create user/developer documentation
- `readme` — Generate or update README

**Runs on:** main agent (selected model)  
**Effort:** medium

---

### gather-requirements
**Command:** `/gather-requirements [elicit | document | review] [topic | file]`  
**Purpose:** Gather and document business, user, and technical requirements

**Subcommands:**

| Mode | Action | Output |
|------|--------|--------|
| `elicit` | Six-phase interactive elicitation with batched questions | Requirements summary |
| `document` | Categorize into BR/UR/FR/NFR, apply IEEE 29148 sentence forms | `BRD-*.md`, `URD-*.md`, `FR-NFR-*.md`, optional JSON |
| `review` | Quality, completeness, consistency, and traceability audit | PASS / NEEDS REVISION report |

**Runs on:** main agent (selected model), or the requirements-gatherer subagent (build tier) that preloads it  
**Effort:** high

**Key features:**
- `BR-NNN → UR-NNN → FR-NNN`/`NFR-NNN` traceability chain, cited by specs and code markers
- RFC 2119 binding language (SHALL/MUST/SHOULD/MAY) in every FR and NFR
- Acceptance criteria as GIVEN/WHEN/THEN scenarios, one happy path and one failure path per FR
- Nine-criterion quality checklist plus a banned-words list

**Used by:** requirements-gatherer agent

---

### spec-from-requirements
**Command:** `/spec-from-requirements [create | delta | review] [feature-name | file-path]`  
**Purpose:** Turn requirements into specification files under `specs/`

**Modes:**

| Mode | Action | Output |
|------|--------|--------|
| `create` | Classify the requirement, apply the matching template, write the spec | `specs/spec-[feature].md` |
| `delta` | Record an incremental change without rewriting the file | `## Change Log` section with ADDED/MODIFIED/REMOVED |
| `review` | Completeness, correctness, and coherence audit | CRITICAL / WARNING / SUGGESTION findings |

**Runs on:** main agent (selected model), or the solutions-architect subagent (review tier) that preloads it  
**Effort:** high

**Key features:**
- Classify-first: Architecture, API endpoint, Frontend action, Functionality, UI/UX design, General (first match wins, never mix templates)
- Behavior written as `### Requirement:` plus `#### Scenario:` GIVEN/WHEN/THEN blocks with RFC 2119 keywords
- Every spec traces to at least one `BR/UR/FR/NFR-NNN` ID from `gather-requirements`
- OpenAPI 3.1 fragment for API endpoint specs; JSON projection for any spec
- GCP/AWS cloud pattern library and the five cloud-boundary rules
- Pseudo-code gate: agent-suggested blocks keep the spec at Draft until approved

**Used by:** solutions-architect agent

---

### review-md
**Command:** `/review-md <path-to-report.md>`  
**Purpose:** Review markdown reports for factual soundness, consistency, and conciseness

**Modes:**
- Manual — invoked directly on any report file
- Automated — auto-invoked after report-producing skills (`ask`, `debug`, `pr-review`, `technical-writing`, `bump`, `map-project`, `commit`, `branch`, `do`) before the report reaches the user

**Runs on:** main agent (selected model)  
**Effort:** medium

**Constraints:**
- Read-only on the reviewed file; never edits it
- Produces a separate findings artifact using the three-part structure (what's wrong, why it matters, what to change)

---

## Governance Rules

See [rules/assist-plugin-rule.md](../rules/assist-plugin-rule.md)

**Key gates:**
- **Security:** OWASP review on code changes (top 10 vulnerabilities)
- **Testing:** >70% test coverage for new code
- **Review:** Code reviewer sign-off required before merge
- **LLM security:** OWASP Top 10 for LLM review on agents, skills, rules, context files, plugin config, and install scripts ([llm-security-checklist.md](../rules/llm-security-checklist.md))

---

## Token Optimization Strategy

See [TOKEN_OPTIMIZATION.md](TOKEN_OPTIMIZATION.md) for detailed rationale.

**Key techniques:**
- Link-based documentation (pointers, not inline)
- Consolidated agent registry (table, no duplication)
- Concise agent descriptions (400 chars max)
- Table-driven data (no prose for static info)
- Reuse: Skills reference agent docs; agents reference model routing

**Result:** ~65% token footprint of original software-development plugin with full feature parity (measured on the Claude Code build; not re-measured on Antigravity).

