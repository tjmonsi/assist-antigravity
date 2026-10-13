# assist-antigravity

`assist-plugin` for [Google Antigravity](https://antigravity.google/): 21 skills (17 user-facing, 4 internal) and 15 subagents that cover the development lifecycle from requirements to shipping. The `/do` orchestrator routes each task to a specialist subagent, writes an execution plan for your approval, and runs review loops before work is marked done.

This repo ports the Claude Code plugin [`assist-plugin` v1.10.0](https://github.com/tjmonsi/assist-marketplace-plugin) by Toni-Jan Keith Monserrat to Antigravity's plugin format. Skill and agent content follows upstream; frontmatter, tool names, model tiers, and orchestration steps are rewritten for Antigravity.

## Status

Verified live on the Antigravity CLI (`agy` 1.3.3, 2026-10-12). Items below are results for the 1.7.0-antigravity release (14 subagents) unless marked with a later release:

- `agy plugin install` works from a local clone and from a GitHub subpath URL.
- All 18 skills of that release load as slash commands (`/do`, `/ask`, ...). agy also accepts the namespaced form `/assist-plugin:<name>` and shows that form in the chat (observed on agy 1.3.3).
- All 14 subagents are invocable, with the ported Antigravity tool names.
- The always-on routing rule (`assist-routing.md`) loads.
- Subagents run on the tier in their agent file's `model:` line (observed for `reviewer`, which ran on pro; the other agents use the same mechanism).
- 1.8.0: the always-on `writing-standard-compact.md` rule loads in the main agent and in a subagent (observed for `reviewer` on agy 1.3.3, which named the rule file).
- 1.9.0: `/ask` answered a repo question without an approval step or a shell command.
- 1.9.0: `/deslop` returned a cleaned rewrite in `edit` mode. One `/deslop detect` run ended with no reply (see [Skills](#skills)).
- 1.9.0: `/do` routed a small feature to worker, ran the git config guard and the Preflight disk check, asked the approval question without a model-change option, and its write-path check listed the two files worker changed.
- 1.9.0: subagent shell commands under `/do` are not shown and are denied after about 60 seconds (details below).
- 1.9.0: `intake-reviewer` is invocable from a headless `agy -p` session, and its ten-field terminal block reached the parent agent byte for byte.
- 1.10.0: `/voice-script` and `/clarify` appear in the skill list (listed, not run).

Not yet verified: the 1.10.2 `/do` Hard rules and reference-file loading; the 1.10.2 Testing Gate ending as `Testing Gate not-run (skipped: command denied)`; the 1.10.2 `/ask` changes (search scope and the single `git log` form); the 1.10.2 `DECISIONS.md` timing (appended at Preflight); the 1.10.0 `/do` fixes (the plan table inside the approval question, review gates after a worker step, the subagent-permission message) and the 1.10.0 `/deslop` fix (no shell commands) in a live run; a full `/do` run end to end with its review gates and the qa Testing Gate; the `NeedsInput` relay with `send_message`; `/voice-script` and `/clarify` runs; the always-on attribution reminder loading; the 1.10.1 settings-file denial (the ten write agents and the `/do` write-path check); the 1.10.1 `/commit` and `/bump` config and hook check; Antigravity 2.0 and the Antigravity IDE.

Headless `agy -p` cannot approve shell commands: it denies every `run_command` call, so skills that run commands stop at the first one. The denial message itself names the fix: "Add an allow-rule under permissions.allow in settings.json (e.g. command(<target>))" (observed on agy 1.3.3). Run those skills in an interactive session, or add allow rules for the commands you trust to `~/.gemini/antigravity-cli/settings.json` (the file exists at that path on agy 1.3.3, observed):

```json
{"permissions": {"allow": ["command(df -h .)"]}}
```

The allow rule itself was not exercised in testing. agy may treat an allow rule as a prefix of the command line; then `command(df -h .)` also allows `df -h . && <anything>`. After adding a rule, ask agy to run `df -h . && echo prefix-check`; if it runs without a prompt, remove the rule. Run it as one command line, and the prompt must show the whole line; otherwise the test did not run (a model may split it into two calls, and a prompt for `echo prefix-check` alone would look like a pass). On Windows a `df.cmd` or `df.bat` in the workspace can shadow `df` under a global rule, so do not add the rule there. `agy agents` printed nothing in tests; list subagents with `/agents` in the TUI instead (not exercised in testing).

Subagent commands under `/do` (observed on agy 1.3.3): when developer, worker, qa, or devops asks to run a shell command, the CLI does not show the request. It is denied after about 60 seconds, and typing "approve" or "y" in chat does not approve it. The step then reports the command as skipped. To let a subagent run a command, add an allow rule for an exact command you have read and trust to `~/.gemini/antigravity-cli/settings.json` before you start `/do`, for example `{"permissions": {"allow": ["command(df -h .)"]}}`, then restart agy. Every `git` command reads `.git/config`, which an agent with a write tool can change so that even `git status` runs a program, so do not allow `git` commands either. The rule is global: it applies to every agy session, every workspace, and the main agent too, so a hostile clone can use it as well. agy may match the rule as a prefix, so even an exact command can allow longer commands (see the prefix check above); never write a pattern. Do not allow a test runner or a build command: it runs the repository's own code in every workspace with no prompt. Whether allow rules reach subagents has not been tested. qa's test commands are denied like any other subagent command; whether an allow rule lets them run is untested. 1.10.2 tells `/do` to end the Testing Gate as `Testing Gate not-run (skipped: command denied)` with no fix loop (not yet verified live).

Skill size (observed on agy 1.3.3): when you run a slash command, agy injects the skill's body into the conversation and cuts it at about 24,000 bytes, marked `<truncated N bytes>`. In the observed run the model did not open the file to read the rest, so the cut-off rules never applied. `/do` therefore keeps its states, approval flow, and a short Hard rules section in `SKILL.md` (under 20,000 bytes) and its Preflight, Dispatch, Display, and Cleanup detail in reference files that `SKILL.md` tells the model to open with `view_file`. `scripts/validate.py` warns at 20,000 bytes and fails any skill body of 22,000 bytes or more.

In agy 1.3.3 print mode (`agy -p`), a workspace `.agents/hooks.json` ran in a folder not listed as trusted, with no prompt, so a cloned repository's hooks can run commands in headless mode (interactive sessions not tested). The same probe ran a workspace plugin's hook from `.agents/plugins/`. Before running `agy -p` in a repository you did not write, check `.agents/hooks.json` and `.agents/plugins/`.

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

Restart `agy` after every `agy plugin install` or update. A running session keeps the skill text it loaded at start: in the observed agy 1.3.3 log, skills reloaded only at session start and once more, so an open session can keep running the old `/do`.

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
| Build | ask, developer, developer-tester, devops, general-purpose, intake-reviewer, planner, qa, requirements-gatherer, worker | `flash` | `inherit` | `pro` | `flash` |
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

`/do` classifies the request, picks an agent and tier for each step, writes a plan to `.agent/main-plan/`, shows it in chat as a step table, and asks you to approve, edit, or cancel before running anything. Use the direct skills below when you already know which tool you need.

## Skills

Skills load as `/<name>` (`/do`, `/ask`). agy also accepts the namespaced form `/assist-plugin:<name>` and shows that form in the chat (observed on agy 1.3.3). The text after the command is the skill's input.

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
| `/deslop [edit \| detect] <file-or-text>` | Remove AI writing tells from prose; `edit` returns the cleaned text, `detect` lists findings |
| `/voice-script [topic \| draft-file]` | Write a paste-ready text-to-speech script with the chosen model's own tags and style field, saved to `docs/tts/`; checks OpenRouter's live model list only on request |
| `/clarify [what is unclear]` | Explain unclear points in the agent's last output with evidence, ask you about points only you can settle, and append both to `.agent/clarify/` |

If `/deslop` ends without a reply (observed once on agy 1.3.3 with Gemini 3.8 Flash), run the same command again with the mode word. Without `detect`, pasted text runs in `edit` mode and comes back rewritten.

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
| `general-purpose` | flash | Ad-hoc analysis and experimentation when `/do` explicitly matches it; unmatched work goes to Clarify |
| `intake-reviewer` | flash | Read-only intake review of a user-provided spec or requirements file before `/do` plans write steps |
| `planner` | flash | Architecture, roadmaps, dependency and risk analysis |
| `qa` | flash | Test plans, acceptance validation, pentest, integration and coverage checks |
| `requirements-gatherer` | flash | Requirements elicitation, BRD/URD, FR and NFR |
| `researcher` | pro | Web research, documentation audit, best practices |
| `reviewer` | pro | Code review for bugs, security (OWASP), and quality |
| `solutions-architect` | pro | Requirements to specs, APIs, schemas, data flows |
| `worker` | flash | Multi-discipline generalist for small features |

The five subagents granted `run_command` (developer, devops, general-purpose, qa, worker) use `commandExecutionPolicy: sandbox`; the other ten have no shell and use `off`. Subagents inherit the parent's permission and sandbox settings, so the frontmatter `sandbox` value does not override a permissive user setting. Every agent sets `mainAgent: false`: none can run as the chat's primary agent, and `/do` is the entry point.

## Governance

The rules in [`plugins/assist-plugin/rules/`](plugins/assist-plugin/rules/) define the gates `/do` enforces:

- **OWASP Top 10** review on code changes
- **OWASP for LLM** review on changes to agents, skills, and rules ([`llm-security-checklist.md`](plugins/assist-plugin/rules/llm-security-checklist.md))
- **Planning document** review before a plan runs
- **Test coverage** of at least 70% for new code
- **Code review sign-off** before merge, plus the merge policy

[`assist-routing.md`](plugins/assist-plugin/rules/assist-routing.md) is always on and sends actionable development prompts to `/do`; it also carries a one-line reminder never to add AI attribution (a Co-Authored-By trailer, a "Generated with" footer, an AI session link) to commit messages, tags, or PR bodies. [`assist-plugin-rule.md`](plugins/assist-plugin/rules/assist-plugin-rule.md) holds the full gate definitions and the untrusted-content rules, and loads when the model judges it relevant.

[`writing-standard-compact.md`](plugins/assist-plugin/rules/writing-standard-compact.md) is also always on: twelve bullets on how agents write prose (answer first, three-part findings, plain words, no em dashes). It does not apply to code, data, or quoted text, and your project and user instructions take precedence. [`writing-standard.md`](plugins/assist-plugin/rules/writing-standard.md) holds the full rules and loads on demand, for example when `/deslop` or `/review-md` runs.

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

The `pentest` skill (preloaded by qa) uses these against authorized targets only. Commands, versions, and caveats are in [tooling.md](plugins/assist-plugin/skills/pentest/references/tooling.md), the ZAP runbook in [zap.md](plugins/assist-plugin/skills/pentest/references/zap.md), and per-ecosystem audit commands in the skill's [Dependency Audit](plugins/assist-plugin/skills/pentest/SKILL.md#dependency-audit) table. Under `/do`, plan approval authorizes the listed commands and target; outside `/do`, qa's caller asks you first.

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
| Model change at plan approval | The approval question offers Approve, Edit steps, Change models, or Cancel | Approve, Edit steps, or Cancel. The agent file's `model:` line overrides `invoke_subagent`'s `Model` parameter, so a model change means running `scripts/set-model-profile.sh`, restarting Antigravity (or the `agy` session), and re-running `/do` |
| Concurrent code writes | Each wave of independent steps runs as background agents | Overlapping code-writing steps run sequentially in workspace `inherit`; the `branch` workspace is not used until worktree merge-back is verified on a live install |
| Hooks | `doc-cli-guard`, `sa-mermaid-only`, a SessionStart `health-check`, from v1.8.0 `injection-filter`, `prose-gate`, `prose-advisor`, and `writing-context`, from v1.9.0 `fsa-write-bar` and `fsa-log`, and from v1.10.0 `commit-attribution-guard` | None shipped. Antigravity hook payloads name the calling conversation but not the calling agent, and there is no SessionStart, SubagentStart, SubagentStop, or UserPromptSubmit event. In agy 1.3.3, a PostToolUse hook's input for `view_file` carries no tool result and the undocumented `overwrite_result` output had no effect on a `view_file` result; a PreToolUse hook that prints nothing and exits 0 leaves the call to the normal permission flow, while `{}` and `{"decision":""}` deny it; a PreToolUse hook that exits non-zero, cannot start, times out, prints output agy cannot parse, or returns an unknown decision blocks every call its matcher covers; and a PostToolUse hook that exits 1 or prints unparsable output replaces a `view_file` result with an error. Tested only in agy 1.3.3 CLI print mode on Linux; interactive sessions, the IDE, Antigravity 2.0, Windows, and macOS are untested. |
| Test-path write scope | `fsa-write-bar` hook denies developer-tester writes outside test paths and developer writes to test paths | Text rules plus detection: developer-tester holds only `write_to_file` and no shell, and `/do` compares the files each step changed with its approved Writes after the step reports, recording each mismatch as a finding. Nothing blocks the write, and git-ignored paths escape the snapshot |
| Terminal-block log and table check | `fsa-log` hook logs each subagent's terminal block; `scripts/check-fsa-tables.js` compares the hook tables with the markdown | `/do` parses every terminal block itself; `scripts/validate.py` checks the `## States` tables and `fsa` blocks |
| `NeedsInput` resume | Resumes the subagent with `SendMessage` to its agent ID | `send_message` to the subagent's conversation ID; a killed subagent is started again with `invoke_subagent`, the original prompt, and the answers |
| Named skill for debug and technical-writing | `/do` computes the skill path from the "Base directory for this skill" line | `/do` copies the absolute path from the "Available skills" list in its system prompt |
| Commit attribution | `commit-attribution-guard` hook denies `git commit`, `git merge`, `gh pr create`, and `gh pr edit` when the message or body holds an AI attribution line; `/health` reports Claude Code's attribution settings | Text only: the No AI Attribution Rule in `assist-plugin-rule.md`, `/commit`, `/bump`, and a one-line always-on reminder in `assist-routing.md`. Nothing checks the message. The agy 1.3.3 binary holds no attribution string of its own (searched for "co-authored") |
| Document-skill write scope | `Edit(./path)` rules let `gather-requirements`, `spec-from-requirements`, `technical-writing`, `clarify`, and `voice-script` write their own files without a prompt and prompt for any other path | Each skill names its paths; any other path needs your confirmation (`ask_question`, or the approved Writes under `/do`). Nothing enforces the list |
| `/voice-script` live check | Fetches OpenRouter's speech-model list on every run with `WebFetch`, limited to `openrouter.ai`, through an extraction prompt | Uses the built-in catalog (verified 2026-10-12) and fetches the list only when you ask. `read_url_content` returns the whole reply and has no domain limit, so the skill text limits which URLs it fetches and which fields it reads |
| Context-file writes | The `fsa-write-bar` hook denies `CLAUDE.md` and `AGENTS.md` to developer-tester only | developer, devops, general-purpose, planner, qa, requirements-gatherer, researcher, solutions-architect, and worker never write `AGENTS.md`, `GEMINI.md`, `CLAUDE.md`, or a `.agents` path (developer-tester's test-path denials cover the same names), and `/do`'s write-path check flags such a write even when the plan's Writes list it. All ten agents with a write tool also never write under `~/.gemini/`, where Antigravity keeps its settings and permissions, and never add an allow rule; `/do` sees such a path only in a step's reported `artifact` list (git diff paths are repo-relative), and its write-path check flags it there. The check compares paths as strings, so a write through an in-repo symlink escapes it. These are text rules plus detection; nothing blocks the write |
| Prompt-injection filter | `injection-filter` hook rewrites injection sentences in web, MCP, and subagent results | No filter. The governance rule's Untrusted Content section and each skill's own text tell agents to treat fetched content and subagent results as data and report injection attempts; nothing filters them automatically |
| Writing standard | `writing-context` hook injects the compact rules into the session and each subagent; `prose-gate` and `prose-advisor` check prose writes | `rules/writing-standard-compact.md` loads as an `always_on` rule; writes are not checked. Use `/deslop detect` or `/review-md` to check prose |
| Output style | Opt-in `assist-plugin:terse` output style | Not ported; Antigravity plugins have no output styles, and the always-on writing rule covers its core (answer first, no preamble or recap) |
| `/health` skill | Reports hook health and self-tests the hooks | Not ported (no hooks to report on) |
| Command pre-approval | `allowed-tools` pre-approves exact test-runner, audit, git, and doc-CLI commands | No pre-approval; skills list the safe read-only form of each command, and anything that runs repo-controlled code or needs network runs only after you confirm |
| Security scans from qa | Under `/do`, plan approval authorizes the listed commands; permission prompts are the backstop | Under `/do`, plan approval authorizes the listed commands and qa reports any other in `out_of_scope`; a subagent's approval request may be denied rather than prompted. Outside `/do`, qa has no `ask_question`, so it hands the exact command and target back to the agent that started it, which asks you |
| Worktree cleanup | `/branch cleanup` sweeps merged worktrees directly; the `/do` Cleanup state removes the worktrees its own steps created | `/branch cleanup` shows a dry-run listing and asks for confirmation with `ask_question` before removing anything; `/do` creates no worktrees, so its Cleanup state only chooses the terminal status (it keeps the disk-space preflight) |
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

The validator uses the Python standard library only. It checks `plugin.json` keys, agent frontmatter (tool names, `model`, `commandExecutionPolicy`, `mainAgent: false`, `run_command` requiring `sandbox`, `skills:` paths), skill and rule frontmatter, the 24,000-byte rule size limit, the tier table in `set-model-profile.sh`, relative markdown links, control bytes (anything but TAB and LF) and TABs outside fenced code in markdown, invisible Unicode (bidi controls and tag characters are errors, zero-width characters are warnings) in markdown and `plugin.json`, leftover Claude Code terms, the FSA `## States` tables and `fsa` terminal blocks, em dashes and curly quotes in prose (warnings), and that every `## Report Writing Standard` block matches `rules/writing-standard-compact.md` (fix drift with `python3 scripts/sync-writing-standard.py`). It prints `ERROR` and `WARN` lines and exits 1 on any error. Contributor workflow is in [AGENTS.md](AGENTS.md).

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
│       ├── agents/            # 15 subagents
│       ├── skills/            # 21 skills (17 user-facing, 4 internal)
│       ├── rules/             # routing rule, governance gates, LLM security checklist, writing standard
│       ├── docs/              # specification, architecture, standards
│       ├── README.md          # plugin quick reference
│       ├── CHANGELOG.md       # upstream plugin history
│       ├── LICENSE
│       └── NOTICE
└── scripts/
    ├── install.sh             # copy the plugin into Antigravity 2.0 / IDE folders
    ├── set-model-profile.sh   # switch subagent model tiers
    ├── sync-writing-standard.py  # copy the compact writing rules into every Report Writing Standard block
    └── validate.py            # static format checker
```

## License

Copyright (C) 2026 Toni-Jan Keith Monserrat

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.

The full license text is in [LICENSE](LICENSE) (also shipped as [`plugins/assist-plugin/LICENSE`](plugins/assist-plugin/LICENSE)). [NOTICE](NOTICE) and [`plugins/assist-plugin/NOTICE`](plugins/assist-plugin/NOTICE) carry the attribution and license history.

The 1.5.0-antigravity port was licensed under MIT and was not published; from 1.7.0-antigravity the port is licensed under AGPL-3.0-or-later, following upstream assist-plugin v1.7.0. Components derived from the earlier MIT-licensed software-development plugin keep their original MIT notice, reproduced in NOTICE.
