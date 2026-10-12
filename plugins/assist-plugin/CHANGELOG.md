# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

> Upstream history: the four entries below ([1.8.0], [1.7.0], [1.6.1], [1.6.0]) are copied unchanged from upstream assist-plugin `CHANGELOG.md` ([1.8.0] at 442d34e, the others at ae32066) and describe the Claude Code plugin. The 1.8.0-antigravity and 1.7.0-antigravity entries above record what this port took from them.

## [1.8.0] - 2026-10-12

### New Features

- **Injection filter hook** (`hooks/injection-filter.js`): a deterministic, fail-open filter for prompt-injection text in untrusted content
  - PostToolUse on `WebFetch`, `WebSearch`, `mcp__*` tools, `Agent` results, and Bash `firecrawl`/`curl`/`wget`/`ctx7`: matching sentences are replaced with a visible marker, invisible Unicode is stripped, and the result is returned in its original shape with a factual note listing rule ids
  - PreToolUse on `Agent`: a matching subagent prompt is rewritten and returned with an `ask` decision; UserPromptSubmit only warns (the typed prompt is never changed or blocked)
  - Eight rule families (instruction override, role reassignment, system-prompt or secret exfiltration, fake chat delimiters, hidden-instruction carriers, tool hijack, data-exfiltration links, concealment); plugin files and sources in `injection-allowlist.json` are skipped
  - `lib/health.js` gains `transform()` (fail-open runtime for filter hooks); the health check self-tests the filter with a known-injection and known-benign corpus and disables it if a benign sample is altered or an injection sample is missed
- **Writing standard and de-slop layer**: one source of truth for how the plugin writes, with hooks, a skill, and a style that apply it
  - `rules/writing-standard.md` holds every rule with its reason and examples; `rules/writing-standard-compact.md` holds the always-on bullets; `scripts/sync-writing-standard.js` rewrites every `## Report Writing Standard` block in `agents/` and `skills/` from the compact file (`--check` exits 1 on drift)
  - `prose-gate` (PreToolUse on `Write`, `Edit`, `MultiEdit`, `NotebookEdit`) denies a prose write only when the text it adds holds a block-tier tell: em dash, chatbot residue, curly quote, or summary-label phrase. Text already in the file is not judged
    - The prose hooks skip files under the system temp directory and any path listed in `prose-gate-allowlist.json` in the plugin data directory (the entry `"*"` disables the gate for all paths). The deny reason names the standard by absolute path and says how to keep verbatim text
  - `prose-advisor` (PostToolUse on the same tools) adds a short advisory note for hedges, intensifiers, AI vocabulary, throat-clearing, binary contrast, en dashes, and prose arrows. It never blocks
  - `writing-context` (SessionStart and SubagentStart) injects the compact standard (about 1,195 characters, about 300 tokens) into the session and into each subagent
  - `hooks/lib/prose-rules.js` is the tell catalog and `hooks/lib/prose-diff.js` finds the added text; all three hooks fail open, only `prose-gate` and `prose-advisor` are self-tested by the health check, and the per-write hooks add about 80 to 110 ms per write
  - Opt-in `assist-plugin:terse` output style (`output-styles/terse.md`): answer first, no preamble, recap, or sign-off. Subagents do not use it
  - New user-invocable `deslop` skill: `/deslop [edit | detect] <file-or-text>` removes AI writing tells from prose; `edit` returns cleaned text and `detect` lists findings. The plugin now has 20 skills (16 user-invocable)
  - New `code` reference `code-slop.md` and a stricter TypeScript rule: `unknown` only at trust boundaries, narrowed immediately; concrete types inside the codebase
  - Review output rules in `do/references/review-protocol.md`, `agents/reviewer.md`, `agents/code-reviewer.md`, and `skills/pr-review`: terse, three-part findings
  - De-slop pass over the plugin's agents, skills, rules, docs, and READMEs: em dashes, curly quotes, prose arrows, and filler words removed

## [1.7.0] - 2026-10-12

### License

- Relicense the marketplace and assist-plugin from MIT to the GNU Affero General Public License v3.0 or later (`AGPL-3.0-or-later`): both LICENSE files carry the verbatim AGPL v3 text, manifests use the SPDX identifier, hook sources carry SPDX headers, and NOTICE keeps the original MIT notice for derived components. Releases up to and including v1.6.1 remain available under MIT.

## [1.6.1] - 2026-10-12

### Bug Fixes

- Ship `plugins/assist-plugin/hooks/lib/` (`launch.js`, `health.js`). The root `.gitignore` rule `lib/` excluded them from v1.6.0, so installed guards failed open with a launch-error warning on every Bash call; the rule is now anchored to the repo root (`/lib/`).

## [1.6.0] - 2026-10-12

### New Features

- **Fail-open guard hooks and health reporting**
  - Add PreToolUse guards: `sa-mermaid-only` (solutions-architect may run only mermaid-cli with allowlisted flags and relative paths) and `doc-cli-guard` (blocks firecrawl/ctx7 output, endpoint, and shell-operator forms)
  - Guards deny only on a positive match; crashes, unsupported Node (below 6), timeouts, and disabled guards let the command run with a `systemMessage` warning and never exit 2
  - Add SessionStart self-test (silent when healthy; auto-disables a guard that blocks known-safe commands) and `health` skill (`/assist-plugin:health [--clear]`)
- **Worktree and cache cleanup**
  - Add `/branch cleanup [--dry-run]`: removes only merged, clean, unlocked, non-protected worktrees; never `--force` or `-D`; clears the Go build and test cache
  - `/do` runs targeted cleanup for worktrees its own steps created and checks free disk space (asks under 2G) before dispatching agents
