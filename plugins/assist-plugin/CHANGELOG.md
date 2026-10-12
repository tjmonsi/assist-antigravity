# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.10.0-antigravity] - 2026-10-12

Synced with upstream assist-plugin v1.10.0 (25370a2), with fixes for the defects found in a live agy 1.3.3 test of 1.9.0-antigravity. Not yet verified live: `/voice-script` and `/clarify` loading as slash commands, `ask_question` rendering their menus and a markdown table in the `/do` approval question, the `date` call through `run_command`, and the always-on attribution reminder loading.

### Added

- `/voice-script [topic | draft-file]`: writes a paste-ready text-to-speech script for a chosen TTS model with only that model's own tags and style field, saved to `docs/tts/voice-<slug>-YYYYMMDD-HHmm.md`. It ships 19 dated model reference files and an output template. It uses its built-in catalog (verified 2026-10-12) and fetches OpenRouter's speech-model list with `read_url_content` only when the user asks, reading only each model's id and endpoint path. Menus use `ask_question` with 2 to 4 options and the built-in write-in; a skipped question stops the run.
- `/clarify [what is unclear]`: explains unclear points in the agent's last output with evidence, asks the user about points only the user can settle with `ask_question`, and appends both to `.agent/clarify/clarify-YYYYMMDD.md` with `replace_file_content` on an end marker. It never writes `/do` plan files or `DECISIONS.md`. The plugin now has 21 skills (17 user-facing, 4 internal).
- No AI Attribution Rule in `rules/assist-plugin-rule.md` (commit messages, tag messages, and PR bodies), with the rule in its `description` so it loads when committing, and a one-line always-on reminder in `rules/assist-routing.md` (1,219 bytes; the always-on rules now total 2,723 bytes).
- `scripts/validate.py` Claude-ism warnings for `commit-attribution-guard`, `assist-plugin:health`, `attribution.commit` and `attribution.pr`, `hooks-disabled.json`, `Edit(...)`, `Write(...)`, and `Read(...)` permission rules, and "through Other".
- AGENTS.md sync-table rows for `WebFetch(domain:...)`, `Edit(./path)` rules, the AskUserQuestion "Other" option, Claude Code attribution settings, and "never forks".

### Changed

- `/commit`: "No AI Attribution" covers `*-Session:` trailers and bare AI session links; human co-authors are fine. The message-file check uses a wider `grep` (trailers with leading space, session trailers, and an unanchored "Generated with/by" footer), asks for a read of every printed line, amends with a new message file when a line slipped through, and stops to ask when a line names a person the user asked to credit. The section is renamed "Removing AI Attribution".
- `/bump` and `bump-strategy.md`: the bump commit and the tag message carry no AI attribution.
- `gather-requirements`, `spec-from-requirements`, and `technical-writing` state their write scope as text: the paths each writes, confirmation with `ask_question` (or the approved Writes under `/do`, or `out_of_scope` in a subagent) for any other path, and no claim that anything enforces the list.
- `rules/writing-standard.md` Exemptions: voice scripts keep their text in fenced `text` blocks, so the Code exemption covers em dashes and ellipses used as pause marks.
- worker is described as writing code and tests together; `/do` still runs the review gates after it (`agents/worker.md`, `agent-registry.md`, plugin README).
- Fast-Track Review in `review-protocol.md` and `assist-plugin-rule.md`: `/do` never decides on its own that a change is low-risk. A step skips the Security Gate or the Code Review Gate only when the user asked for that skip in the prompt or an edit and `/do` listed it in the approval question as "Step N skips GATE (you asked)"; the Pre-Test Code Review Gate and the Testing Gate always run for a step that changes code.
- Docs and counts: 21 skills in `plugin.json`, both READMEs (skill rows, Differences rows for commit attribution, document-skill write scope, the voice-script live check, and context-file writes, and `commit-attribution-guard` in the Hooks row), SPECIFICATION (voice-script and clarify sections), ARCHITECTURE, and TOKEN_OPTIMIZATION. `AGENTS.md` names upstream v1.10.0 and adds the attribution guard and the failing-hook reason to the hooks row. `plugin.json` `version` is 1.10.0; NOTICE files name upstream v1.10.0.

