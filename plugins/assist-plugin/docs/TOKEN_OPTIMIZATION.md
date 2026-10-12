# Token Optimization Strategy

> **Measurement note:** Every token figure, size, and ratio in this document was measured on the Claude Code build (assist-marketplace-plugin v1.5.0). None has been re-measured on Antigravity, which loads plugins, skills, rules, and subagents through its own mechanism. Treat these numbers as relative guidance only.

## Overview

assist-plugin achieves a ~65% token footprint of the original software-development plugin while maintaining full feature parity. This document explains what's included, excluded, and why.

---

## Included ✓

### Agents (15)
- **All core agents:** developer, developer-tester, reviewer, planner
- **All testing agents:** qa, solutions-architect
- **All planning agents:** requirements-gatherer, devops
- **All support agents:** ask, researcher, code-reviewer, intake-reviewer, explore, general-purpose, worker

**Why:** Full agent coverage ensures task routing flexibility without off-loading to external plugins.

### Skills (21)
- `do` (orchestrator): replaces `run` with leaner logic
- `debug`: replaces `debug-code` with token-optimized workflow
- `bump`: semantic versioning & changelog generation
- `pr-review`: GitHub/Bitbucket PR review with auto-detection
- `commit`, `branch`: essential git operations
- `map-project`: project discovery
- `technical-writing`: documentation generation
- `ask`, `gather-requirements`, `spec-from-requirements`, `task-plan`, `review-md`, `create-test`: user-invocable Q&A, requirements, spec, planning, review, and test skills
- `deslop`: AI-writing-tell removal
- `clarify`, `voice-script`: explain unclear points from the current discussion, and write paste-ready text-to-speech scripts
- `code`, `pentest`, `integrated-test`, `run-test`: internal skills preloaded by developer and qa

**Why:** Minimal viable skill set covering 80% of common tasks.

> **Note:** `pr-review` supports both GitHub and Bitbucket in a single skill (~11.6KB). software-development only provides Bitbucket (`review-bkt-pr`). The higher token cost reflects broader platform support.
>
> **Note:** `bump` generates a full categorized CHANGELOG.md. software-development's `release-version` only bumps version numbers. The extra token cost reflects added functionality.

### References (Consolidated)
- `agent-registry.md`: 1 source of truth for all agents
- `model-routing.md`: Model assignment rules (table format)
- `plan-format.md`: Plan template (compact)
- `review-protocol.md`: Review workflow (essential steps only)
- `developer-self-review.md`, `fix-phase-rules.md`, `fsa-template.md`, `planning-review-agents.md`, `reviewer-adversarial-reflection.md`, `routing-with-discovery.md`: `do` state-machine, review, and routing rules

**Why:** Centralized references eliminate duplication and reduce lookup time.

### Governance Rules
- Security (OWASP top 10)
- Testing (coverage gates)
- Review (sign-off requirements)

**Why:** Core governance without specialized compliance rules.

---

## Excluded ✗

### Complex DevOps/Integration Skills
- **Why excluded:** DevOps workflows are project-specific; this plugin stays generic
- **Skills:** bkt-pr, bkt-jira, cert-prep, context7, branch-to-jira
- **Alternative:** Reference software-development plugin for these or use self-hosted deployments

### Meta-Skills (Skill/Agent Creation)
- **Why excluded:** create-agent, create-skill expand plugin scope unnecessarily
- **Alternative:** Edit SKILL.md directly for custom skills

### Hooks & CI Infrastructure
- **Why excluded:** Git hooks, CI pipelines, and project-specific automation belong to each project; governance is in rules
- **Antigravity port:** ships no hooks. `sa-mermaid-only` needs the calling agent's identity, which Antigravity hook payloads do not carry. `health-check` needs a SessionStart event and plugin data, which Antigravity does not document. `doc-cli-guard` is deferred pending a live test of its no-match decision. The command-shape rules they enforced live in skill and agent text instead. Upstream v1.8.0's `injection-filter`, `prose-gate`, and `prose-advisor`, and v1.9.0's `fsa-write-bar` and `fsa-log`, are not ported either: Antigravity hook payloads do not name the calling agent, there is no SubagentStop event, Antigravity's PostToolUse hook cannot read or change a tool result, and a PreToolUse write gate would need a decision on every file write. Upstream v1.10.0's `commit-attribution-guard` needs no agent identity but is not ported: agy documents no pass-through decision for a command the guard does not match, and user reports show a failing PreToolUse hook blocking every tool call. Its rule ships as text (the No AI Attribution Rule) plus a one-line reminder in `assist-routing.md`. The compact writing standard loads as an `always_on` rule (`rules/writing-standard-compact.md`, 1,504 bytes; with `assist-routing.md` (1,219 bytes) the always-on rules total 2,723 bytes) in place of upstream's `writing-context` hook. Upstream's `terse` output style has no Antigravity equivalent <!-- claude-ref-ok -->
- **Alternative:** Implement hooks in your git repo or CI/CD

