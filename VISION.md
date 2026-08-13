# eval-flash

## What this is

`eval-flash` contains a recovered Flash/Elpis pilot and a separate, presentable
benchmark for measuring Elpis on longer developer workflows.

## Core thesis

The useful question is whether the same model completes fixed, inspectable
developer tasks more reliably or efficiently through Elpis than directly.

## Map

- `prompts/` — fixed task instructions.
- `fixtures/` — disposable local workspaces and source data.
- `scripts/` — workspace preparation, Elpis PTY execution, scoring, and static validation.
- `results/runs/` — raw transcripts, metadata, and final disposable workspaces.
- `EVALUATION.md` — protocol and claim boundaries.
- `REPORT.md` — current evidence report.
- `RECOVERY.md` — lost-path and chat-recovery record.
- `benchmark/` — the new 12-task suite, scorers, external runner, protocol, and presentation page.

## Honest state — 2026-08-13

The original uncommitted directory was lost. This filesystem recovery contains
the protocol, 12 primary Flash runs, and four supplemental retry artifacts. The
primary results are exact-contract 3/3,
code-scope 2/3, long-context 2/3, and tool-sequence 2/3. Two supplemental code
retries passed; two supplemental workspace retries hit provider disconnects. The
evidence is useful for a bounded compatibility observation but is not a clean
benchmark, a model ranking, or evidence of an Elpis causal benefit. Tiny was
not run. The clean benchmark has 12 task definitions and passing local oracle
checks, and a two-task real pilot: direct passed both tasks; Elpis produced the
exact contract response but timed out before editing the code fixture. The full
matrix and continuity sub-benchmark remain unrun.

## What this file is for

This is the cold re-entry point. Keep it aligned with the actual files and
evidence, and keep unsupported claims out of public-facing summaries.