### Fixed

- `/do` skipped every review gate on a worker step, ran the tests itself, and wrote gate results no reviewer produced. `review-protocol.md` adds worker and general-purpose to the agents that receive review; `/do` says a producer's own tests or self-review never replace a gate; new Constraints forbid running project code, tests, or builds in the main agent and writing a gate result without the reviewer's terminal block; `plan-format.md` writes each gate line only from the reviewer's `verdict` and never ticks "User approved final result".
- `/do` polled transcripts, set timers, and told the user a denied subagent command was running. A "Subagent command permissions" paragraph gives the one message to show, forbids polling and timers, and keeps the step's `skipped:` markers.
- `/deslop` ran shell commands with the pasted text embedded and searched the home directory to fact-check it. A Hard rule forbids `run_command`, putting the target text in a command or file, and searching files or the web.
- `/deslop` edit dropped a correction ("not the Y the plan described") and cut a list item to its label. `structural-tells.md` keeps a departure from a named plan or earlier statement, and pass 3 reverts a list item cut to its label.
- The `/do` approval question showed no plan table on agy 1.3.3. The full step table and Order line now go at the start of the `ask_question` text.
- The plan file name had no timestamp format, and a same-day rerun overwrote the earlier plan. Plan files are `plan-[slug]-[YYYYMMDD-HHmmss].md` and are never overwritten (`-2`, `-3`).
- `/do` ran a bare `git rev-parse` first and passed `"Model": "inherit"` to `invoke_subagent`. SKILL.md gives the exact first git call and says to leave the `Model` key out entirely.
- `/ask` linked absolute `file://` paths. The visible text is now the relative repo path; the link target may use the host's form.
- README said skills load without a plugin prefix; agy 1.3.3 also accepts and shows `/assist-plugin:<name>`. README also records that agy 1.3.3 neither shows nor waits for a subagent's shell permission request (denied after about 60 seconds), and what to do when `/deslop` ends without a reply.
- `scripts/validate.py` printed nothing and exited 0 when the sync script called `sys.exit()` on import; it now catches `SystemExit` at the load and call sites and reports an ERROR.
- `scripts/validate.py` closed a fence on any fence-like line, so a four-backtick block holding a three-backtick block flipped prose and code. It now tracks the fence character and length (CommonMark).
- `/do` write-path check: a workspace under a folder named `test` put every developer write under a test glob. The test globs now apply to the workspace-relative path.
- `/do` treated a missing `git` command as a generic `git-error`. Ingest has a `git-missing` outcome (Error(tool-missing)); a later git command that reports `git` missing stops the run as a tripped config guard does (Paused).
- `review-protocol.md` said "prefixed excludes", but the prefix is never put into a command; it now says "output filtering".

### Security

- developer, devops, and worker never write `AGENTS.md`, `GEMINI.md`, or `CLAUDE.md` at any depth or a path with a `.agents` segment; a step that needs one lists it in `out_of_scope`. The `/do` write-path check treats such a path as out of bounds for those agents even when the approved Writes list it, judged on the workspace-relative path.
- `/voice-script` fetches nothing unless the user asks; `read_url_content` has no domain limit, so the skill's Fetch scope rule names the only two URL shapes and the endpoint-path pattern, and the reply is untrusted vendor text.
- `llm-security-checklist.md`: LLM01 surfaces for `/voice-script` and `/clarify`, an LLM05 surface and verification item for skills that take pasted text and run no command (`/deslop`), and technical-writing asking before any path other than `README.md`. The file stays under the 24,000-byte limit (23,937 bytes) by tightening the `scripts/` note, the pr-review bullet, the Merge Gate path list (now a pointer to the When triggered list), and the Open Gaps preamble.

