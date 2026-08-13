#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
required=(README.md EVALUATION.md tasks.json prompts/exact_contract.md prompts/code_scope.md prompts/long_context.md prompts/tool_sequence.md fixtures/calculator/calculator.py fixtures/calculator/tests/test_calculator.py fixtures/long-context/context.md fixtures/tool-sequence/events.json results/SCHEMA.md)
for path in "${required[@]}"; do [[ -f "$path" ]] || { echo "missing $path" >&2; exit 1; }; done
jq -e '.tasks | length == 4 and all(.[]; (.id|type)=="string" and (.prompt|type)=="string")' tasks.json >/dev/null
if rg -n --hidden --glob '!.git/**' '(^|[^[:alnum:]])(sk|hf)_[[:alnum:]]{20,}' .; then echo 'credential-looking token found' >&2; exit 1; fi
echo 'eval-flash validation passed'
