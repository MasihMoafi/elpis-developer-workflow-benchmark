# Ling-3.0 Flash / Elpis recovery report

Date: 2026-08-13

## Bottom line

The Flash evaluation project is usable for inspection, but it is not a clean
benchmark. In the primary three-repetition protocol, Flash completed
exact-contract 3/3, code-scope 2/3, long-context 2/3, and tool-sequence 2/3.
Four bounded supplemental retries added two code repairs and exposed provider
disconnects on the two missing workspace-task paths.

## Recovered evidence

The recovery contains four fixed task families with three primary repetitions
each:

| Task | Raw runs | Evidence in recovery |
| --- | ---: | --- |
| `exact_contract` | 3 | expected JSON present in all 3 transcripts; wrapper timeout in all 3 |
| `code_scope` | 3 | correct source repair and `PASS` response in repetitions 1–2; repetition 3 incomplete |
| `long_context` | 3 | exact `answer.json` and allowed scope in repetitions 1–2; repetition 3 incomplete |
| `tool_sequence` | 3 | exact `answer.json` and allowed scope in repetitions 1–2; repetition 3 incomplete |

Every primary run retains `transcript.txt`, `run.json`, and its final workspace.
The runner metadata identifies the provider, model, prompt hash, fixture hash,
Elpis binary hash, sandbox, approval mode, and wrapper process status. The
supplemental `code_scope__r04` artifact has no `run.json`, which is recorded
explicitly below.

Some historical raw metadata keeps absolute prompt paths from before the
recovery was consolidated. That provenance was not rewritten; current project
files use repository-relative paths.

## Bounded continuation

After the computer failure, the project was restored from Trash and the
historical runs were left unchanged. Supplemental retries used fresh
directories and a completion-aware local monitor:

| Retry | Result | Evidence |
| --- | --- | --- |
| `code_scope__r04` | pass, supplemental | fresh workspace re-score passes; its stored pre-stop `score.json` is stale/fail and launcher metadata is missing |
| `code_scope__r05` | pass, supplemental | tests pass; only `calculator.py` changed; launcher metadata retained |
| `long_context__r04` | incomplete | context was read, then OpenRouter disconnected before `answer.json` |
| `tool_sequence__r04` | incomplete | task was started, then OpenRouter disconnected before `answer.json` |

The primary protocol therefore remains 3/3, 2/3, 2/3, and 2/3 respectively;
including supplemental retries, the observed counts are code-scope 4/5,
long-context 2/4, and tool-sequence 2/4. Supplemental retries are not a new
model arm or a replacement for the fixed protocol.

OpenRouter cumulative usage reported `39.246513295` before these retries and
`39.247860721` afterward, a reported increase of `0.001347426` account units.
The key endpoint exposed no configured limit or remaining-limit value.

## Harness correction before any rerun

The local runner was corrected before the supplemental retries. It now
polls the task scorer, stops the PTY when a valid task result appears, records
`completion_status` separately from the process exit status, classifies
provider disconnects, refuses to overwrite an existing run, and accepts an
explicit Elpis binary/provider/model through environment variables. The exact
contract also has a mechanical transcript check; its known ceiling is the
terminal-echo heuristic documented in `scripts/score.sh`.

A local fake-Elpis smoke was recorded during the continuation for the four task
paths plus provider-error and timeout classification. No fake binary or test
fixture is retained in this project, so this is setup evidence only; it is not a
new Flash result and is not independently reproducible from the repository.

## Infrastructure condition

All primary wrapper runs ended under the PTY timeout boundary: eleven with
status 124 and one with status 143. The supplemental `code_scope__r05` was
stopped by the monitor after its workspace passed and consequently has status
143; both supplemental workspace failures reached status 124. These statuses
are infrastructure evidence, not model pass/fail scores.

The first two `code_scope` workspaces predate the fixture's `.gitignore` and
contain generated `__pycache__` bytecode. The scoring script now excludes that
generated runtime noise when checking the allowed source scope. The historical
workspaces and transcripts remain unchanged.

## What this does not establish

This is not a general model ranking, a Tiny result, a production-readiness
claim, a safety evaluation, or evidence that Elpis itself improves task
performance. A clean replicated comparison would require a reliable completion
boundary and a paired direct-provider baseline.

## Source of truth

See `RECOVERY.md` for the lost-path and chat-path record, `EVALUATION.md` for
the protocol, and `results/runs/` for the raw evidence.
