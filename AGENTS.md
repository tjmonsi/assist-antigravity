# AGENTS.md

Guidance for agents and contributors working in this repo.

## Repo identity

- **Repo:** `tjmonsi/assist-antigravity`
- **Plugin:** `plugins/assist-plugin` (Antigravity plugin name `assist-plugin`, port of upstream v1.7.0)
- **Upstream:** [`tjmonsi/assist-marketplace-plugin`](https://github.com/tjmonsi/assist-marketplace-plugin), the Claude Code version; local checkout expected at `../assist-marketplace-plugin`
- **Install:** `agy plugin install https://github.com/tjmonsi/assist-antigravity/plugins/assist-plugin` (stages to `~/.gemini/config/plugins/assist-plugin/` on `agy` 1.3.3, the same folder `scripts/install.sh --global` writes; CLI users use `agy plugin install`, Antigravity 2.0 and IDE users use `install.sh`)
- **License:** AGPL-3.0-or-later ([LICENSE](LICENSE), [NOTICE](NOTICE)). The 1.5.0-antigravity port was licensed under MIT and was not published; from 1.7.0-antigravity the port is licensed under AGPL-3.0-or-later. New scripts start with `# SPDX-License-Identifier: AGPL-3.0-or-later` and `# Copyright (C) 2026 Toni-Jan Keith Monserrat` after the shebang; markdown files carry no SPDX header

Do not rename the plugin folder or the `name` in `plugin.json`. The install URL, `scripts/install.sh`, and users' installed copies all depend on `assist-plugin`.

`plugin.json` carries `name`, `version`, and `description`. The `version` key is accepted by agy 1.3.3 (CLI); Antigravity 2.0 and the IDE are untested. agy's own Claude-plugin importer (`agy plugin import`) writes `version` and `author` into the `plugin.json` it generates. Record each release in the root [CHANGELOG.md](CHANGELOG.md) and bump `version` in `plugin.json` to match.

## Layout

```text
plugins/assist-plugin/
├── plugin.json          # {"name", "version", "description"}
├── agents/<name>.md     # 14 subagents
├── skills/<name>/       # 18 skills: SKILL.md + optional references/
├── rules/*.md           # every rule needs `trigger` frontmatter, under 24,000 bytes
└── docs/                # SPECIFICATION, ARCHITECTURE, standards
scripts/
├── validate.py          # static format checker (stdlib only)
├── set-model-profile.sh # agent -> tier table and profile switcher
└── install.sh           # folder-copy installer for Antigravity 2.0 / IDE
```

## Adding or removing an agent

1. Create `plugins/assist-plugin/agents/<name>.md`. The filename must match `name`.

   ```yaml
   ---
   name: <name>
   description: "<one sentence the router can match on>"
   model: flash            # inherit | flash | pro
   tools:
     - view_file
     - list_dir
     - grep_search
     - find_by_name
   skills:                 # optional; paths relative to the plugin root
     - skills/<skill-name>
   mainAgent: false        # must be false (see note below); validate.py rejects anything else
   subagent: true
   commandExecutionPolicy: "off"   # quote "off" (bare off is a YAML boolean); use sandbox if tools include run_command
   ---
   ```

   `mainAgent` means "selectable as the primary agent in chat" (antigravity.google/docs/subagents/); `subagent` means invocable through `invoke_subagent`. Every agent here sets `mainAgent: false`: none holds `invoke_subagent` or `ask_question`, and the always-on routing rule sends prompts to `/do`, which needs both. Keep `subagent: true` so `/do` can start the agent.

2. Use exact Antigravity tool names. A wrong name can hang the subagent. `validate.py` accepts only: `view_file`, `write_to_file`, `replace_file_content`, `multi_replace_file_content`, `list_dir`, `find_by_name`, `grep_search`, `search_web`, `read_url_content`, `run_command`, `manage_task`, `schedule`, `list_permissions`, `ask_permission`, `invoke_subagent`, `define_subagent`, `send_message`, `manage_subagents`, `ask_question`, `generate_image`.
3. Grant the fewest tools the role needs. Review agents stay read-only. Granting `run_command` requires `commandExecutionPolicy: sandbox`; `validate.py` rejects `run_command` with any other policy.
4. Add the agent to exactly one tier array in `scripts/set-model-profile.sh` (`REVIEW_TIER`, `BUILD_TIER`, or `FAST_TIER`). Keep each array on one line; `validate.py` parses them. The script refuses to run if any agent file is missing from the table.
5. Set `model:` to the value the shipped `gemini` profile gives that tier: `pro` for review, `flash` for build and fast.
6. Update every file in the counts checklist below.

To remove an agent, delete its file, remove it from the tier table, remove its routing entry from `skills/do/references/agent-registry.md`, and update the counts checklist.

## Adding or removing a skill

1. Create `plugins/assist-plugin/skills/<name>/SKILL.md` with `name` and `description`. Put `effort`, `argument-hint`, and `user-invocable` under `metadata:`. Do not use `allowed-tools`, `disable-model-invocation`, or a `metadata.json` file; `validate.py` rejects them.
2. For user-invocable skills, show the command with either a `Usage: /<name> <arguments>` line or a Quick Start/examples block in the body. Internal skills need neither. Refer to user input as "the text after the slash command"; Antigravity documents no `$ARGUMENTS` placeholder.
3. Internal skills cannot be hidden. Start the description with `Internal: preloaded by the <agent> agent.` and list the skill in that agent's `skills:` frontmatter.
4. Keep relative links in `references/` resolvable; `validate.py` checks them.
5. Update every file in the counts checklist below.

Ship skills only. Antigravity retires workflows on 2026-10-19.

## Keeping counts in sync

When an agent or skill is added, removed, or renamed, update the counts and lists in:

- [ ] `plugins/assist-plugin/plugin.json` (description)
- [ ] `README.md` (skill table, agent table, layout tree)
- [ ] `AGENTS.md` (layout tree)
- [ ] `plugins/assist-plugin/README.md`
- [ ] `plugins/assist-plugin/docs/SPECIFICATION.md`
- [ ] `plugins/assist-plugin/docs/ARCHITECTURE.md` (layout tree and agent tiers)
- [ ] `plugins/assist-plugin/docs/TOKEN_OPTIMIZATION.md` (agent and skill lists, scope comparison table)
- [ ] `plugins/assist-plugin/skills/do/references/agent-registry.md`
- [ ] `scripts/set-model-profile.sh` tier table (agents only)

## Before committing

Run the validator and fix every `ERROR`:

```bash
python3 scripts/validate.py
```

If the `agy` CLI is installed, also run Antigravity's structural check:

```bash
agy plugin validate plugins/assist-plugin
```

`agy plugin validate` checks structure only. In tests it accepted wrong tool names, `model: sonnet`, invalid rule triggers, and skills with no description, so `scripts/validate.py` stays the required gate.

If you touched `set-model-profile.sh`, round-trip it and confirm the agents return to their original state:

```bash
./scripts/set-model-profile.sh inherit
./scripts/set-model-profile.sh gemini
git diff --stat plugins/assist-plugin/agents/
```

## LLM security gate

Agent, skill, and rule markdown is executable instruction handed to a model with tool access. Changes to any of these paths require a `reviewer` or `code-reviewer` pass against [`rules/llm-security-checklist.md`](plugins/assist-plugin/rules/llm-security-checklist.md), ending in `✓ LLM Security Clear`, before merge:

- `plugins/assist-plugin/agents/`
- `plugins/assist-plugin/skills/` (including `references/`)
- `plugins/assist-plugin/rules/`
- `AGENTS.md`
- `plugins/assist-plugin/plugin.json`
- `hooks.json` and `mcp_config.json` (none ship today; any addition is in scope)
- `scripts/` (contributor scope for this repository only; the plugin rules' trigger list in `rules/llm-security-checklist.md` omits `scripts/` because those rules load in users' projects)

Pay particular attention to new tool grants, `commandExecutionPolicy` changes, skills that pass fetched web or PR content into state-changing steps, and anything in `install.sh` that writes outside the target plugin folder.

## Syncing from upstream

There is no automated sync. To port an upstream change:

1. Diff the upstream release in `../assist-marketplace-plugin/plugins/assist-plugin` against the version recorded in [CHANGELOG.md](CHANGELOG.md).
2. Port each change by hand, applying these conversions:

   | Upstream (Claude Code) | This repo (Antigravity) |
   |---|---|
   | `model: opus` / `sonnet` / `haiku` | `pro` / `flash` / `flash`, plus a tier-table entry |
   | `Read` | `view_file`, `list_dir` |
   | `Write` | `write_to_file` |
   | `Edit` | `replace_file_content`, `multi_replace_file_content` |
   | `Grep` / `Glob` | `grep_search` / `find_by_name` |
   | `Bash`, `PowerShell` | `run_command` with `commandExecutionPolicy: sandbox` |
   | `WebSearch` / `WebFetch` | `search_web` / `read_url_content` |
   | `Agent` tool | `invoke_subagent` |
   | `AskUserQuestion` | `ask_question` |
   | `LSP` | drop (no equivalent) |
   | `skills: [code]` | `skills: [skills/code]` |
   | `type`, `effort` in agent frontmatter | drop (note effort in the body) |
   | `CLAUDE.md`, `.claude/settings*.json` | `AGENTS.md`, `plugin.json`, `hooks.json`, `mcp_config.json`, `.agents/**` |
   | `skills/*/metadata.json` | delete |
   | hooks (`hooks/*.js`, `hooks/hooks.json`) | no port: Antigravity hook payloads do not identify the calling agent, there is no plugin-root variable or SessionStart event, and the effect of a no-match result is undocumented. Restrict the agent's tools and put the command-shape rules in skill text instead, without claiming a hook enforces them |
   | `allowed-tools` pre-approval, "pre-approved", "prompts" | no pre-approval; write "safe read-only form" for read-only commands and "run only after the user confirms" for anything that runs repo-controlled code or needs network |
   | `EnterWorktree` / `ExitWorktree`, `isolation: "worktree"` | drop; `/do` uses workspace `inherit` and creates no worktrees |

3. Run `python3 scripts/validate.py`. Treat `WARN ... Claude-isms remaining` as a to-do list.
4. Add a CHANGELOG entry naming the upstream version you synced to.
5. Bump `version` in `plugins/assist-plugin/plugin.json` to the release number (without the `-antigravity` suffix).
