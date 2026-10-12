# assist-plugin

Token-optimized software development plugin for Google Antigravity. It orchestrates 14 specialized subagents and 19 skills across the full development lifecycle. This is the Antigravity port of [assist-plugin](https://github.com/tjmonsi/assist-marketplace-plugin), originally built for Claude Code.

## Install

Install instructions for the Antigravity CLI, Antigravity 2.0, and the Antigravity IDE live in the [repository README](https://github.com/tjmonsi/assist-antigravity#readme). The short version:

```bash
# Antigravity CLI
agy plugin install https://github.com/tjmonsi/assist-antigravity/plugins/assist-plugin   # stages to ~/.gemini/config/plugins/assist-plugin
agy plugin enable assist-plugin

# Antigravity 2.0 / IDE (from a clone of the repository)
scripts/install.sh --global            # ~/.gemini/config/plugins/assist-plugin
scripts/install.sh --workspace <dir>   # <dir>/.agents/plugins/assist-plugin
```

## Quick Start

Use `/do` to route any development task to the right agent:

```
/do implement user authentication in the backend
/do review this PR for security issues
/do design the API schema for the new feature
```

## Subagents (14)

The orchestrator starts these with `invoke_subagent`; they are not slash commands. Tiers show the shipped `gemini` profile.

| Agent | Purpose | Tier (`model`) |
|-------|---------|----------------|
| **ask** | Answer questions using repo + web research | build (`flash`) |
| **developer** | Write, fix, refactor code | build (`flash`) |
| **developer-tester** | Create black-box tests from acceptance criteria | build (`flash`) |
| **reviewer** | Code review, security, quality checks | review (`pro`) |
| **planner** | Architecture, design, planning | build (`flash`) |
| **qa** | Testing, validation, acceptance; run pentest, integration, security tests | build (`flash`) |
| **solutions-architect** | Feature specs, data flow, contracts, Mermaid architecture diagrams | review (`pro`) |
| **requirements-gatherer** | Elicitation, BRD/URD, FR+NFR | build (`flash`) |
| **devops** | CI/CD, infrastructure, deployment | build (`flash`) |
| **researcher** | Web research, documentation audit | review (`pro`) |
| **code-reviewer** | Formal code review (specialized) | review (`pro`) |
| **general-purpose** | Catch-all for unmatched tasks | build (`flash`) |
| **explore** | Fast read-only code search | fast (`flash`) |
| **worker** | Multi-discipline fallback | build (`flash`) |

## Models

- The main agent, including `/do` and every other skill, runs on the model selected in Antigravity's model selector (Gemini, or Claude on plans that offer it).
- Subagents run on the `model` value in their agent file. Switch every agent at once with `scripts/set-model-profile.sh <gemini|inherit|gemini-pro|gemini-flash> [plugin-dir]` from a clone of the repository; `inherit` makes every subagent follow the model selector.
- See [skills/do/references/model-routing.md](skills/do/references/model-routing.md) for the tier table and rationale.

## Skills (19)

Antigravity exposes every skill as a slash command. The text typed after the command is the skill's input.

| Skill | Command | Purpose |
|-------|---------|---------|
| **do** | `/do [task description or prompt]` | Route task to best agent + orchestrate |
| **ask** | `/ask [--web] <question>` | Answer questions using repo + optional web research |
| **debug** | `/debug [analyze \| fix \| review] [description \| file:line]` | Root cause analysis & iterative fixes |
| **bump** | `/bump [patch \| minor \| major \| auto] [--path PATH] [--no-tag] [--no-commit]` | Semantic versioning & changelog generation |
| **pr-review** | `/pr-review [PR#\|branch-name] [--approve\|--changes-requested\|--comment] [--message TEXT]` | Auto-detect GitHub/Bitbucket, review PRs |
| **commit** | `/commit [--squash] [--amend] [--scope SCOPE] [TYPE: message]` | Conventional commit with git |
| **branch** | `/branch [create \| switch \| list \| cleanup] [branch-name \| --dry-run]` | Branch management and merged worktree cleanup |
| **map-project** | `/map-project` | Discover repo structure |
| **technical-writing** | `/technical-writing [docs \| readme \| guide \| api] [topic \| file]` | Generate documentation |
| **review-md** | `/review-md <path-to-report.md>` | Review reports for consistency, conciseness, and factual accuracy |
| **gather-requirements** | `/gather-requirements [elicit \| document \| review] [topic \| file]` | Elicit and document BR/UR/FR/NFR with IEEE 29148 templates and GIVEN/WHEN/THEN criteria |
| **spec-from-requirements** | `/spec-from-requirements [create \| delta \| review] [feature-name \| file-path]` | Classify-first feature specs with Requirement/Scenario blocks and delta change logs |
| **task-plan** | `/task-plan <spec-file-or-prompt> [target-language]` | Generate ordered coding steps from feature specs |
| **create-test** | `/create-test [spec-file \| feature-name] [language]` | Create black-box tests from acceptance criteria only |
| **deslop** | `/deslop [edit \| detect] <file-or-text>` | Remove AI writing tells from prose; edit returns cleaned text, detect lists findings |
| **code** | (internal; preloaded by developer) | Language/framework standards, logging, error-handling, traceability conventions |
| **pentest** | (internal; preloaded by qa) | Security testing: OWASP Top 10, LLM OWASP Top 10, dependency audit |
| **integrated-test** | (internal; preloaded by qa) | Integration/E2E testing with Playwright, container patterns, Playwright availability check |
| **run-test** | (internal; preloaded by qa) | Execute test suites, collect coverage, produce consolidated test report |

## Documentation

- **[SPECIFICATION.md](docs/SPECIFICATION.md)**: Full agent/skill catalog
- **[TOKEN_OPTIMIZATION.md](docs/TOKEN_OPTIMIZATION.md)**: What's included/excluded and why
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)**: Design rationale and structure
- **[writing-standard.md](rules/writing-standard.md)**: Writing rules and AI-slop removal tiers (source of truth); [writing-standard-compact.md](rules/writing-standard-compact.md) is its always-on summary
- **[DOCUMENTATION_STANDARD.md](docs/DOCUMENTATION_STANDARD.md)**: Documentation-specific rules: structure, citations, and conciseness checklist
- **[TRACING_MARKERS.md](docs/TRACING_MARKERS.md)**: Requirement/spec traceability marker convention

## Getting Started

1. Install this plugin (see [Install](#install))
2. Pick a model in Antigravity's model selector, then use `/do` to start delegating tasks
3. Review [docs/SPECIFICATION.md](docs/SPECIFICATION.md) for detailed workflows
4. Check [docs/TOKEN_OPTIMIZATION.md](docs/TOKEN_OPTIMIZATION.md) to understand scope

## Governance

- **Security:** OWASP top 10 review on code changes
- **Testing:** >70% coverage required for new code
- **Review:** Code reviewer sign-off required before merge
- **LLM security:** OWASP Top 10 for LLM review on changes to agents, skills, rules, context files, and plugin config
- See [rules/assist-plugin-rule.md](rules/assist-plugin-rule.md) and [rules/llm-security-checklist.md](rules/llm-security-checklist.md); [rules/assist-routing.md](rules/assist-routing.md) is the always-on routing rule

