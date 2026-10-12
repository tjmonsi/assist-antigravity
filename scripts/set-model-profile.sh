#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Toni-Jan Keith Monserrat
# Switch the model tier of every assist-plugin subagent.
#
# Rewrites only the `model:` line inside each agents/<name>.md YAML frontmatter.
# Body text is never touched. All files are checked before any file is written.
set -euo pipefail

# Agent -> tier table. scripts/validate.py parses these three lines; keep the
# NAME=(...) one-line form and keep them in sync with plugins/assist-plugin/agents/.
REVIEW_TIER=(code-reviewer reviewer researcher solutions-architect)
BUILD_TIER=(ask developer developer-tester devops general-purpose intake-reviewer planner qa requirements-gatherer worker)
FAST_TIER=(explore)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_PLUGIN_DIR="${SCRIPT_DIR}/../plugins/assist-plugin"

usage() {
  cat <<EOF
Usage: $(basename "$0") <gemini|inherit|gemini-pro|gemini-flash> [plugin-dir]

Profiles:
  gemini        review tier -> pro, build tier -> flash, fast tier -> flash (default shipped profile)
  inherit       every subagent uses the model selected in Antigravity (Gemini or Claude)
  gemini-pro    every subagent -> pro
  gemini-flash  every subagent -> flash

Tiers:
  review  ${REVIEW_TIER[*]}
  build   ${BUILD_TIER[*]}
  fast    ${FAST_TIER[*]}

plugin-dir defaults to this repo's plugins/assist-plugin. To change an installed copy, pass its path:
  ~/.gemini/config/plugins/assist-plugin            (global: agy plugin install, or install.sh --global)
  <workspace>/.agents/plugins/assist-plugin         (workspace install)
  ~/.gemini/antigravity-cli/plugins/assist-plugin   (location named in older Antigravity CLI docs)
EOF
}

die() {
  printf 'error: %s\n' "$1" >&2
  exit 1
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage >&2
  exit 2
fi
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
  usage
  exit 0
fi

profile="$1"
plugin_dir="${2:-$DEFAULT_PLUGIN_DIR}"

case "$profile" in
  gemini)       review_model="pro";     build_model="flash";   fast_model="flash" ;;
  inherit)      review_model="inherit"; build_model="inherit"; fast_model="inherit" ;;
  gemini-pro)   review_model="pro";     build_model="pro";     fast_model="pro" ;;
  gemini-flash) review_model="flash";   build_model="flash";   fast_model="flash" ;;
  *) usage >&2; die "unknown profile '${profile}'" ;;
esac

[[ -d "$plugin_dir" ]] || die "plugin directory not found: ${plugin_dir}"
plugin_dir="$(cd "$plugin_dir" && pwd)"
[[ -f "${plugin_dir}/plugin.json" ]] || die "not a plugin directory (missing plugin.json): ${plugin_dir}"
[[ -d "${plugin_dir}/agents" ]] || die "not a plugin directory (missing agents/): ${plugin_dir}"

# Bash 3.2 compatible (macOS default): no associative arrays.
model_for() {
  local agent="$1" a
  for a in "${REVIEW_TIER[@]}"; do [[ "$a" == "$agent" ]] && { printf '%s' "$review_model"; return 0; }; done
  for a in "${BUILD_TIER[@]}"; do [[ "$a" == "$agent" ]] && { printf '%s' "$build_model"; return 0; }; done
  for a in "${FAST_TIER[@]}"; do [[ "$a" == "$agent" ]] && { printf '%s' "$fast_model"; return 0; }; done
  return 1
}

agents=()
while IFS= read -r agent; do
  agents+=("$agent")
done < <(printf '%s\n' "${REVIEW_TIER[@]}" "${BUILD_TIER[@]}" "${FAST_TIER[@]}" | sort)

# Every agent file on disk must be in the tier table, so no agent is silently skipped.
for file in "${plugin_dir}/agents/"*.md; do
  [[ -e "$file" ]] || continue
  agent="$(basename "$file" .md)"
  model_for "$agent" > /dev/null || die "agent '${agent}' is not in the tier table of $(basename "$0")"
done

tmp_files=()
cleanup() {
  local f
  for f in "${tmp_files[@]+"${tmp_files[@]}"}"; do
    rm -f -- "$f"
  done
}
trap cleanup EXIT

# Pass 1: render every rewritten file into a temp file; fail before writing anything.
old_models=()
new_models=()
for i in "${!agents[@]}"; do
  agent="${agents[$i]}"
  file="${plugin_dir}/agents/${agent}.md"
  [[ -f "$file" ]] || die "agent file missing: ${file}"
  new_models[i]="$(model_for "$agent")"
  tmp="$(mktemp "${file}.XXXXXX")"
  tmp_files[i]="$tmp"
  cp -p -- "$file" "$tmp" || die "cannot copy permissions of ${file}"  # mktemp makes mode 600; cp -p keeps the original's mode
  status=0
  awk -v model="${new_models[$i]}" '
    NR == 1 { if ($0 != "---") exit 4; in_fm = 1; print; next }
    in_fm && $0 == "---" { in_fm = 0; if (!done) exit 3; print; next }
    in_fm && !done && /^model:/ { print "model: " model; done = 1; next }
    { print }
    END { if (in_fm) exit 4 }
  ' "$file" > "$tmp" || status=$?
  case "$status" in
    0) ;;
    3) die "no 'model:' line in frontmatter: ${file}" ;;
    4) die "missing or unterminated YAML frontmatter: ${file}" ;;
    *) die "awk failed (${status}) on ${file}" ;;
  esac
  old_models[i]="$(awk 'NR == 1 { next } $0 == "---" { exit } /^model:/ { sub(/^model:[[:space:]]*/, ""); print; exit }' "$file")"
done

# Pass 2: atomically replace each original with its same-directory temp file (mode already copied
# in pass 1). Replacements finish before any output, so a closed stdout pipe (SIGPIPE) cannot
# leave a partial profile.
for i in "${!agents[@]}"; do
  mv -f -- "${tmp_files[$i]}" "${plugin_dir}/agents/${agents[$i]}.md"
done

printf 'Profile: %s\nPlugin:  %s\n' "$profile" "$plugin_dir"
for i in "${!agents[@]}"; do
  printf '  %-22s %-8s -> %s\n' "${agents[$i]}" "${old_models[$i]}" "${new_models[$i]}"
done
printf 'Updated %d agents.\n' "${#agents[@]}"