### Examples & Tutorials
- **Why excluded:** Links to docs instead of inline examples save tokens
- **Format:** Each skill references comprehensive examples in SPECIFICATION.md

### Verbose Reference Documentation
- **Why excluded:** Consolidated references (18 files spanning skills: do (10), debug (4), bump (2), pr-review (2))
- **Original approach:** Separate reference file per agent/skill + examples
- **This approach:** Table-driven data + link-based structure

---

## Token Conservation Techniques

### 1. Link-Based Documentation
**Before (token cost: HIGH):**
```
## Agent: developer
Responsibilities:
- Implement features from specs
- Bug fixes from approved RCAs
...extensive inline explanation...
```

**After (token cost: LOW):**
```
See [SPECIFICATION.md](SPECIFICATION.md) for detailed agent descriptions.
```

### 2. Consolidated Agent Registry
**Before:** Each agent file + agent index (duplication)  
**After:** Single `agent-registry.md` sourced by all tools (1 read)

### 3. Table-Driven Data
**Before (prose):**
```
The developer agent handles code writing, fixing, and refactoring. 
It runs on the build tier by default. Its tools are view_file, write_to_file, replace_file_content, etc.
```

**After (table):**
```
| Agent | Purpose | Model | Tools |
|-------|---------|-------|-------|
| developer | Write, fix, refactor | flash | view_file, write_to_file, ... |
```

### 4. Concise Agent Descriptions
- **Limit:** 400 chars per agent (vs. 1000+ in original)
- **Focus:** What agent does, not how to use it
- **Detail:** Deferred to SPECIFICATION.md

### 5. Reuse & Cross-Referencing
- **Skills reference agents:** No re-definition, just link
- **Agents reference model routing:** 1 source of truth for model assignment
- **Documentation references code:** Less duplication

### 6. Compact Plan Format
- **Removed:** Verbose step numbering
- **Kept:** Essential fields only (Goal, Relevant Files, Status)
- **Format:** Markdown table for status tracking

---

## Scope Comparison

| Aspect | assist-plugin | software-development | Ratio |
|--------|---------------|----------------------|-------|
| Agents | 15 | 12 | 125% |
| Skills | 21 | 20+ | ~105% |
| Reference files | 10 | 20+ | 50% |
| Documentation | 3 pages | 50+ pages | 6% |
| **Plugin size** | ~2.5k | ~4.0k | **62%** |
| **Model mix** | Strongest tier for decisions (quality) | Mixed | Higher token cost |
| **Total execution tokens** | ~10-12k | ~12-15k | ~80% |

---

## Trade-Offs

| Decision | Benefit | Cost |
|----------|---------|------|
| No DevOps skills | Smaller, focused | Use external plugin for bkt-jira |
| No meta-skills | Reduced scope | Manual skill creation (rare need) |
| No hooks | Simpler | Implement in your CI/CD |
| Link-based docs | ~30% token saving on docs | Need to read external docs |
| Compact format | Faster parsing | Less verbose explanations |
| **Review tier (`pro`) for architecture** | Better quality decisions | Higher cost per task |
| **Build tier (`flash`) for execution** | Cost-effective implementation | May iterate more on fixes |

---

## Future Extensions

To add capabilities without bloating token count:

1. **Add skill:** Create `skills/new-skill/SKILL.md` + minimal references
2. **Add agent:** Add row to `agent-registry.md`, link from `README.md`, add it to a tier in `scripts/set-model-profile.sh`
3. **Add reference:** New `.md` file in `references/` (links only, no duplication)

**Principle:** Each new addition should aim for <50 tokens per feature.

---

## Model Tier Strategy

**Architecture-First Approach** (shipped `gemini` profile; see [model-routing.md](../skills/do/references/model-routing.md)):
- **Review tier (`pro`)** for foundational decisions: solutions-architect, researcher, reviewer, code-reviewer
- **Build tier (`flash`)** for execution: ask, developer, developer-tester, planner (move to `pro` for complex planning), qa, requirements-gatherer, intake-reviewer, devops, general-purpose, worker
- **Fast tier (`flash`)** for pure search: explore
- **Orchestrator:** the model the user selects in Antigravity's model selector
- The `inherit` profile collapses all tiers onto the selected model, which removes this cost split

**Why this costs more but saves overall:**
- Better architecture prevents rework (saved tokens from fewer iterations)
- Good specs reduce implementation time (the build tier can execute faster)
- Research quality reduces dependency issues (fewer emergency fixes)
- Security review quality prevents vulnerabilities (less forensic debugging)

**Cost comparison:**
- Naive approach: everything on the build tier (cheaper initially, more iterations/fixes = more tokens total)
- This approach: review tier for decisions, build tier for work (higher per-task cost, lower total lifecycle cost)

## Verification

To measure token efficiency:
1. Track tokens per task and compare iteration count
2. Compare total project cost (architecture quality affects maintenance burden)
3. Switch profiles with `scripts/set-model-profile.sh` (or edit an agent's `model:` line) to compare cost against quality. A per-call `Model` value in `invoke_subagent` did not override the agent file's `model:` line in any test on `agy` 1.3.3