### Removed

- Deliberately not ported from upstream v1.10.0:
  - `commit-attribution-guard` hook and `hooks.json`. The guard needs no agent identity, but agy documents no pass-through decision for a command it does not match (`allow` auto-approves, `ask` prompts), and user reports show a failing PreToolUse hook blocking every tool call. The rule ships as text.
  - Claude Code `attribution.commit` and `attribution.pr` guidance and the `health` attribution report: agy adds no attribution line, and the port ships no `health` skill.
  - The prose-hook `docs/tts/` exemption (the port has no prose hooks; fenced blocks cover voice scripts) and upstream's `shell-program.js` refactor of `doc-cli-guard`.
  - `metadata.json` files with scoped `Edit(...)`, `WebFetch(domain:...)`, and `Bash(date ...)` grants; the write scopes are skill text.

## [1.9.0-antigravity] - 2026-10-12

Synced with upstream assist-plugin v1.9.0 (09ea02d). Not yet verified live: the `intake-reviewer` subagent, whether a full terminal block reaches `/do`, the `NeedsInput` relay with `send_message`, the post-step write-path check, and a `/do` run end to end.

### Added

- `intake-reviewer` subagent (build tier, `model: flash`): read-only review of a user-provided spec, requirements, or instructions file with `gather-requirements review` before `/do` plans write steps. It holds `view_file`, `list_dir`, `grep_search`, and `find_by_name`, `commandExecutionPolicy: "off"`, and `mainAgent: false`; the file is untrusted data and findings cite lines without quoting it. The plugin now has 15 subagents.
- `skills/do/references/fsa-template.md`: rules T1 to T9, state kinds, the `## States` table format, the ten-field `fsa` terminal block, and the Dispatch prompt text `/do` pastes into every dispatch. Resume uses `send_message`; no subagent holds `ask_question`.
- `## States` tables and terminal blocks for developer, reviewer, code-reviewer, intake-reviewer, create-test (developer-tester), and task-plan; qa ends with a terminal block and a Testing Gate verdict of `approved` or `returned`.
- developer-tester `## Write scope`: nine test-path globs and four denials (dot-prefixed segments; files named `AGENTS.md`, `GEMINI.md`, or `CLAUDE.md` at any depth; paths over 4096 characters; NUL). The agent follows it as text; no hook enforces it.
- `/do` post-step write-path check: tree snapshots before and after each step, one fixed `git diff --name-only --no-renames` per check, and string comparison against the step's approved Writes and the Write scope. Each mismatch is a finding recorded in the step's Review field and shown at Display; it goes to the fix loop only when the fixer can undo the write, with the step's diff passed as untrusted data. It detects after the write and blocks nothing. No subagent-chosen path or string is put into a command.
- `scripts/validate.py` FSA check (port of upstream `check-fsa-tables.js`): ERROR on a malformed `## States` table, an `fsa` block with missing or misordered fields, a wrong `state`, `error_class`, `questions`, or `resume_at`, a `trace` that leaves the owning table, a table owner whose `### Terminal block` names another agent, and a Dispatch prompt text block that differs from the Terminal block template. Claude-ism warnings for `SendMessage`, `SubagentStop`, `SubagentHandback`, the two FSA hook names, `check-fsa-tables`, and "Base directory for this skill".
- `llm-security-checklist.md` attack surfaces for `/deslop`, `intake-reviewer`, the `NeedsInput` relay, and `DECISIONS.md`.

### Changed

