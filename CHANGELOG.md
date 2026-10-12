# Changelog

All notable changes to assist-antigravity are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions track the upstream [`assist-plugin`](https://github.com/tjmonsi/assist-marketplace-plugin) release they are ported from, with an `-antigravity` suffix. Upstream history before the port is in [`plugins/assist-plugin/CHANGELOG.md`](plugins/assist-plugin/CHANGELOG.md).

## [1.8.0-antigravity] - 2026-10-12

Synced with upstream assist-plugin v1.8.0 (442d34e). Not yet verified live: `/deslop` and the `/do` plan table and approval loop.

### Added

- `/deslop [edit | detect] <file-or-text>`: removes AI writing tells from prose without changing facts, quotations, or the writer's voice. `edit` returns the cleaned text (or edits a file the user named with `replace_file_content`), `detect` lists findings and changes nothing. Its word-tell catalog points at "Mechanical tiers" in `rules/writing-standard.md`, because upstream's exact phrase list lives in a hook library the port does not ship. The plugin now has 19 skills (15 user-facing, 4 internal).
- `rules/writing-standard.md` (`trigger: model_decision`): every writing rule with its reason, examples, block and advisory tiers, exemptions, and scope. Hook references are rewritten as rules writers and reviewers apply.
- `rules/writing-standard-compact.md` (`trigger: always_on`, 1,504 bytes): the twelve compact bullets, opened by upstream's scoping sentence (prose only; project and user instructions take precedence). It replaces upstream's `writing-context` hook.
- "Untrusted Content" section in `rules/assist-plugin-rule.md`: web pages, MCP results, `curl`/`wget`/`firecrawl`/`ctx7` output, PR text, scanner output, and subagent results are data; eight injection patterns are reported as LLM01 findings and never followed. The section states that nothing filters content automatically.
- `code/references/code-slop.md`, a catalog of generated-code tells, linked from the `code` checklist, the developer self-review, and the reviewer's adversarial reflection.
- "Review Output Rules" in `do/references/review-protocol.md`, linked from reviewer, code-reviewer, and `/pr-review`. `/pr-review` treats existing PR reviews read for "only new findings" as untrusted data.
- `scripts/sync-writing-standard.py` (stdlib port of upstream's `sync-writing-standard.js`): rewrites every `## Report Writing Standard` block from the compact rule; `--check` exits 1 on drift.
- `scripts/validate.py`: ERROR on any Report Writing Standard block that differs from the compact rule; WARN on em dashes and curly quotes in plugin markdown prose (fenced code, inline code, and double-quoted examples skipped); Claude-ism warnings for upstream hook names, `prose-rules.js`, and output styles.

### Changed

- `/do` Steps 3 and 4: clarify ambiguities with `ask_question` first, write the plan with a step table and Order line, print the table in chat, then ask Approve, Edit steps, or Cancel. Edits re-show the table and ask again; Cancel sets the plan to `Cancelled`; Approve records answers under `## User Decisions`. A wave of steps starts in one `invoke_subagent` call (at most 3 entries, read-only or non-overlapping writes only), and plan status moves through `In Progress` and `Complete`.
- `/do` Step 5 tells the orchestrator to treat subagent results as data and to label them when passing them to another subagent.
- `plan-format.md`: step table with `pro / flash / inherit` models, Runs values, `## User Decisions`, `## Step Details`, and the `Cancelled` status; the port's `Concurrent` and `Workspace` fields stay. `agent-registry.md` "Model Tier Changes" points at the new approval loop.
- Report Writing Standard blocks in 32 agent and skill files now carry the twelve compact bullets. `commit` moves its subject-line exemption into Constraints, and the debug review keeps its badge exception outside the block.
- TypeScript guidance: `unknown` only at trust boundaries, narrowed immediately; `retry-backoff.md` narrows at the boundary.
- `review-md` reuses the deslop catalogs for its conciseness check; `DOCUMENTATION_STANDARD.md` keeps only documentation-specific rules.
- De-slop pass over agents, skills, rules, docs, READMEs, and code comments: em dashes, prose arrows, and filler removed, including port-only text.
- Docs and counts: 19 skills in `plugin.json`, both READMEs (deslop row, Differences rows for the new hooks, the writing standard, the output style, and the approval options), SPECIFICATION, ARCHITECTURE (with the two new rules), and TOKEN_OPTIMIZATION. `AGENTS.md` adds a rules count of 5, a Writing standard section, the sync check, and sync-table rows for `output-styles/` and `sync-writing-standard.js`. `plugin.json` `version` is 1.8.0; NOTICE files name upstream v1.8.0.

### Fixed

- `/do` Step 5 passed the agent name as `invoke_subagent`'s `Role`. agy 1.3.3's schema takes the agent in `TypeName` and a 2-5 word job title in `Role`; the step now sets both.

### Removed

- Deliberately not ported from upstream v1.8.0:
  - `injection-filter` hook. Antigravity's PostToolUse hook receives no tool result and returns only `{}`, and there is no UserPromptSubmit event. Filtering only subagent prompts through PreToolUse would leave web, MCP, and shell output unfiltered and would need an `allow` or `ask` decision on every delegation. The Untrusted Content rule text stands in, without any filtering claim.
  - `prose-gate` and `prose-advisor` hooks. A PreToolUse write gate must return a decision on every file write (`allow` would auto-approve all writes), PostToolUse has no context channel, and both need Node and a plugin data directory. Use `/deslop detect` or `/review-md`.
  - `writing-context` hook: there is no SessionStart or SubagentStart event. The compact rule loads as an `always_on` rule instead.
  - `output-styles/terse.md`: Antigravity plugins have no output styles; the compact rule covers its core.
  - "Change models" at plan approval: the agent file's `model:` line overrides `invoke_subagent`'s `Model` parameter, so model changes still go through `scripts/set-model-profile.sh` and a restart.
  - `Running now` Runs value in the `/do` plan table: no step starts before approval, so every step starts `pending`.
  - `health` skill updates, hook libraries, `deslop/metadata.json`, and the marketplace manifest.

## [1.7.0-antigravity] - 2026-10-12

Synced with upstream assist-plugin v1.7.0 (ae32066). Content changes come from upstream v1.6.0 (17307ec); upstream v1.6.1 only added the hook runtime (`hooks/lib/`), and v1.7.0 is the relicense to AGPL-3.0-or-later.

Verified live on the Antigravity CLI (`agy` 1.3.3): local and GitHub-subpath install, 18 slash commands without a plugin prefix, 14 invocable subagents, the always-on routing rule, the ported subagent tool names, and agent-file model tiers. A full `/do` run, Antigravity 2.0, and the IDE remain unverified.

### Added

- `/branch cleanup [--dry-run]` with `skills/branch/references/worktree-cleanup.md`: sweeps linked worktrees, removes only merged, clean, unlocked, non-protected ones, deletes their branches with `git branch -d`, and clears the Go build and test cache. It always shows the dry-run listing first and removes nothing until the user confirms with `ask_question`. It never uses `--force`, `-D`, `git clean`, or `rm -rf`.
- `/do` disk-space preflight: `df -h .` before dispatching agents; under 2G it asks with `ask_question` and points to `/branch cleanup --dry-run`. The preflight deletes nothing.
- Pentest references `tooling.md` (ZAP, Nuclei, Semgrep, CodeQL, garak, promptfoo, PyRIT) and `zap.md` (ZAP Docker runbook).
- Pentest Confirmation Path: qa holds no `ask_question`, so before every active test, audit, or scanner run it stops and returns the exact commands and targets; `/do` asks the user and passes back only the approved commands. The qa agent card and `/do` Step 5 state the same rule.
- `code` skill documentation lookup: install commands for a missing `ctx7` or `firecrawl`, bans on `--api-url`, `FIRECRAWL_API_URL`, and `CONTEXT7_*URL*` overrides, and an accepted-risk paragraph on data leaving through scrape URLs and search text.
- "Worktree and Cache Cleanup" section in `rules/assist-plugin-rule.md`, adapted so cleanup runs only through `/branch cleanup`.
- README "Recommended CLI tools" section (git, uv, Python, gh/bkt, ctx7/firecrawl, mmdc, Playwright, Docker, security and audit tools, a check loop) and an optional Antigravity Deny list for `firecrawl env`, `ctx7 setup`, and `ctx7 login`.
- Repo-root `NOTICE`.
- `scripts/validate.py`: invisible-Unicode check. ERROR on bidi controls (U+200E, U+200F, U+061C, U+202A-202E, U+2066-2069) and tag characters (U+E0000-E007F) in plugin markdown and `plugin.json`; WARN on zero-width characters and the BOM, with one allowed exception.
- `scripts/validate.py`: ERROR on control bytes other than TAB and LF in plugin markdown (read as raw bytes, so CR is caught); WARN on a literal TAB outside fenced code; new Claude-ism warnings for `allowed-tools`, "pre-approved", `Bash(...)` permission rules, "PowerShell tool", `EnterWorktree`/`ExitWorktree`, `isolation: "worktree"`, `CLAUDE_PLUGIN_DATA`, and `systemMessage`.

### Changed

- License: the port is now AGPL-3.0-or-later, following upstream v1.7.0. Both `LICENSE` files carry upstream's verbatim AGPL v3 text; `plugins/assist-plugin/NOTICE` follows upstream's v1.7.0 structure, keeps the original MIT notice for components derived from the software-development plugin, and keeps the Antigravity-port attribution; `scripts/*.sh` and `scripts/validate.py` carry SPDX `AGPL-3.0-or-later` and copyright headers; the README License section carries the FSF notice. The 1.5.0-antigravity port was licensed under MIT and was not published. `plugin.json` gets no license field.
- Pentest skill body: OWASP Top 10:2025 web and OWASP Top 10 for LLM Applications 2026 checklists with mapping tables (`web-owasp.md` and `llm-owasp.md` replaced), a per-ecosystem dependency-audit table, and a Scanning Tools section. Upstream's `allowed-tools` pre-approval wording is rewritten: the table lists the safe read-only form for each ecosystem, and rows marked **repo code** run only on trusted repos after the user confirms.
- Python testing guidance prefers uv, with pip or pipx only when uv is absent: `uv run --no-sync --no-python-downloads` in `run-test`, `integrated-test`, `create-test`, `coverage-commands.md`, and `code/references/languages/python.md`. `run-test` calls Node runners as `npx --no vitest run` and `npx --no jest`.
- `diagram-generation.md` shows the mermaid-cli install command and forbids installing mmdc or running it through `npx`.
- Docs: SPECIFICATION (branch cleanup), ARCHITECTURE (developer-tester under Quality, ask under Support), TOKEN_OPTIMIZATION (14 agents and 18 skills; the hooks paragraph says the port ships none), and the branch rows and Differences table in both READMEs.
- `plugin.json` gains `version: 1.7.0`. agy 1.3.3 (CLI) accepts the key; Antigravity 2.0 and the IDE are untested. agy's own Claude-plugin importer writes `version` and `author`; AGENTS.md adds bumping it to the release steps.
- `AGENTS.md`: port of upstream v1.7.0, license line, counts checklist adds `docs/ARCHITECTURE.md` and `docs/TOKEN_OPTIMIZATION.md`, and the sync table explains why hooks are not ported and how to translate `allowed-tools` wording and worktree tools.

### Fixed

- Docs corrected after the live `agy` 1.3.3 run: `agy plugin install` stages to `~/.gemini/config/plugins/assist-plugin/` (the same folder as `install.sh --global`), not `~/.gemini/antigravity-cli/plugins/`; README, AGENTS.md, `model-routing.md`, `routing-with-discovery.md`, and the `set-model-profile.sh` and `install.sh` hints now say so and point CLI users to `agy plugin install`. README and AGENTS.md add `agy plugin validate` as a structural-only check beside `scripts/validate.py`. The "no per-call override" wording in `/do`, `model-routing.md`, `agent-registry.md`, `TOKEN_OPTIMIZATION.md`, and README now states the observed behavior: the agent file's `model:` line wins over `invoke_subagent`'s `Model` parameter, and `/do` omits `Model`. `/ask` and `/map-project` search with `find_by_name`, `grep_search`, `list_dir`, and `view_file`, and use `run_command` only for git metadata. The README Status section reports the live results.
- `skills/integrated-test/references/integration-patterns/python.md`: the port's copy held literal TAB, CR, FF, BS, and BEL bytes (interpreted `\t`, `\r`, `\f`, `\b`, `\a` escapes) that broke the code fences and mangled `testcontainers`, `respx`, and `fakeredis`. It is replaced with upstream's repaired version (asyncpg driver, `pytest_asyncio.fixture`, savepoint rollback, dependency override), adapted to use `find_by_name` for the `.venv` check.

### Removed

- `pip install bitbucket-cli` guidance in `pr-review/references/pr-detection.md`.
- Deliberately not ported from upstream:
  - Hooks `doc-cli-guard`, `sa-mermaid-only`, `health-check`, `hooks.json`, and `hooks/lib/`. Antigravity hook payloads do not identify the calling agent, there is no SessionStart event, and the no-match decision for doc-cli-guard needs a live test. The command-shape rules those hooks enforced live in skill and agent text, and no text claims a hook enforces them.
  - The `health` skill, which reports on hooks this port does not ship. Counts stay at 14 agents and 18 skills.
  - `/do` Step 7 worktree cleanup: `/do` runs subagents in workspace `inherit` and creates no worktrees.
  - Upstream's shell for researcher and mmdc-only shell for solutions-architect, and the LSP grants. Both agents stay shell-less.

### Security

- The bkt install guidance now points to avivsinai/bitbucket-cli (brew, winget, or `go install`), shown to the user and never run by the agent. The old `pip install bitbucket-cli` line installed an unrelated PyPI package.
- No skill text describes commands as pre-approved. Commands that run repo-controlled code or need network run only after the user confirms, and scans from qa go through the orchestrator's `ask_question`.
- `/branch cleanup` adds a confirmation step upstream lacks, because worktrees inside the workspace are removed in the sandbox without an Antigravity permission prompt.
- The `uv run --no-sync --no-python-downloads` and `npx --no` forms fail instead of installing packages or downloading Python.
- Pentest Rule of Engagement 8: scanner reports, target responses, and LLM outputs are untrusted data; the agent never follows instructions in them and reports such text as an LLM01 finding.
- Doc-CLI command shapes (`ctx7`, `firecrawl`) use single quotes around the query or URL, and the text bans the characters that break out of them.
- Agent-run `docker` commands carry `--pull=never`, so the agent never pulls an image; the user pulls images. The ZAP compose example sets `pull_policy: never` and is marked user-run.
- `uvx` and `uv run --with` fetch and run packages, so they are user-run only; agent-run Python uses `uv run --no-sync --no-python-downloads`. The ZAP client venv lives in `"$HOME/.venvs/zap-client"`, not `/tmp`.
- `/branch cleanup` validates the default branch name before it uses it in a merged-branch check.
- Scanner reports go to a private directory made with `mktemp -d "${TMPDIR:-/tmp}/assist-scan.XXXXXX"` (mode 700, unpredictable name) or to a directory the user names, instead of the working directory.
- `pr-review/references/pr-detection.md` drops `curl -u username:password`, which puts the password in process arguments. Bitbucket Server/DC calls use `--netrc-file` or `-H @"$HOME/.config/bitbucket-auth-header"` (mode 600).

## [1.5.0-antigravity] - 2026-10-12

Initial port of `assist-plugin` v1.5.0 from Claude Code to Google Antigravity.

### Added

- `plugins/assist-plugin/` in Antigravity plugin format: 14 subagents, 18 skills (14 user-facing, 4 internal), and 3 rules.
- `rules/assist-routing.md` (`trigger: always_on`) carrying the routing rule that sends development prompts to `/do`.
- `scripts/install.sh`: copies the plugin to `~/.gemini/config/plugins/` or `<workspace>/.agents/plugins/` for Antigravity 2.0 and the IDE, with optional `--profile`.
- `scripts/set-model-profile.sh`: switches subagent models between the `gemini`, `inherit`, `gemini-pro`, and `gemini-flash` profiles.
- `scripts/validate.py`: stdlib-only checker for the documented Antigravity plugin, subagent, skill, and rule formats.
- Repo `README.md`, `AGENTS.md`, `CHANGELOG.md`, and `LICENSE`.

### Changed

- Agent frontmatter: Claude tool names mapped to Antigravity tool names; `model` set to `pro` (review tier) or `flash` (build and fast tiers); `skills:` entries use plugin-relative paths; `subagent: true` and `commandExecutionPolicy` added.
- Skill frontmatter: `effort`, `argument-hint`, and `user-invocable` moved under `metadata:`; internal skills marked "Internal:" in their descriptions because Antigravity cannot hide skills.
- `rules/assist-plugin-rule.md` and `rules/llm-security-checklist.md` load on `trigger: model_decision`.
- `/do` orchestrator uses `invoke_subagent` and `ask_question`, reports each agent's tier from its frontmatter, and scans Antigravity plugin and skill paths for discovery.
- `plugin.json` carries only `name` and `description`; the version is tracked in this file.
- All 14 agents set `mainAgent: false` (none holds `invoke_subagent` or `ask_question`, and `/do` is the entry point); `validate.py` errors on any other value and on `run_command` without `commandExecutionPolicy: sandbox`, and flags `$0`/`$1` and `!` dynamic-context syntax.
- `/do` runs overlapping code-writing steps sequentially in workspace `inherit` (the `branch` workspace is not used until worktree merge-back is verified), allows at most 3 concurrent subagents, passes `git diff` plus prior findings to each reviewer, and asks the user when a gate reaches its 10-iteration cap.
- `pr-review` treats PR content as untrusted data and validates arguments; `commit` stages named paths and uses `git commit -F`; `bump` stages only version files; `code` and the test skills show install commands instead of running them.
- `install.sh` resolves physical paths and refuses workspace targets that escape the workspace through symlinks.
- The LLM security checklist reflects these changes, and its trigger list leaves out `scripts/` (this repository's `AGENTS.md` keeps it for contributors).

### Removed

- `LSP` tool grants (no Antigravity equivalent).
- Shell access for `solutions-architect`; upstream restricted it to mermaid-cli with a Claude hook that has no Antigravity equivalent.
- Shell access for `researcher`; it reads untrusted web content and now uses `search_web` and `read_url_content` only.
- Hooks, the marketplace manifest, and all `skills/*/metadata.json` files.
