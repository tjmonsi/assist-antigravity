# Architecture

## Philosophy

assist-plugin follows these core principles:

1. **Orchestration over monolith**: One skill (`do`) routes to 14 specialized subagents
2. **Agent specialization**: Each agent handles one domain; no overlapping responsibilities
3. **Model routing**: Task complexity determines the subagent tier (review, build, fast), mapped to Antigravity's `pro`/`flash`/`inherit` by a profile
4. **Review gates**: Security + testing + code review checkpoints before merge
5. **Token efficiency**: Centralized references, link-based docs, table-driven data

---

## Plugin Structure

```
assist-plugin/
├── plugin.json                # name, version, description (Antigravity manifest)
├── README.md                  # plugin quick reference
├── CHANGELOG.md, LICENSE, NOTICE
├── agents/<name>.md           # 14 subagents (subagent: true, model, tools, commandExecutionPolicy)
├── skills/<name>/SKILL.md     # 19 skills, each exposed as /<name>
│   └── references/            # progressive-disclosure detail loaded on demand
├── rules/
│   ├── assist-routing.md      # trigger: always_on (route actionable work to /do)
│   ├── assist-plugin-rule.md  # trigger: model_decision (governance gates)
│   ├── llm-security-checklist.md  # trigger: model_decision (OWASP Top 10 for LLM)
│   ├── writing-standard.md    # trigger: model_decision (full writing rules)
│   └── writing-standard-compact.md  # trigger: always_on (compact writing rules)
└── docs/                      # SPECIFICATION, ARCHITECTURE, TOKEN_OPTIMIZATION,
                               # DOCUMENTATION_STANDARD, TRACING_MARKERS, history/
```

The plugin ships no `metadata.json` files, no hooks directory, no `hooks.json`, and no `mcp_config.json`. `scripts/set-model-profile.sh`, `scripts/install.sh`, and `scripts/sync-writing-standard.py` live in the repository root, outside the plugin folder.

---

## System Architecture

```
┌─────────────────────────────────────────────┐
│         User Input / CLI (`/do`)            │
└────────────────┬────────────────────────────┘
                 │
        ┌────────▼────────┐
        │  Orchestrator   │
        │   (do skill)    │
        │  - Classify     │
        │  - Route        │
        │  - Plan         │
        │  - Delegate     │
        │  - Synthesize   │
        └────────┬────────┘
                 │
    ┌────────────┼────────────┬─────────────┬──────────────┐
    │            │            │             │              │
    ▼            ▼            ▼             ▼              ▼
┌────────┐  ┌──────────┐  ┌────────┐  ┌─────────┐  ┌──────────────┐
│Developer│  │Reviewer  │  │Planner │  │QA Agent │  │Requirements  │
│  Agent  │  │  Agent   │  │ Agent  │  │         │  │   Gatherer   │
└────────┘  └──────────┘  └────────┘  └─────────┘  └──────────────┘
    │            │            │             │              │
    └────────────┼────────────┴─────────────┴──────────────┘
                 │
        ┌────────▼────────────────────┐
        │   Review Gate               │
        │  - Security (OWASP)         │
        │  - Testing (>70% coverage)  │
        │  - Code Review (sign-off)   │
        └────────┬────────────────────┘
                 │
        ┌────────▼────────────────────┐
        │   Merge / Synthesize        │
        │   Results                   │
        └─────────────────────────────┘
```

---

## Agent Taxonomy

### By Responsibility

#### Development Tier
- **developer**: Implement, fix, refactor code
- **reviewer**: Quality, security, performance checks
- **code-reviewer**: Formal line-by-line review (specialized)

#### Architecture Tier
- **planner**: System design, roadmap, risk assessment
- **solutions-architect**: Feature specs, API design, data flow

#### Quality Tier
- **qa**: Test planning, acceptance validation
- **developer-tester**: Black-box tests from acceptance criteria
- **requirements-gatherer**: Requirements, BRD/URD, FR+NFR

#### Infrastructure Tier
- **devops**: CI/CD, infrastructure, deployment

#### Support Tier
- **researcher**: Web research, documentation, best practices
- **explore**: Fast code search and location discovery
- **ask**: Repository and optional web Q&A
- **general-purpose**: Catch-all for unmatched tasks
- **worker**: Multi-discipline (code + review + test combined)

### By Model Tier

| Tier | `gemini` profile | `inherit` profile | Agents | Use Cases |
|------|------------------|-------------------|--------|-----------|
| **fast** | `flash` | `inherit` | explore | Code search, fast lookup |
| **build** | `flash` | `inherit` | ask, developer, developer-tester, planner (`pro` available by editing its file), qa, requirements-gatherer, devops, general-purpose, worker | Implementation, testing, planning, DevOps |
| **review** | `pro` | `inherit` | reviewer, code-reviewer, solutions-architect, researcher | Architecture, design, research, security, decisions |

The orchestrator (`do`) and every other skill run on the model selected in Antigravity's model selector.

---

## Skill Tree

