---
trigger: always_on
description: "Route actionable development prompts through the assist-plugin /do orchestrator skill; use direct skills for quick queries, git, search, and docs."
---

# assist-plugin Routing

**Invoke the orchestrator:** All actionable development prompts SHOULD be routed through the `/do` skill. The `do` skill classifies the task, matches it to the right agent, creates an execution plan, and coordinates agents with review loops.

**Do NOT invoke `/do`:**
- Quick informational queries ("what is X?", "explain Y")
- Git operations where `/commit` or `/branch` is more direct
- Pure code search (search directly or use `/map-project`; `explore` is a subagent the orchestrator can delegate to, not a slash command)
- Simple documentation requests (use `/technical-writing` directly)

**Default behavior:** If a prompt does not obviously match a specific skill, route to `/do` for classification and delegation.

**Commits and pull requests:** never add a Co-Authored-By trailer or any other AI attribution line (a "Generated with" footer, an AI session link) to a commit message, tag message, or PR body; human co-authors are fine. Full rule: No AI Attribution Rule in `assist-plugin-rule.md`. A project's own disclosure or trailer rule takes precedence.
