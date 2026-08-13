#!/usr/bin/env bash
set -euo pipefail
[[ $# -eq 2 ]] || { echo "usage: $0 TASK DESTINATION" >&2; exit 2; }
task="$1"
dest="$2"
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -e "$dest" ]] && [[ -n "$(find "$dest" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  echo "refusing non-empty destination: $dest" >&2
  exit 1
fi
mkdir -p "$dest"
case "$task" in
  exact_contract) printf 'evaluation workspace\n' > "$dest/.workspace-marker" ;;
  code_scope) cp -a "$repo_dir/fixtures/calculator"/. "$dest"/ ;;
  long_context) cp -a "$repo_dir/fixtures/long-context"/. "$dest"/ ;;
  tool_sequence) cp -a "$repo_dir/fixtures/tool-sequence"/. "$dest"/ ;;
  *) echo "unknown task $task" >&2; exit 2 ;;
esac
if [[ -n "$(find "$dest" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
  git init -q "$dest"
  git -C "$dest" config user.name eval-flash
  git -C "$dest" config user.email eval-flash@localhost
  git -C "$dest" add -A
  git -C "$dest" commit -qm baseline
fi
