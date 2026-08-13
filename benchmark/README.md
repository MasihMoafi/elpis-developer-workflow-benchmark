# Elpis Developer Workflow Benchmark

Status: task suite and local scorers built; bounded two-task pilot captured;
full suite not run.

## The question

Does Elpis help the same model complete long, multi-step developer work
correctly, compared with running that model directly?

The benchmark is about Elpis. A model such as Ling-3.0-Flash is only one test
arm; it is not the claim.

## What the benchmark can show

On this fixed task suite and under the declared limits, it can compare:

- whether the task finished correctly;
- whether the agent obeyed file and output limits;
- whether long tool output or a session break caused a failure;
- time, tokens, context peak, tool calls, and failure class.

It cannot establish that Elpis is universally better, that a model is best, or
that either system improves real-world productivity without further evidence.

## The task suite

There are 12 fixed tasks across six families:

| Family | Plain-language question | Tasks |
| --- | --- | ---: |
| Contract | Can it follow an exact output rule? | 2 |
| Scoped code | Can it fix code without touching other files? | 2 |
| Long retrieval | Can it find the right facts and avoid guessing? | 2 |
| Tool workflow | Can it read, calculate, write, and validate? | 2 |
| Context pressure | Can it keep one important fact through noisy output? | 2 |
| Continuity | Can it continue after a phase/session break? | 2 |

The first four families are ordinary developer-work sanity checks. The last
two are the Elpis-specific stress cases. A short exact-JSON task cannot prove
anything about context pruning, so it is never the headline result.

## First bounded pilot

This is an adapter check, not a benchmark conclusion. The same
`inclusionai/ling-3.0-flash` model was run once through each arm on two tasks:

| Task | Direct | Elpis | Evidence-led reading |
| --- | --- | --- | --- |
| `contract_01` | pass | pass* | Exact JSON was captured in both arms. The original Elpis run stopped late because the old transcript scorer expected two echoed lines; [`rescored.json`](results/runs/elpis__contract_01__r01/rescored.json) records the corrected independent score. |
| `scoped_code_01` | pass | timeout | Direct repaired the code and passed tests. Elpis reached `minimal` reasoning, produced one planning sentence, made no edit, and hit the 180-second limit. |

The full 12-task matrix and continuity-recall repetitions remain deliberately
unrun. Raw attempts are under [`results/runs/`](results/runs/); the archived
superseded Elpis attempts are outside the benchmark tree in `/tmp`.

## Continuity recall sub-benchmark

The suite also includes a stronger 30-case continuity protocol copied from
Elpis's evaluation materials. It asks for ten exact planted tokens, ten
paraphrased versions of the same facts, and ten deliberately absent tokens.
Those cases run only after both arms complete the same long-session and real
restart sequence. The planned design is 10 repetitions per arm. See
[`continuity/README.md`](continuity/README.md).

## Why these tasks

The task families come from Elpis's documented behavior: context control,
inspectable edits and commands, continuity across compaction or restart, and
durable evidence. [The task manifest](tasks.json) attaches one claim to every
task.

## Local checks

From this directory's parent:

```bash
python3 benchmark/scripts/validate.py
python3 benchmark/scripts/smoke.py
rustc benchmark/continuity/score.rs -o /tmp/elpis-score-context-continuity-v01
/tmp/elpis-score-context-continuity-v01 benchmark/continuity/cases.tsv --self-test
python3 benchmark/scripts/run_task.py --help
```

These checks create temporary workspaces, verify that deliberate defects fail
before repair, and verify all 12 declared scorers with local oracle answers.
They do not call a model or change Elpis.

`run_task.py` prints a dry-run plan by default. It requires the explicit
`--execute` flag before it can start an external agent process.

The one-shot and two-phase runner paths have been exercised with a fake local
agent. The direct Codex and Elpis one-shot adapters have also been boundedly
checked; continuity-restart runs still need their own controlled check.

## Real-run protocol

The same task, model, provider, prompt, fixture, sandbox, approval policy, and
time limit must be run in both arms:

1. direct model path;
2. Elpis path.

Each task needs repeated runs, raw transcript and workspace retention, exact
task scoring, and separate labels for model failure versus provider or launcher
failure. See [PROTOCOL.md](PROTOCOL.md).
