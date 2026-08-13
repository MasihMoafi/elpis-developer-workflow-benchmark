#!/usr/bin/env bash
set -euo pipefail
[[ $# -eq 2 ]] || { echo "usage: $0 TASK REP" >&2; exit 2; }
task="$1"
rep="$2"
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
run_id="${task}__r$(printf '%02d' "$rep")"
run_dir="$repo_dir/results/runs/$run_id"
workspace="$run_dir/workspace"
[[ ! -e "$run_dir" ]] || { echo "run already exists: $run_dir (choose a new repetition; raw runs are immutable)" >&2; exit 1; }
prompt_rel="$(jq -r --arg task "$task" '.tasks[] | select(.id == $task) | .prompt' "$repo_dir/tasks.json")"
fixture_rel="$(jq -r --arg task "$task" '.tasks[] | select(.id == $task) | .fixture // empty' "$repo_dir/tasks.json")"
sandbox="$(jq -r --arg task "$task" '.tasks[] | select(.id == $task) | .sandbox' "$repo_dir/tasks.json")"
[[ -n "$prompt_rel" && "$prompt_rel" != null ]] || { echo "unknown task: $task" >&2; exit 2; }
prompt="$repo_dir/$prompt_rel"
[[ -f "$prompt" ]] || { echo "missing prompt: $prompt" >&2; exit 1; }
elpis_bin="${ELPIS_BIN:-elpis}"
provider="${ELPIS_PROVIDER:-openrouter}"
model="${ELPIS_MODEL:-inclusionai/ling-3.0-flash}"
timeout="${ELPIS_TIMEOUT:-60}"
[[ -x "$elpis_bin" ]] || { echo "Elpis binary is not executable: $elpis_bin (set ELPIS_BIN to a valid binary)" >&2; exit 1; }
mkdir -p "$run_dir"
"$repo_dir/scripts/prepare_workspace.sh" "$task" "$workspace"
started="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
transcript="$run_dir/transcript.txt"
stop_file="$run_dir/stop"
set +e
(
  export HTTP_PROXY=http://127.0.0.1:10808
  export HTTPS_PROXY=http://127.0.0.1:10808
  export ALL_PROXY=http://127.0.0.1:10808
  export http_proxy=http://127.0.0.1:10808
  export https_proxy=http://127.0.0.1:10808
  export all_proxy=http://127.0.0.1:10808
  export TERM=xterm-256color
  python "$repo_dir/scripts/pty_run.py" "$workspace" "$transcript" "$prompt" "$sandbox" --timeout "$timeout" --stop-file "$stop_file" >"$run_dir/runner.log" 2>&1 &
  pty_pid=$!
  completion_status=timeout
  while kill -0 "$pty_pid" 2>/dev/null; do
    if "$repo_dir/scripts/score.sh" "$task" "$workspace" "$transcript" >"$run_dir/score.json" 2>/dev/null; then
      completion_status=pass
      touch "$stop_file"
      break
    fi
    if [[ -f "$transcript" ]] && rg -a -q 'Stream disconnected before completion|unexpected status [0-9]+|provider returned error' "$transcript"; then
      completion_status=provider_error
      touch "$stop_file"
      break
    fi
    sleep 0.25
  done
  wait "$pty_pid"
  process_status=$?
  if [[ "$completion_status" == timeout ]]; then
    if "$repo_dir/scripts/score.sh" "$task" "$workspace" "$transcript" >"$run_dir/score.json" 2>/dev/null; then
      completion_status=pass
    elif [[ -f "$transcript" ]] && rg -a -q 'Stream disconnected before completion|unexpected status [0-9]+|provider returned error' "$transcript"; then
      completion_status=provider_error
    elif [[ "$process_status" -eq 124 ]]; then
      completion_status=timeout
    else
      completion_status=process_exit
    fi
  fi
  printf '%s\n' "$completion_status" > "$run_dir/completion_status"
  printf '%s\n' "$process_status" > "$run_dir/process_status"
)
subshell_status=$?
set -e
finished="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
if [[ -n "$fixture_rel" ]]; then
  fixture_hash="$(find "$repo_dir/$fixture_rel" -type f -not -path '*/__pycache__/*' -print0 | sort -z | xargs -0 sha256sum | sha256sum | cut -d' ' -f1)"
else
  fixture_hash=""
fi
prompt_hash="$(sha256sum "$prompt" | cut -d' ' -f1)"
elpis_hash="$(sha256sum "$elpis_bin" | cut -d' ' -f1)"
process_status="$(cat "$run_dir/process_status")"
completion_status="$(cat "$run_dir/completion_status")"
jq -n \
  --arg run_id "$run_id" \
  --arg started "$started" \
  --arg finished "$finished" \
  --arg task "$task" \
  --arg rep "$rep" \
  --arg model "$model" \
  --arg provider "$provider" \
  --arg sandbox "$sandbox" \
  --arg prompt "$prompt" \
  --arg prompt_sha256 "$prompt_hash" \
  --arg fixture_sha256 "$fixture_hash" \
  --arg elpis_binary_sha256 "$elpis_hash" \
  --arg transcript "transcript.txt" \
  --arg workspace "workspace" \
  --arg process_status "$process_status" \
  --arg completion_status "$completion_status" \
  '{run_id:$run_id,started_at_utc:$started,finished_at_utc:$finished,task:$task,repetition:($rep|tonumber),provider:$provider,model_id:$model,elpis_binary_sha256:$elpis_binary_sha256,sandbox:$sandbox,approval_mode:"never",prompt_file:$prompt,prompt_sha256:$prompt_sha256,fixture_sha256:$fixture_sha256,raw_transcript:$transcript,workspace:$workspace,process_status:($process_status|tonumber),completion_status:$completion_status}' > "$run_dir/run.json"
rm -f "$stop_file"
echo "$run_id process_status=$process_status completion_status=$completion_status"
