# Elpis Developer Workflow Benchmark

An evidence-first benchmark for one practical question:

> Does the same model complete fixed, multi-step developer tasks correctly
> more reliably through Elpis than directly?

The benchmark compares identical prompts, fixtures, provider, model, sandbox,
approval policy, and time limit. Only the execution path changes: direct model
execution versus the same model through Elpis.

## Start here

- [Open the visual benchmark page](benchmark/index.html)
- [Read the benchmark README](benchmark/README.md)
- [Read the test protocol](benchmark/PROTOCOL.md)
- [Inspect the task manifest](benchmark/tasks.json)

## Current status

The suite contains 12 fixed tasks across six developer-workflow families and a
separate 30-probe continuity protocol. A bounded pilot is recorded for
`inclusionai/ling-3.0-flash`: direct passed the contract and code tasks;
Elpis produced the exact contract response but timed out before editing the
code fixture. This is pilot evidence, not an aggregate benchmark conclusion.

The full matrix and continuity repetitions remain deliberately unrun. Raw
pilot records are under [`benchmark/results/runs/`](benchmark/results/runs/).

## Boundaries

This repository contains the benchmark and recovered evaluation notes. It does
not modify the Elpis source tree, claim universal model or product superiority,
or turn missing telemetry into zero. No credentials or local state are stored
here.

Run `./scripts/validate.sh` for the repository's existing validation, then use
the commands in [`benchmark/README.md`](benchmark/README.md) for the clean
benchmark checks.