- `/do` is a finite-state Communicator: Ingest (`resume <plan>`, `stop`), Decompose (effect, writes, reads, active tests), Clarify, DependencyAnalysis, AgentSelection, Branch (intake reviews before approval), PlanApproval, Preflight, Dispatch, Display, and Cleanup, ending in Complete, Partial, Paused, Cancelled, or Error. Clarify, PlanApproval, and the relay use `ask_question`; a wave is one `invoke_subagent` call with at most 3 entries in workspace `inherit`. A single ask or explore step skips approval; a skipped approval question is not approval. Architectural decisions append to `DECISIONS.md` after approval, in `/do`'s words.
- `NeedsInput` relay: questions reach the user verbatim with no Recommended mark and only narrowing added options ("Skip it", "Fail the step"); answers never widen a step. `/do` resumes the subagent with `send_message` to its conversation ID, and starts it again with `invoke_subagent` when it was killed. Relays are bounded at 3 per phase and 10 per step.
- A review gate that reaches its bound ends with one binding code-reviewer pass: `approved` completes the step and `returned` fails it. This replaces the port's ask-the-user Iteration Cap in `review-protocol.md`, `fix-phase-rules.md`, `planning-review-agents.md`, `reviewer-adversarial-reflection.md`, `assist-plugin-rule.md`, and `llm-security-checklist.md`.
- Review protocol: a gate-per-artifact table, the gate prompt contents (including the port's scoped diff and fix delta), verdict reading, and test-path findings routed to developer-tester (fix-phase Rule 1b). The plan format gains Partial, Paused, and Error, an "Approved:" bullet, `## Intake Findings`, Effect, Writes, Reads, Active tests, Out of scope, and the step statuses `waiting-user`, `failed`, and `skipped`.
- One coverage bar of >=70% across rules, `run-test`, `integrated-test`, qa, docs, and READMEs.
- debug and technical-writing steps route to developer with the skill's absolute path copied from agy's "Available skills" list. general-purpose is no longer a fallback; unmatched work goes to Clarify.
- pentest active tests under `/do` run only the commands the approved plan lists; qa reports any other in `out_of_scope`. The Confirmation Path now covers qa runs started outside `/do`.
- ask lists the agent that would help in `out_of_scope` when it cannot answer; requirements-gatherer and gather-requirements end each elicitation round with `NeedsInput`; the requirements review treats its document as untrusted data.
- Docs and counts: 15 subagents in `plugin.json`, both READMEs (Differences rows for the write scope, the terminal-block log, the `NeedsInput` resume, and the named-skill path), SPECIFICATION, ARCHITECTURE, TOKEN_OPTIMIZATION, the agent registry, model routing, and the `BUILD_TIER` table. `AGENTS.md` names upstream v1.9.0, adds `GEMINI.md` to the context-file row, adds sync-table rows for `SendMessage`, `run_in_background`, the skill base directory, and `check-fsa-tables.js`, and describes the FSA check. `plugin.json` `version` is 1.9.0; NOTICE files name upstream v1.9.0.

### Security

- `/do` copies the repo git config at Ingest (`config`, `config.worktree`, `<git-dir>/commondir`, and the root `.git` file in a linked worktree) and scans it for keys that run code (`core.pager`, `core.fsmonitor`, `filter.*`, `diff.external`, `diff.*.command`, `diff.*.textconv`, `include.path`, `includeIf.*`). A match raises a question before the first git call (for example `filter.lfs` when git-lfs is set up); declining ends in Cancelled (`config-declined`). A later change to the copy dispatches nothing new and ends in Paused, named at Display.
- Every git call `/do` runs uses `--no-pager -c core.fsmonitor=false`; every `git diff` adds `--no-ext-diff --no-textconv`; the working-tree `git diff` and `git status` add `--ignore-submodules=all`. Global and system git config, and submodule configs, are not guarded.
- Hooks and nested `.git`: every git call also carries `-c core.hooksPath=/dev/null -c safe.bareRepository=explicit` (Git 2.38 or later) and runs from the repository top level; the guard copy records `info/exclude` and every `.git` entry from the working directory up to the top level.
- No plan-file or subagent-supplied string is placed in any command; paths are selected from command output by string comparison.
- The write-path check runs whenever a step settles, not only when a valid block arrives.
- `llm-security-checklist.md` Open Gaps row 15 records the race between the guard comparison and the next git call.

### Fixed

- `scripts/sync-writing-standard.py` wrote files with `Path.write_text(..., newline="")`, which raises `TypeError` on Python 3.9; it now uses `open(..., newline="")`. Both scripts state Python 3.9 as the floor.
- `scripts/sync-writing-standard.py` silently replaced non-bullet text inside a Report Writing Standard block; it now stops with an error naming the file and line.
- `scripts/validate.py` crashed with a traceback when the sync script failed to load or lacked a function; it now reports an ERROR line.
- `rules/writing-standard.md` tells agents not to run the sync script in another project.
- `/do` DependencyAnalysis runs a step that commits, pushes, approves or comments on a PR, or writes `AGENTS.md`, `GEMINI.md`, `.agents/**`, or `DECISIONS.md` alone in its wave, as `llm-security-checklist.md` asks.
- `llm-security-checklist.md` lists `/deslop` as an LLM01 surface, and its `/do` references use state names.

### Removed

- The port's main-agent fallback in `/do` ("handles it directly if no agent matches").
- Deliberately not ported from upstream v1.9.0:
  - `fsa-write-bar` hook. Antigravity hook payloads carry no agent identity, and a PreToolUse hook owes a decision on every write (`allow` auto-approves, `ask` prompts each time). The Write scope text, developer-tester's tool list, and the `/do` write-path check stand in, without a blocking claim.
  - `fsa-log` hook. Antigravity has no SubagentStop event and its PostToolUse hook receives no tool result. `/do` parses every terminal block itself; a direct run outside `/do` gets no log.
  - `scripts/check-fsa-tables.js`. The port has no hook tables to compare; `validate.py` checks the markdown instead.
  - The `health` skill's FSA self-tests (the port ships no `health` skill and no hooks).
  - "Change models" at plan approval. The agent file's `model:` line overrides `invoke_subagent`'s `Model` parameter on agy 1.3.3, so a model change goes through `scripts/set-model-profile.sh` and a restart.
  - The worktree part of the Cleanup state and the worktree-cleanup "Cleanup state" wording. `/do` creates no worktrees; Cleanup only chooses the terminal.
  - "Permission prompts remain the backstop" in pentest Rule of Engagement 3: a subagent's approval request may be denied rather than prompted, and Turbo asks nothing.
  - `.claude-plugin/marketplace.json`, `MARKETPLACE.md`, and upstream's `.gitignore` change (the port already ignores the `.agent` subfolders it uses).

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

> Upstream history: the six entries below ([1.10.0], [1.9.0], [1.8.0], [1.7.0], [1.6.1], [1.6.0]) are copied unchanged from upstream assist-plugin `CHANGELOG.md` ([1.10.0] at 25370a2, [1.9.0] at 09ea02d, [1.8.0] at 442d34e, the others at ae32066) and describe the Claude Code plugin. The 1.10.0-antigravity, 1.9.0-antigravity, 1.8.0-antigravity, and 1.7.0-antigravity entries above record what this port took from them.

## [1.10.0] - 2026-10-12

### New Features

- **New user-invocable `voice-script` skill**: `/voice-script [topic | draft-file]` writes a paste-ready text-to-speech script for a chosen TTS model
  - Asks for the model, voice, length, delivery, and a topic or draft, then saves `docs/tts/voice-<slug>-YYYYMMDD-HHmm.md` with that model's own paralinguistic tags
  - Catalog of Chatterbox-Turbo, 32 OpenRouter speech models, and OpenAI gpt-audio and gpt-audio-mini, with a live OpenRouter check
- **New user-invocable `clarify` skill**: `/clarify [what is unclear]` turns unclear points in the current discussion into explanations and settled answers
  - Explains Claude's own unclear output with evidence, then asks the user about points only the user can settle through `AskUserQuestion`
  - Appends each clarification to `.agent/clarify/clarify-YYYYMMDD.md`, a daily append-only log; never writes `/do` plan files or `DECISIONS.md`
  - The plugin now has 22 skills (18 user-invocable)
- **`commit-attribution-guard` hook**: PreToolUse on `Bash` and `PowerShell` denies a `git commit`, `git merge`, `gh pr create`, or `gh pr edit` command whose commit message or PR body holds AI attribution
  - Denies a Co-Authored-By trailer that names an AI tool or vendor (human co-authors pass), a "Generated with/by" footer, an Assisted-by or Generated-by trailer naming an AI tool, and a `*-Session:` trailer or bare session link at an AI host
  - Reads `-m`, `--message`, `-F`, `--file`, `--trailer`, `--body`, `-b`, `--body-file`, chained commands, heredocs, and PowerShell; does not cover `git tag` or a message built from a variable or stdin
  - Lists up to 5 lines to remove, never rewrites the command, and fails open
- **Health check reports Claude Code's attribution setting**: `/assist-plugin:health` runs the new guard's self-test and reports, read-only, when `attribution.commit` or `attribution.pr` is unset or not `""` in the user, project, or local settings file; the README shows the snippet `{"attribution": {"commit": "", "pr": ""}}`

### Changes

- `prose-gate` and `prose-advisor` skip files under `docs/tts/` in the hook's working directory (not the git root), so voice scripts may use em dashes as pause marks
- The `health` skill now lists `docs/tts/` among the paths the prose hooks skip
- The `commit` and `bump` skills and `rules/assist-plugin-rule.md` state the no-AI-attribution rule: no Co-Authored-By trailer or other attribution line for an AI tool in a commit message or PR body; human co-authors are fine
- The `gather-requirements`, `technical-writing`, and `spec-from-requirements` skills pre-approve writes only to their documented output paths through scoped `Edit(...)` rules in `allowed-tools`, replacing plain `Write` and `Edit`; a write to any other path now asks the user first
  - `gather-requirements`: `./BRD-*.md`, `./URD-*.md`, `./FR-NFR-*.md`, `./requirements-*.json`
  - `spec-from-requirements`: `./specs/spec-*.md`, `./specs/spec-*.json`, `./specs/openapi/*.json`, `./specs/openapi/*.yaml`, `./*/specs/spec-*.md`, `./*/specs/spec-*.json`
  - `technical-writing`: `./README.md` only

## [1.9.0] - 2026-10-12

### New Features

- **/do as a deterministic Communicator state machine**: Ingest, Decompose (structured steps with effect, writes, reads), Clarify, DependencyAnalysis (no shared writes in a wave), AgentSelection, Branch, PlanApproval, Preflight, Dispatch, Display, Cleanup; terminals Complete, Partial, Paused, Cancelled, Error
  - Approval is skipped only for a single ask or explore step; unmatched work goes to Clarify; a failed step skips only its dependents; stop and resume go back through approval
  - Every dispatch carries a 10-field fsa terminal block; relayed questions are verbatim and never widen an approved step; out-of-scope items become new requests
  - Read-only intake review of user-provided spec files before approval; architectural decisions append to `DECISIONS.md` after approval
- **FSA state tables and terminal blocks** for developer-tester, reviewer, code-reviewer, developer, task-plan, and create-test; qa reports an approved or returned Testing Gate verdict
- **New agent `intake-reviewer`** (Read, Grep, Glob only) that reviews user files as untrusted data
- **FSA hooks**: `fsa-write-bar` (developer-tester writes only test paths, never dot folders, `CLAUDE.md`, or `AGENTS.md`; developer never writes test paths) and `fsa-log` (records parsed terminal blocks without message text and warns on illegal traces); `scripts/check-fsa-tables.js` keeps hook tables in sync with the markdown

### Changes

- One coverage bar of >=70% everywhere
- debug and technical-writing tasks route to developer through a named-skill intake; general-purpose is no longer a fallback
- pentest active tests under /do run only commands listed in the approved plan
- Counts: 15 agents, 20 skills

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

