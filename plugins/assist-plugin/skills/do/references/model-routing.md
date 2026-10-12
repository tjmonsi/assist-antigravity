# Model Routing

Decision tables for assigning model tiers to subagents in the `do` orchestrator.

Antigravity subagent frontmatter accepts three `model` values: `pro`, `flash`, and `inherit` (follow the model the user selected in Antigravity's model selector). This plugin groups its 15 subagents into three tiers and ships profiles that map each tier to one of those values.

## Orchestrator

The orchestrator (`do` skill) and every other skill run on the main agent, which uses whatever model the user picked in the model selector (for example Gemini 3.1 Pro, a Gemini 3.x Flash model, or a Claude model on plans that offer one). Skills carry no `model` field, so the plugin cannot pin the orchestrator's model. Pick a strong reasoning model in the selector for `/do` sessions; planning, routing, and synthesis are the highest-leverage work in the pipeline.

## Tier Assignment

| Agent | Tier | `gemini` profile (default) | `inherit` profile | Effort |
|-------|------|----------------------------|-------------------|--------|
| **code-reviewer** | review | `pro` | `inherit` | xhigh |
| **reviewer** | review | `pro` | `inherit` | xhigh |
| **researcher** | review | `pro` | `inherit` | xhigh |
| **solutions-architect** | review | `pro` | `inherit` | xhigh |
| **ask** | build | `flash` | `inherit` | medium |
| **developer** | build | `flash` | `inherit` | high |
| **developer-tester** | build | `flash` | `inherit` | high |
| **devops** | build | `flash` | `inherit` | high |
| **general-purpose** | build | `flash` | `inherit` | medium |
| **intake-reviewer** | build | `flash` | `inherit` | medium |
| **planner** | build | `flash` | `inherit` | xhigh |
| **qa** | build | `flash` | `inherit` | high |
| **requirements-gatherer** | build | `flash` | `inherit` | medium |
| **worker** | build | `flash` | `inherit` | high |
| **explore** | fast | `flash` | `inherit` | low |

Antigravity has no effort field. State the effort level in the delegation prompt (see [plan-format.md](plan-format.md)) so the subagent calibrates how deeply to reason.

The fast tier and the build tier share `flash` under the `gemini` profile. The tiers stay separate so a future profile can give `explore` a cheaper model without touching the build agents.

## Profiles

| Profile | review tier | build tier | fast tier | Use when |
|---------|-------------|------------|-----------|----------|
| `gemini` (shipped) | `pro` | `flash` | `flash` | Default. Strongest model on quality gates, faster model on implementation. |
| `inherit` | `inherit` | `inherit` | `inherit` | Every subagent follows the model selector, for example to run the whole pipeline on Claude. |
| `gemini-pro` | `pro` | `pro` | `pro` | Quality matters more than latency or quota for every step. |
| `gemini-flash` | `flash` | `flash` | `flash` | Latency or quota matters more than review depth. |

The `inherit` profile removes the tier split: every subagent runs on the selected model, so the review and build tiers no longer differ in capability.

## Switching Profiles

`scripts/set-model-profile.sh` lives in the assist-antigravity repository, not inside the installed plugin. It rewrites only the `model:` line of each `agents/<name>.md`.

```bash
# Repository copy (plugins/assist-plugin)
scripts/set-model-profile.sh inherit

# Installed copies: pass the plugin directory
scripts/set-model-profile.sh inherit ~/.gemini/config/plugins/assist-plugin            # global (agy plugin install or install.sh --global)
scripts/set-model-profile.sh inherit <workspace>/.agents/plugins/assist-plugin         # workspace install
```

Reinstalling or updating the plugin restores the shipped `gemini` profile; rerun the script afterwards. To change a single agent, edit the `model:` line in that agent's file directly.

After switching profiles, restart Antigravity (or the `agy` session) and re-run `/do`. The running session keeps the agent files it already loaded.

`invoke_subagent` exposes a per-call `Model` parameter (`inherit`, `flash_lite`, `flash`, `pro`), but on `agy` 1.3.3 the agent file's `model:` line took precedence in every test (parameter omitted, explicit `inherit`, explicit `flash_lite`): `reviewer` (`model: pro`) ran on Gemini 3.1 Pro while the parent ran on Gemini 3.8 Flash. Antigravity's documentation does not confirm that `define_subagent` accepts a model. The agent file's `model` field, changed through the profile script, is the control, so the orchestrator omits `Model` in `invoke_subagent` calls and never promises a one-off model change during a run.

---

## Cost vs. Quality Trade-Off

### Fast tier
- Minimal reasoning needed
- **Agents:** explore
- **Use case:** Code search, locating files and symbols

### Build tier: core development
- Implementation, testing, requirements, DevOps, planning
- Balances reasoning quality against latency and quota
- **Agents:** ask, developer, developer-tester, devops, general-purpose, intake-reviewer, planner, qa, requirements-gatherer, worker
- **Strategy:** Iterate and refine if the first pass is incomplete; the review tier catches what slips through

### Review tier: decisions and quality gates
- Design, quality gates, research, sign-off
- Decisions that set project direction or block a merge
- **Agents:** reviewer, code-reviewer, solutions-architect, researcher
- **Strategy:** Spend the strongest model where a wrong answer is expensive to undo

Skills such as `commit` and `branch` run on the main agent's selected model. Their work is mechanical, so they need no tier of their own.

---

## Adjustment Guidance

The tier table is the default. Adjust it only by editing agent files or switching profiles, and only for these reasons.

### Move to `pro`
- **planner:** High-stakes or highly ambiguous architecture where a wrong first pass is costly
- **qa:** Critical test planning
- **devops:** Complex infrastructure
- **developer:** Large cross-cutting refactors where repeated fix loops cost more than one stronger pass

### Move to `flash`
- **solutions-architect:** Simple, well-defined specifications

### Keep on the review tier (non-negotiable)
- **reviewer, code-reviewer:** Security and quality sign-off
- **researcher:** Research quality depends on judging sources
- Under the `gemini-flash` profile these run on `flash`; tell the user review depth drops when they choose that profile.

### Fix phase (non-negotiable)
- **All fixing agents (including developer-tester):** Build tier (`flash` under the `gemini` profile), never the review tier
- **Rationale:** Applying specific, already-identified fixes needs precision, not open-ended judgment, and the review tier stays free for the verification pass
- **Scope constraint:** Fix phase only modifies code or docs tied to the reviewer's findings
- **See:** [fix-phase-rules.md](fix-phase-rules.md) for constraints and procedure

### Guidance
- Build tier plus a review loop beats a single review-tier pass for most implementation work.
- Spend the review tier on risk-critical work: security, architecture, sign-off.
- Exploratory work starts on the build tier and moves up only if results fall short.

---

## Planner on the Build Tier

The planner defaults to the build tier.

**Why:**
- Planning is iterative: plans get reviewed and revised before execution starts, whatever model writes them.
- A build-tier draft plus a review-tier check reaches the plan quality of a single review-tier pass while spending the stronger model only on verification.
- Planning prompts carry large amounts of repo context, so the cheaper tier's savings scale with plan size.
- Move the planner to `pro` for genuinely high-stakes or ambiguous architecture (see Adjustment Guidance).

## Cost Savings vs. Token Context

Tier routing optimizes **cost, quota, and latency**, not token footprint:

- **Token context is identical:** a `flash` subagent reads the same instructions as a `pro` subagent. Routing only changes which model processes them.
- **Cost and quota differ:** `pro` models cost more per token and consume plan quota faster than `flash` models. Check current Gemini pricing and your Antigravity plan's limits for exact figures.
- **Latency differs:** `flash` models typically return faster.

For per-scenario token measurements (taken on the Claude Code build), see [../../../docs/TOKEN_OPTIMIZATION.md](../../../docs/TOKEN_OPTIMIZATION.md).
