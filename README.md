# assist-antigravity

`assist-plugin` for [Google Antigravity](https://antigravity.google/): 18 skills (14 user-facing, 4 internal) and 14 subagents that cover the development lifecycle from requirements to shipping. The `/do` orchestrator routes each task to a specialist subagent, writes an execution plan for your approval, and runs review loops before work is marked done.

This repo ports the Claude Code plugin [`assist-plugin` v1.7.0](https://github.com/tjmonsi/assist-marketplace-plugin) by Toni-Jan Keith Monserrat to Antigravity's plugin format. Skill and agent content follows upstream; frontmatter, tool names, model tiers, and orchestration steps are rewritten for Antigravity.

## Status

Verified live on the Antigravity CLI (`agy` 1.3.3, 2026-10-12):

- `agy plugin install` works from a local clone and from a GitHub subpath URL.
- All 18 skills load as slash commands without a plugin prefix (`/do`, `/ask`, ...).
- All 14 subagents are invocable, with the ported Antigravity tool names.
- The always-on routing rule (`assist-routing.md`) loads.
- Subagents run on the tier in their agent file's `model:` line (observed for `reviewer`, which ran on pro; the other agents use the same mechanism).

Not yet verified: a full `/do` run end to end, Antigravity 2.0, and the Antigravity IDE.

Headless `agy -p` cannot approve shell commands: it denies every `run_command` call, so skills that run commands stop at the first one. The denial message itself names the fix: "Add an allow-rule under permissions.allow in settings.json (e.g. command(<target>))" (observed on agy 1.3.3). Run those skills in an interactive session, or add allow rules for the commands you trust to `~/.gemini/antigravity-cli/settings.json` (the file exists at that path on agy 1.3.3, observed):

```json
{"permissions": {"allow": ["command(git status)"]}}
```

The allow rule itself was not exercised in testing. `agy agents` printed nothing in tests; list subagents with `/agents` in the TUI instead (not exercised in testing).

`scripts/validate.py` also checks the plugin statically against Antigravity's documented plugin, subagent, skill, and rule formats. Please report install or loading problems in [GitHub issues](https://github.com/tjmonsi/assist-antigravity/issues).

## Install

### Antigravity CLI

Install straight from GitHub:

```bash
agy plugin install https://github.com/tjmonsi/assist-antigravity/plugins/assist-plugin
```

Or from a local clone:

```bash
git clone https://github.com/tjmonsi/assist-antigravity.git
agy plugin install /path/to/assist-antigravity/plugins/assist-plugin
```

Manage the plugin with `agy plugin list`, `agy plugin enable assist-plugin`, `agy plugin disable assist-plugin`, and `agy plugin uninstall assist-plugin`. Inside the CLI's TUI, `/plugin` opens the plugin manager.

`agy plugin install` stages the plugin in `~/.gemini/config/plugins/assist-plugin/` (observed on `agy` 1.3.3). Older docs name `~/.gemini/antigravity-cli/plugins/`. This is the same folder that `scripts/install.sh --global` writes to, so CLI users should prefer `agy plugin install`, which also records the install.

### Antigravity 2.0 and Antigravity IDE

Both apps load plugins from a folder. Copy `plugins/assist-plugin` to one of these locations (use `scripts/install.sh` for these apps; CLI users should use `agy plugin install` above):

| Scope | Path |
|---|---|
| Global (all workspaces) | `~/.gemini/config/plugins/assist-plugin` |
| One workspace | `<workspace>/.agents/plugins/assist-plugin` |

`scripts/install.sh` does the copy:

```bash
git clone https://github.com/tjmonsi/assist-antigravity.git
cd assist-antigravity

./scripts/install.sh                                # global install
./scripts/install.sh --workspace ~/code/my-app      # workspace install
./scripts/install.sh --force --profile inherit      # replace an existing install, subagents follow your model
```

| Flag | Effect |
|---|---|
| `--global` | Copy to `~/.gemini/config/plugins/assist-plugin` (default) |
| `--workspace <dir>` | Copy to `<dir>/.agents/plugins/assist-plugin` |
| `--profile <name>` | Run `set-model-profile.sh` on the installed copy (`gemini`, `inherit`, `gemini-pro`, `gemini-flash`) |
| `--force` | Replace an existing `assist-plugin` install at the target |

The script copies files only: no network access, no sudo. It refuses to touch an existing target unless you pass `--force`, and even then refuses a target that is a symlink or that lacks an `assist-plugin` `plugin.json`. Restart Antigravity after installing; the docs do not say whether a running session picks up new plugin folders. Loaded skills, subagents, and rules appear in the Customizations panel ([plugin docs](https://antigravity.google/docs/plugins/)).

There is no marketplace manifest. Antigravity's `agy plugin` marketplace argument accepts only `antigravity-plugins-official`, so third-party marketplaces cannot be added.

## Choosing models

The main agent, which runs `/do` and every other slash command, uses the model you select in Antigravity: `/model` in the CLI, or the model selector under the prompt box in Antigravity 2.0 and the IDE. Per the [Antigravity models page](https://antigravity.google/docs/models/) (as of 2026-10-12), the list includes Gemini 3.8, 3.7, and 3.6 Flash, Gemini 3.1 Pro, and, on Pro, Ultra, and non-trial Enterprise plans, Claude Sonnet 5.5 and Claude Opus 5.5.

Subagents read their model from the `model:` line in `agents/<name>.md`, which accepts `inherit`, `flash`, or `pro`. `invoke_subagent` also exposes a per-call `Model` parameter (`inherit`, `flash_lite`, `flash`, `pro`), but on `agy` 1.3.3 the agent file's `model:` line won in every test (parameter omitted, `inherit`, and `flash_lite`): `reviewer` (`model: pro`) ran on Gemini 3.1 Pro while the parent ran on Gemini 3.8 Flash. The profile script below is the control that works. The plugin ships the `gemini` profile:

| Tier | Agents | `gemini` (shipped) | `inherit` | `gemini-pro` | `gemini-flash` |
|---|---|---|---|---|---|
| Review | code-reviewer, reviewer, researcher, solutions-architect | `pro` | `inherit` | `pro` | `flash` |
| Build | ask, developer, developer-tester, devops, general-purpose, planner, qa, requirements-gatherer, worker | `flash` | `inherit` | `pro` | `flash` |
| Fast | explore | `flash` | `inherit` | `pro` | `flash` |

Switch profiles with `scripts/set-model-profile.sh <profile> [plugin-dir]`. Without `plugin-dir`, the script edits this repo's `plugins/assist-plugin`; pass the installed copy's path to change what Antigravity loads:

```bash
# Run every subagent on the model you selected (use this to run everything on Claude)
./scripts/set-model-profile.sh inherit ~/.gemini/config/plugins/assist-plugin

# Global install (CLI, Antigravity 2.0, or IDE): every subagent on pro
./scripts/set-model-profile.sh gemini-pro ~/.gemini/config/plugins/assist-plugin

# Workspace install
./scripts/set-model-profile.sh gemini-flash ~/code/my-app/.agents/plugins/assist-plugin
```

The script rewrites only the `model:` line in each agent's frontmatter and checks every file before writing any. Re-installing the plugin restores the shipped `gemini` profile, so re-run the script (or pass `--profile` to `install.sh`) after each install or update. After switching profiles, restart Antigravity and re-run `/do` so the session picks up the new `model:` values.

## Quick start

```text
/do implement user authentication
/pr-review 123 --approve
/bump minor
/debug analyze
```

`/do` classifies the request, picks an agent and tier for each step, writes a plan to `.agent/main-plan/`, and asks for approval before running anything. Use the direct skills below when you already know which tool you need.

## Skills

Antigravity exposes every skill as a slash command without a plugin prefix (`/do`, not `/assist-plugin:do`, observed on `agy` 1.3.3). The text after the command is the skill's input.

| Command | Purpose |
|---|---|
| `/do [task]` | Route a task to the best subagent, plan it, and coordinate review loops |
| `/ask [--web] <question>` | Answer questions from the repo, optionally with web research, citing sources |
| `/debug [analyze \| fix \| review] [description \| file:line]` | Root cause analysis and iterative fixes |
| `/bump [patch \| minor \| major \| auto] [--path PATH] [--no-tag] [--no-commit]` | Semantic version bump with changelog generation |
| `/pr-review [PR# \| branch] [--approve \| --changes-requested \| --comment] [--message TEXT]` | Review GitHub or Bitbucket pull requests with platform auto-detection |
| `/commit [--squash] [--amend] [--scope SCOPE] [TYPE: message]` | Create conventional commits |
| `/branch [create \| switch \| list \| cleanup] [branch-name \| --dry-run]` | Create, switch, and list git branches; clean up merged worktrees after a dry-run and your confirmation |
| `/map-project` | Discover repo structure, tech stack, and dependencies |
| `/technical-writing [docs \| readme \| guide \| api] [topic \| file]` | Generate and update technical documentation |
| `/review-md <path-to-report.md>` | Review a markdown report for consistency, conciseness, and accuracy |
| `/gather-requirements [elicit \| document \| review] [topic \| file]` | Elicit and document requirements (IEEE 29148, RFC 2119) |
| `/spec-from-requirements [create \| delta \| review] [feature \| file]` | Write feature specs and delta specs from requirements |
| `/task-plan <spec-file-or-prompt> [language]` | Turn a spec into ordered coding steps |
| `/create-test [spec-file \| feature] [language]` | Generate black-box acceptance-criteria tests |

`/pr-review` uses the `gh` CLI for GitHub and the `bkt` CLI for Bitbucket. See [Recommended CLI tools](#recommended-cli-tools).

Four internal skills are preloaded by subagents. Antigravity cannot hide skills, so they also appear as slash commands; their descriptions start with "Internal:".

| Skill | Preloaded by | Purpose |
|---|---|---|
| `code` | developer | Language and framework standards, logging, error handling, traceability |
| `pentest` | qa | OWASP Top 10 and LLM guardrail security testing |
| `integrated-test` | qa | Integration and E2E testing patterns (testcontainers, Playwright) |
| `run-test` | qa | Run test suites, capture coverage, produce consolidated reports |

## Subagents

Tiers show the shipped `gemini` profile.

| Agent | Tier | Purpose |
|---|---|---|
| `ask` | flash | Answer questions using repo search and optional web research |
| `code-reviewer` | pro | Formal line-by-line code review and sign-off |
| `developer` | flash | Write, fix, and refactor code from specs |
| `developer-tester` | flash | Write black-box acceptance-criteria tests without reading the implementation |
| `devops` | flash | CI/CD, infrastructure, deployment, monitoring |
| `explore` | flash | Fast read-only code search |
| `general-purpose` | flash | Catch-all for unmatched tasks |
| `planner` | flash | Architecture, roadmaps, dependency and risk analysis |
| `qa` | flash | Test plans, acceptance validation, pentest, integration and coverage checks |
| `requirements-gatherer` | flash | Requirements elicitation, BRD/URD, FR and NFR |
| `researcher` | pro | Web research, documentation audit, best practices |
| `reviewer` | pro | Code review for bugs, security (OWASP), and quality |
| `solutions-architect` | pro | Requirements to specs, APIs, schemas, data flows |
| `worker` | flash | Multi-discipline generalist for small features |

The five subagents granted `run_command` (developer, devops, general-purpose, qa, worker) use `commandExecutionPolicy: sandbox`; the other nine have no shell and use `off`. Subagents inherit the parent's permission and sandbox settings, so the frontmatter `sandbox` value does not override a permissive user setting. Every agent sets `mainAgent: false`: none can run as the chat's primary agent, and `/do` is the entry point.

## Governance

The rules in [`plugins/assist-plugin/rules/`](plugins/assist-plugin/rules/) define the gates `/do` enforces:

- **OWASP Top 10** review on code changes
- **OWASP for LLM** review on changes to agents, skills, and rules ([`llm-security-checklist.md`](plugins/assist-plugin/rules/llm-security-checklist.md))
- **Planning document** review before a plan runs
- **Test coverage** above 70% for new code
- **Code review sign-off** before merge, plus the merge policy

[`assist-routing.md`](plugins/assist-plugin/rules/assist-routing.md) is always on and sends actionable development prompts to `/do`. [`assist-plugin-rule.md`](plugins/assist-plugin/rules/assist-plugin-rule.md) holds the full gate definitions and loads when the model judges it relevant.

## Recommended CLI tools

The plugin works without these tools; agents detect each one before use and fall back or skip the step when it is missing. Install only what your workflow needs. Agents never run installs: they show the command and you run it.

### Core

| Tool | Install | Used by | Required? |
|---|---|---|---|
| git | Your OS package manager | `commit`, `branch`, `bump`, `pr-review`, `/do` review diffs | Yes |
| uv | Follow the [uv installation docs](https://docs.astral.sh/uv/getting-started/installation/) | Preferred installer and runner for Python tooling | Recommended |
| Python 3 | Your OS package manager (uv can also fetch Python) | Python-based scanners (Semgrep, garak, PyRIT, pip-audit); pip fallback when uv is absent | Recommended |

Every Python command in the plugin shows the uv form first and the pip or pipx form second. Agents detect uv with `command -v uv` and run tests with the no-install form `uv run --no-sync --no-python-downloads pytest ...`, which needs an existing `.venv` (create it with `uv sync`). Global CLI tools install with `uv tool install [--python X] <pkg>` (fallback `pipx install`); per-project tools with `uv add --dev <pkg>` (fallback `python -m pip install <pkg>` inside the project's virtual environment).

### PR platforms

Install only the one you use. Authenticate with `gh auth login` or `bkt auth login` (check with `gh auth status` or `bkt auth status`).

| Tool | Install | Used by |
|---|---|---|
| `gh` (GitHub) | `brew install gh` or `winget install GitHub.cli` | `pr-review` |
| `bkt` (Bitbucket, [avivsinai/bitbucket-cli](https://github.com/avivsinai/bitbucket-cli)) | `brew install avivsinai/tap/bitbucket-cli`, `winget install AvivSinai.Bitbucket-CLI`, or `go install github.com/avivsinai/bitbucket-cli/cmd/bkt@latest` | `pr-review` |

### Docs lookup, diagrams, and testing

| Tool | Install | Used by |
|---|---|---|
| `ctx7` | `npm install -g ctx7`; optional `CONTEXT7_API_KEY` for higher rate limits | `code` skill (developer) |
| `firecrawl` | `npm install -g firecrawl-cli`, then `firecrawl login` or set `FIRECRAWL_API_KEY` | `code` skill (developer). researcher has no shell and shows you the command instead |
| `mmdc` | `npm install -g @mermaid-js/mermaid-cli` | `spec-from-requirements` PNG rendering, run by you, devops, or the main agent (solutions-architect has no shell) |
| Playwright | `npm install -D @playwright/test && npx playwright install` | `integrated-test` (E2E) |
| Docker | Your OS package manager or docker.com | `integrated-test` (testcontainers), OWASP ZAP |

`run-test` uses your project's own runner (`pytest`, `npm test`, `npx --no vitest run`, `npx --no jest`, `go test`, `cargo test`, `./gradlew test`). The `--no` flag stops `npx` from downloading a missing package.

Nothing in this port checks firecrawl or ctx7 command shapes at run time; the `code` skill states the allowed forms. To block the config-writing subcommands outright, add `command(firecrawl env)`, `command(ctx7 setup)`, and `command(ctx7 login)` to your Antigravity permission Deny list (syntax follows agy's allow-rule message; deny rules were not tested).

### Security testing

The `pentest` skill (preloaded by qa) uses these against authorized targets only. Commands, versions, and caveats are in [tooling.md](plugins/assist-plugin/skills/pentest/references/tooling.md), the ZAP runbook in [zap.md](plugins/assist-plugin/skills/pentest/references/zap.md), and per-ecosystem audit commands in the skill's [Dependency Audit](plugins/assist-plugin/skills/pentest/SKILL.md#dependency-audit) table. qa asks you, through `/do`, before every scan or audit.

| Area | Tools |
|---|---|
| Web, dynamic | OWASP ZAP (`docker pull zaproxy/zap-stable`), Nuclei |
| Web, static | Semgrep CE (`uv tool install semgrep`), CodeQL (not open source; GitHub licenses its CLI for public repositories on GitHub.com and for organization repositories with GitHub Code Security) |
| LLM/bot | promptfoo (`npm install -g promptfoo`, Node.js 22.22.0+), garak (`uv tool install --python 3.13 garak`), PyRIT (`uv tool install --python 3.13 pyrit`) |
| Dependency audit | Built in: `npm audit`, `pnpm audit`, `bun audit`, `composer audit`, `uv audit`. Install: `pip-audit`, `govulncheck`, `cargo-audit`, `bundler-audit`, `osv-scanner`, Trivy (pin the version and verify signatures; Trivy v0.69.4 binaries and Docker images 0.69.5 and 0.69.6 were malicious in March 2026), Grype |

### Check what you have

```bash
for t in git node npm uv python3 gh bkt ctx7 firecrawl mmdc docker promptfoo garak pyrit_scan semgrep pip-audit osv-scanner; do command -v "$t" >/dev/null && echo "ok      $t" || echo "missing $t"; done
```

## Differences from the Claude Code version

| Area | Claude Code (upstream) | Antigravity (this repo) |
|---|---|---|
| Install | Marketplace `assist-plugin@assist-plugin-marketplace` | `agy plugin install` or folder copy; no marketplace |
| Models | Opus, Sonnet, Haiku per agent | `pro`, `flash`, or `inherit` per agent, switched with `set-model-profile.sh` |
| Tools | Claude tool names, including LSP | Antigravity tool names (`view_file`, `run_command`, `invoke_subagent`, ...); LSP dropped, no equivalent |
| solutions-architect | Shell restricted to mermaid-cli by a Claude hook | No shell access; Mermaid source is embedded instead of rendered to PNG |
| researcher | Shell available for firecrawl | No shell (`commandExecutionPolicy: "off"`); uses `search_web` and `read_url_content`, and tells you the firecrawl command if you want it |
| ask | Hands off to explore or researcher | No handoff; Antigravity gives it no `invoke_subagent`, so it searches with its own tools and recommends researcher when deep research is needed |
| Model change at plan approval | Pick a model per agent when approving the plan | Not possible; run `scripts/set-model-profile.sh`, then restart Antigravity (or the `agy` session) and re-run `/do` |
| Concurrent code writes | Independent steps run as background agents | Overlapping code-writing steps run sequentially in workspace `inherit`; the `branch` workspace is not used until worktree merge-back is verified on a live install |
| Hooks | `doc-cli-guard`, `sa-mermaid-only`, and a SessionStart `health-check` in `hooks/` | None shipped; upstream v1.6+ hooks (doc-cli-guard, sa-mermaid-only, health-check) not ported: Antigravity hook payloads do not identify the calling agent, there is no SessionStart event, and the no-match decision for doc-cli-guard needs a live test |
| `/health` skill | Reports hook health | Not ported (no hooks to report on) |
| Command pre-approval | `allowed-tools` pre-approves exact test-runner, audit, git, and doc-CLI commands | No pre-approval; skills list the safe read-only form of each command, and anything that runs repo-controlled code or needs network runs only after you confirm |
| Security scans from qa | Claude prompts per scanner command | qa has no `ask_question`, so it stops and hands the exact command and target back to `/do`, which asks you before qa runs it |
| Worktree cleanup | `/branch cleanup` sweeps merged worktrees directly; `/do` Step 7 removes the worktrees its own steps created | `/branch cleanup` shows a dry-run listing and asks for confirmation with `ask_question` before removing anything; `/do` creates no worktrees and has no cleanup step (it keeps the disk-space preflight) |
| Internal skills | Hidden from the slash menu | Visible, marked "Internal:" |
| Skill metadata | `metadata.json` per skill | Removed; `effort` and `argument-hint` live under `metadata:` in `SKILL.md` |
| Manifest | `plugin.json` with `version` | `plugin.json` with `name`, `version`, and `description`; release notes in [CHANGELOG.md](CHANGELOG.md) |
| Repo guidance | `CLAUDE.md` | [AGENTS.md](AGENTS.md) |
| License | AGPL-3.0-or-later from v1.7.0 (MIT up to v1.6.1) | AGPL-3.0-or-later from 1.7.0-antigravity (1.5.0-antigravity was MIT and never published) |

Upstream token-savings figures in [`docs/TOKEN_OPTIMIZATION.md`](plugins/assist-plugin/docs/TOKEN_OPTIMIZATION.md) were measured on the Claude Code build and have not been re-measured on Antigravity.

## Validating changes

```bash
python3 scripts/validate.py                  # checks plugins/assist-plugin
python3 scripts/validate.py path/to/plugin   # checks another copy
agy plugin validate plugins/assist-plugin    # Antigravity's structural check
```

`agy plugin validate` checks structure only. In tests it accepted wrong tool names, `model: sonnet`, invalid rule triggers, and skills with no description, so `scripts/validate.py` stays the required gate.

The validator uses the Python standard library only. It checks `plugin.json` keys, agent frontmatter (tool names, `model`, `commandExecutionPolicy`, `mainAgent: false`, `run_command` requiring `sandbox`, `skills:` paths), skill and rule frontmatter, the 24,000-byte rule size limit, the tier table in `set-model-profile.sh`, relative markdown links, control bytes (anything but TAB and LF) and TABs outside fenced code in markdown, invisible Unicode (bidi controls and tag characters are errors, zero-width characters are warnings) in markdown and `plugin.json`, and leftover Claude Code terms. It prints `ERROR` and `WARN` lines and exits 1 on any error. Contributor workflow is in [AGENTS.md](AGENTS.md).

## Repository layout

```text
assist-antigravity/
├── AGENTS.md                  # contributor guidance for agents and humans
├── CHANGELOG.md               # release history
├── LICENSE                    # AGPL-3.0-or-later
├── NOTICE                     # attribution and license history
├── README.md
├── plugins/
│   └── assist-plugin/         # the Antigravity plugin; install this folder
│       ├── plugin.json        # name, version, description
│       ├── agents/            # 14 subagents
│       ├── skills/            # 18 skills (14 user-facing, 4 internal)
│       ├── rules/             # routing rule, governance gates, LLM security checklist
│       ├── docs/              # specification, architecture, standards
│       ├── README.md          # plugin quick reference
│       ├── CHANGELOG.md       # upstream plugin history
│       ├── LICENSE
│       └── NOTICE
└── scripts/
    ├── install.sh             # copy the plugin into Antigravity 2.0 / IDE folders
    ├── set-model-profile.sh   # switch subagent model tiers
    └── validate.py            # static format checker
```

## License

Copyright (C) 2026 Toni-Jan Keith Monserrat

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.

The full license text is in [LICENSE](LICENSE) (also shipped as [`plugins/assist-plugin/LICENSE`](plugins/assist-plugin/LICENSE)). [NOTICE](NOTICE) and [`plugins/assist-plugin/NOTICE`](plugins/assist-plugin/NOTICE) carry the attribution and license history.

The 1.5.0-antigravity port was licensed under MIT and was not published; from 1.7.0-antigravity the port is licensed under AGPL-3.0-or-later, following upstream assist-plugin v1.7.0. Components derived from the earlier MIT-licensed software-development plugin keep their original MIT notice, reproduced in NOTICE.