```
/do (Orchestrator)
 ├─► Route to developer
 │   └─► Use /debug [analyze|fix|review] for bugs
 ├─► Route to reviewer
 │   └─► Use review-protocol (built-in)
 ├─► Route to planner
 │   └─► Use /map-project for discovery
 ├─► Route to solutions-architect
 │   └─► Use /technical-writing [docs] for specs
 ├─► Route to qa
 │   └─► Use /technical-writing [docs] for test plans
 ├─► Route to requirements-gatherer
 │   └─► Use /technical-writing [docs] for BRD
 ├─► Route to devops
 │   └─► Use /commit for deployment tracking
 ├─► Route to researcher
 │   └─► Use /map-project for stack discovery
 ├─► Route to others
 │   └─► Agent-specific workflows
 └─► Report Quality Gate (all report-producing steps)
     └─► /review-md checks the drafted report before it reaches the user
```

---

## Data Flow: Task → Agent → Delivery

### Example: "Implement user authentication"

1. **User:** `/do implement user authentication in backend`

2. **Orchestrator classifies:**
   - Primary intent: Code implementation
   - Scope: Feature (not quick fix)
   - Output: Code files + tests
   - Agent: developer
   - Model: `flash` (build tier, from the agent file)

3. **Orchestrator creates plan:**
   ```
   ## Step 1: Design API Schema
   Agent: solutions-architect
   Model: pro
   Files: docs/api.md
   
   ## Step 2: Implement Authentication
   Agent: developer
   Model: flash
   Files: backend/auth.ts, tests/auth.test.ts
   
   ## Step 3: Review Code
   Agent: reviewer
   Model: pro
   Files: (changed files from Step 2)
   ```

4. **User approves plan** (through `ask_question`)

5. **Orchestrator delegates** with `invoke_subagent`:
   - Step 1: solutions-architect designs API
   - Step 2: developer implements code
   - Step 3: reviewer checks security (OWASP) + tests (>70%)

6. **Orchestrator synthesizes:** Presents design + code + review

7. **Review gates:**
   - Security: ✓ No SQL injection, XSS, CSRF
   - Testing: ✓ 85% coverage
   - Code review: ✓ Approved

8. **User merges:** Ready for production

---

## Reference Data Model

### agent-registry.md
- **Source of truth:** All agent metadata
- **Format:** Table (name, purpose, model, tools, responsibilities)
- **Used by:** `do` skill for routing, README.md for index

### model-routing.md
- **Source of truth:** Model assignment rules
- **Format:** Tables (agent, tier, `gemini` and `inherit` values, effort; profiles; adjustment guidance)
- **Used by:** `do` skill for tier reporting and fix-phase routing

### plan-format.md
- **Source of truth:** Plan file structure
- **Format:** Markdown template
- **Used by:** `do` skill when creating plans

### review-protocol.md
- **Source of truth:** Review workflow
- **Format:** Procedural steps + gates
- **Used by:** `reviewer` agent and orchestrator

---

## Extension Points

### Add a New Skill
1. Create `skills/new-skill/SKILL.md` with `name` and `description` frontmatter; put `effort` and `argument-hint` under `metadata`
2. Add references in `skills/new-skill/references/`
3. Update the `README.md` skills table
4. Update plan/orchestrator if skill changes routing logic
5. Run `python3 scripts/validate.py`

### Add a New Agent
1. Create `agents/new-agent.md` with `name`, `description`, `model`, `tools`, `subagent: true`, and `commandExecutionPolicy` (`sandbox` if it holds `run_command`, else `off`)
2. Add the agent to one tier array in `scripts/set-model-profile.sh`
3. Add row to `agent-registry.md` and `model-routing.md`
4. Update the `README.md` agents table
5. Run `python3 scripts/validate.py`

### Add a Governance Rule
1. Edit `rules/assist-plugin-rule.md` (keep it under 24,000 bytes and keep its `trigger` frontmatter)
2. Update review-protocol if it affects review gates
3. Update SPECIFICATION.md if user-facing

---

## Token Efficiency

### Key Design Decisions

1. **Avoid re-definition:** All agent descriptions defined once in agent-registry.md
2. **Link, don't duplicate:** Skills link to SPECIFICATION.md for detailed workflows
3. **Tables for static data:** Model routing, agent index, skill mapping (compact)
4. **Prose only for logic:** `do` skill procedure, review gates (essential flow)
5. **Consolidate references:** 4 key files vs. 20+ in original plugin

### Model Tier Optimization

**Distribution (review tier reserved for decisions):**
- **Fast tier:** 1 agent (search only)
- **Build tier:** 9 agents (questions, implementation, planning, testing, DevOps, requirements)
- **Review tier:** 4 agents (architecture, research, security, review)
- **Orchestrator:** the user's selected model

**Rationale:** The strongest tier goes to architectural and review decisions (solutions-architect, researcher, reviewer, code-reviewer) because these determine project quality and downstream costs. The planner runs on the build tier by default; move it to `pro` for complex planning.

### Result
Token figures below were measured on the Claude Code build (assist-marketplace-plugin) and have not been re-measured on Antigravity.
- **Base plugin:** ~2.5k tokens
- **Full load (agents + skills + docs):** ~10-12k tokens
- **Model mix:** review tier for foundational decisions, build tier for execution
- **Comparison:** software-development plugin ~12-15k tokens
- **Cost vs. Quality:** Higher token cost for better architecture/design/research quality