- **Pentest references**
  - Web checklist moves to OWASP Top 10:2025 and LLM checklist to the 2026 OWASP LLM Top 10, with mapping tables
  - Dependency-audit table for every ecosystem with read-only commands and mutating flags to avoid
  - Add `tooling.md` (ZAP, Nuclei, Semgrep, CodeQL, garak, promptfoo, PyRIT) and `zap.md` (Docker runbook)

### Changes

- Agents preload dependent skills via `skills:`; internal skills drop `disable-model-invocation`
- researcher gains WebSearch/WebFetch; solutions-architect gains mmdc-only Bash; developer, qa, reviewer, code-reviewer gain LSP; Tools lines match frontmatter
- researcher and solutions-architect route as Opus; planner documented as Sonnet
- Pre-approved commands narrowed to exact forms; anything that runs repo code or installs software prompts; `npx --no` everywhere
- Python guidance prefers uv with pip/pipx fallback; garak and PyRIT documented as global tools and per-repo dev dependencies

### Documentation

- GitHub URLs use `tjmonsi/assist-marketplace-plugin`; root `Claude.md` renamed to `CLAUDE.md` and rewritten
- README adds Recommended CLI Tools, hook health, and corrected installs (bkt from avivsinai/bitbucket-cli, ZAP via Docker)
- Counts updated to 14 agents and 19 skills (15 user-invocable)

## [1.5.0-antigravity] - 2026-10-12

Port of assist-plugin v1.5.0 from [assist-marketplace-plugin](https://github.com/tjmonsi/assist-marketplace-plugin) (Claude Code) to Google Antigravity. Entries below this one record upstream history.

### Changed
- Manifest: `.claude-plugin/plugin.json` replaced by a root `plugin.json` carrying only `name` and `description`; the version lives in this changelog
- Subagent frontmatter: `type` and `effort` dropped (effort moved to each agent body); `subagent: true`, `mainAgent: false`, and `commandExecutionPolicy` added (`sandbox` for agents with `run_command`, `off` otherwise); `skills` entries use `skills/<name>` paths
- Tool names mapped to Antigravity tools: `view_file`, `list_dir`, `write_to_file`, `replace_file_content`, `multi_replace_file_content`, `grep_search`, `find_by_name`, `run_command`, `search_web`, `read_url_content`, `invoke_subagent`, `ask_question`
- Model routing: the upstream three-model routing became three tiers with a shipped `gemini` profile (review tier `pro`, build and fast tiers `flash`); `scripts/set-model-profile.sh` switches to `inherit`, `gemini-pro`, or `gemini-flash`. The orchestrator runs on the model selected in Antigravity's model selector
- Fix phase: runs on the build tier, never the review tier
- Orchestrator: `ask_question` for approval, `invoke_subagent` for delegation (workspace `inherit` only; overlapping code writes run sequentially and the `branch` workspace is not used until worktree merge-back is verified), at most 3 concurrent subagents for non-overlapping or read-only steps, the orchestrator passes `git diff` and prior findings to every review, and a gate that hits its iteration cap stops and asks the user; Antigravity plugin, skill, and subagent discovery paths
- Rules: `trigger` frontmatter added; new always-on `rules/assist-routing.md`; LLM Security gate trigger list covers `AGENTS.md`/`GEMINI.md`, `plugin.json`, `hooks.json`, and `mcp_config.json` (no `scripts/*.sh`: the rules load in users' projects; the repository's root `AGENTS.md` keeps `scripts/` for contributors)
- Skills: `effort`, `argument-hint`, and `user-invocable` moved under `metadata`; `allowed-tools` dropped; internal skills marked in their descriptions
- Plugin quick reference `Claude.md` replaced by `README.md`
- Skills: `pr-review` treats PR content as untrusted data and validates PR numbers and branch names; `commit` stages named paths and commits with `git commit -F`; `bump` stages only version files and `CHANGELOG.md`; `code` and the test skills show install commands instead of running them; `$0`/`$1` placeholders and the `!` dynamic-context block are replaced with plain instructions

### Removed
- `run_command` from solutions-architect: upstream limited its shell to mermaid-cli with a Claude Code hook that has no Antigravity equivalent; the agent now writes Mermaid source and leaves PNG rendering to the user or devops
- `run_command` from researcher: it reads untrusted web content, so it uses `search_web` and `read_url_content` only and tells the user the firecrawl command when needed
- LSP tool grants (no Antigravity equivalent)
- `skills/*/metadata.json` files

## [1.3.0] - 2026-09-14

### Added
- Ask skill: answer questions using repo search and optional web research
- Router plugin discovery: runtime detection and suggestions to subagents
- Fix-phase protocol: Sonnet-only, scope-constrained iteration for reviewer-identified fixes
- Documentation standard: comprehensive AI-slop removal checklist, conciseness rules, token cost awareness

### Changed
- Planner agent: default model Opus → Sonnet (cost optimization via iteration strategy)
- Commit skill: default model → Haiku (cheapest tier, mechanical formatting only)
- Review protocol: unified fix-phase workflow with hard scope constraints
- Ask agent added to routing (question-answering intent check before agent-registry table)

### Fixed
- Code review blocker resolutions (6 critical/major issues)
- LLM co-authorship removal from commit messages (no Claude/Anthropic attribution in git footers)
- Em-dash contradiction in ask answer-format template (changed to colon separator)
- Conflicting revision workflow removed (single iteration path per fix-phase-rules)

## [1.2.0] - 2024-08-27

### Added
- Version bump infrastructure (commit tracking)

---

## [1.1.0]

Earlier releases. See git history.

