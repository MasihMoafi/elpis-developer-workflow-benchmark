# Experiment setup intent

Build a separate, presentable Elpis developer-workflow benchmark without
modifying Elpis itself. Keep the recovered Flash evidence intact, define fixed
tasks and mechanical scorers, and run only bounded model pilots after the local
suite and external runner are verified.

## Boundaries

- Do not rewrite or delete historical raw runs.
- Do not launch the full model/API matrix until the pilot adapter and scorer boundaries are stable.
- Do not download Tiny weights; Tiny is an unrun arm.
- Do not modify the Elpis source tree.
- Do not claim general ranking, production readiness, safety, or an Elpis causal
  performance effect.

## Current session status

The surviving recovery is the repository root. The original Codex chat is
retained locally but is not part of this repository. The new benchmark is under `benchmark/`; its 12
task definitions, scorers, local smoke checks, external runner, and
presentation page are built. A bounded two-task pilot is recorded: direct
passed the contract and code tasks; Elpis produced the contract answer but
timed out before editing the code task. This is pilot evidence, not an
aggregate benchmark result.

The bounded continuation used fresh directories and did not rewrite historical
runs. It added one fully recorded code-scope pass, one metadata-incomplete code
pass, and two provider-disconnect failures. The separate benchmark pilot used
two tasks through both arms: direct passed both; Elpis returned the contract
answer but timed out before editing the code fixture. The full matrix remains
deferred. The primary historical matrix remains exact-contract 3/3,
code-scope 2/3, long-context 2/3, and tool-sequence 2/3. The key reported
cumulative usage rose from `39.246513295` to `39.247860721`; no key limit was
exposed.

The older local PTY runner and scorer were smoke-tested with a fake Elpis
executable. The new benchmark's 12 local oracle checks and phase runner also
pass. The full task matrix and continuity-recall runs remain deliberately
deferred.
