# Benchmark protocol

## Unit of comparison

One run is one task, one model, one arm, one repetition, and one disposable
workspace. The control and treatment receive the same task and limits. The
only intended difference is the execution path: direct model or Elpis.

## Before a run

- copy the declared fixture into a new empty workspace;
- record the task and prompt hashes;
- initialize a baseline Git commit for workspace tasks;
- use a fresh isolated `CODEX_HOME` for the arm and repetition; keep it
  temporary so credentials, plugin caches, and session databases are not
  copied into the result archive;
- set a fixed model, provider, sandbox, approval policy, and wall-clock limit;
- do not allow network access from the task itself;
- do not overwrite an existing run directory.

The external runner lives in `scripts/run_task.py`; it is deliberately outside
Elpis and requires `--execute` before launching an agent.

## During a run

Retain the raw terminal transcript, final workspace, runner log, and provider
metadata. The current external runner records the isolated state as temporary
and does not archive credentials, plugin caches, or session databases. Copy
only non-secret context or pruning records when the arm exposes them. For the
direct arm, retain the equivalent provider response and tool trace.

Continuity tasks are two-phase tasks. Phase 1 ends with `PHASE_ONE_DONE` and no
workspace edit. Phase 2 starts after the configured session break and receives
only the phase-2 instruction plus whatever state the arm normally preserves.

The continuity-recall sub-benchmark is stricter: both arms receive the same
ordinary-turn sequence, must traverse the real compaction and restart path, and
then answer all 30 rows in `continuity/cases.tsv` in order. It has ten exact,
ten paraphrase, and ten absent-token checks. A run is invalid if the restart
path was not actually traversed.

## Primary result

`end_to_end_pass` is binary and mechanical:

- exact response tasks: the response equals the declared line;
- code tasks: tests pass and only allowed files changed;
- artifact tasks: the JSON equals the declared object and only the artifact is
  new;
- continuity tasks: phase 1 completed, phase 2 finishes correctly, and scope
  checks pass.

## Secondary measurements

Record these when the provider and runner expose them:

- elapsed seconds;
- input, output, and total tokens;
- peak context tokens or percentage;
- number of tool calls;
- number of pruning/compaction events;
- API cost when available;
- failure class.

Do not replace missing telemetry with zero. Mark it unavailable.

## Failure classes

`model_wrong`, `scope_violation`, `format_wrong`, `tool_failure`,
`continuity_lost`, `provider_error`, `launcher_error`, `timeout_before_score`,
and `telemetry_missing` are separate labels. Provider, launcher, and timeout
failures are not model failures.

## Publication gate

Do not publish a comparison until:

- every task has a working scorer;
- both arms use the same task and fixture hashes;
- the runner has a tested completion boundary;
- raw evidence exists for every attempted repetition;
- model failures and infrastructure failures are separated;
- the report shows individual repetitions, not only an average.
