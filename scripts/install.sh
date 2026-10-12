#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Toni-Jan Keith Monserrat
# Copy assist-plugin into an Antigravity 2.0 / IDE plugin folder.
# Local copy only: no network access, no sudo.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$(cd "${SCRIPT_DIR}/../plugins/assist-plugin" && pwd)"
PLUGIN_NAME="assist-plugin"

usage() {
  cat <<EOF
Usage: $(basename "$0") [--global | --workspace <dir>] [--profile <gemini|inherit|gemini-pro|gemini-flash>] [--force]

  --global            Copy to \${HOME}/.gemini/config/plugins/${PLUGIN_NAME} (default; Antigravity 2.0 and IDE)
  --workspace <dir>   Copy to <dir>/.agents/plugins/${PLUGIN_NAME}
  --profile <name>    Run set-model-profile.sh on the installed copy
  --force             Replace an existing ${PLUGIN_NAME} install at the target

Antigravity CLI users should prefer agy, which stages to the same folder as
--global (~/.gemini/config/plugins/${PLUGIN_NAME}) and records the install:
  agy plugin install https://github.com/tjmonsi/assist-antigravity/plugins/${PLUGIN_NAME}
  agy plugin install <local-path-to>/plugins/${PLUGIN_NAME}
EOF
}

die() {
  printf 'error: %s\n' "$1" >&2
  exit 1
}

mode="global"
workspace=""
profile=""
force=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --global) mode="global"; shift ;;
    --workspace)
      [[ $# -ge 2 && -n "$2" ]] || die "--workspace needs a directory"
      mode="workspace"; workspace="$2"; shift 2 ;;
    --profile)
      [[ $# -ge 2 && -n "$2" ]] || die "--profile needs a value"
      profile="$2"; shift 2 ;;
    --force) force=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; die "unknown argument '$1'" ;;
  esac
done

case "$profile" in
  ""|gemini|inherit|gemini-pro|gemini-flash) ;;
  *) die "unknown profile '${profile}'" ;;
esac

[[ -f "${SRC_DIR}/plugin.json" ]] || die "source plugin not found: ${SRC_DIR}"

# True when physical path $1 is $2 or lies inside it.
inside() {
  [[ "$1" == "$2" || "$1" == "$2"/* ]]
}

# Resolve the install root (HOME or the workspace) to its physical path first, so symlinks in the
# root itself cannot hide where files land. Every check below runs before any rm or cp.
if [[ "$mode" == "global" ]]; then
  [[ -n "${HOME:-}" && "${HOME}" != "/" ]] || die "HOME is unset or '/'"
  [[ -d "$HOME" ]] || die "HOME is not a directory: ${HOME}"
  root="$(cd "$HOME" && pwd -P)"
  rel=".gemini/config/plugins"
else
  [[ -d "$workspace" ]] || die "workspace directory not found: ${workspace}"
  root="$(cd "$workspace" && pwd -P)"
  rel=".agents/plugins"
fi
[[ "$root" != "/" ]] || die "refusing to install into the filesystem root"

# Workspace mode only: a repository can ship a symlinked .agents, so check the deepest directory that
# already exists on the way to the plugins folder and refuse before mkdir can create anything outside
# the workspace. Global mode skips this check on purpose: users may symlink ~/.gemini to another disk
# or a dotfiles repo, and the path is resolved physically below either way.
if [[ "$mode" == "workspace" ]]; then
  probe="${root}/${rel}"
  while [[ ! -d "$probe" ]]; do
    probe="$(dirname "$probe")"
  done
  inside "$(cd "$probe" && pwd -P)" "$root" \
    || die "${rel} resolves outside ${root}; refusing to install (is .agents a symlink?)"
fi

mkdir -p -- "${root}/${rel}"
parent="$(cd "${root}/${rel}" && pwd -P)"
if [[ "$mode" == "workspace" ]]; then
  inside "$parent" "$root" \
    || die "${rel} resolves to ${parent}, outside ${root}; refusing to install"
fi
target="${parent}/${PLUGIN_NAME}"

# Defensive: the computed target must be a non-root path ending in /plugins/assist-plugin.
[[ "$target" == /*/plugins/"${PLUGIN_NAME}" ]] || die "refusing unexpected target path: ${target}"

if [[ -L "$target" ]]; then
  die "target is a symlink; remove it manually: ${target}"
fi

if [[ -e "$target" ]]; then
  [[ -d "$target" ]] || die "target exists and is not a directory: ${target}"
  if [[ "$(cd "$target" && pwd -P)" == "$(cd "$SRC_DIR" && pwd -P)" ]]; then
    die "target is the source plugin directory: ${target}"
  fi
  if [[ "$force" -ne 1 ]]; then
    die "target already exists (use --force to replace): ${target}"
  fi
  [[ -f "${target}/plugin.json" ]] \
    && grep -Eq '"name"[[:space:]]*:[[:space:]]*"assist-plugin"' "${target}/plugin.json" \
    || die "target exists but is not an ${PLUGIN_NAME} install; not removing: ${target}"
  printf 'Removing existing install: %s\n' "$target"
  rm -rf -- "$target"
fi

cp -R -- "$SRC_DIR" "$target"
printf 'Installed %s -> %s\n' "$PLUGIN_NAME" "$target"

if [[ -n "$profile" ]]; then
  bash "${SCRIPT_DIR}/set-model-profile.sh" "$profile" "$target"
fi

cat <<EOF

If Antigravity is running, restart it so it rescans plugin folders.
Antigravity CLI users should prefer agy, which stages to the same folder as
--global and records the install:
  agy plugin install https://github.com/tjmonsi/assist-antigravity/plugins/${PLUGIN_NAME}
  agy plugin install <local-path-to>/plugins/${PLUGIN_NAME}
EOF
