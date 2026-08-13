# Evaluation protocol

## Question

What succeeds and fails when Ling-3.0-flash is hosted by Elpis on small,
reproducible developer workflows? The same protocol is ready for Tiny once a
documented serving path exists.

## Design

The pilot has four fixed task families and three repetitions per model arm:

| Task | Signal | Mechanical outcome |
| --- | --- | --- |
| `exact_contract` | strict instruction following | exact one-line JSON |
| `code_scope` | coding and tool use | tests pass; only `calculator.py` changes |
| `long_context` | retrieval and abstention | exact `answer.json`, including `NOT_FOUND` |
| `tool_sequence` | multi-step tool use | exact `answer.json`, no source changes |

The Elpis build is held constant within the arm. Every run records model ID,
provider, sandbox, approval mode, prompt/fixture hashes, raw transcript, and
workspace outcome. Timeouts, provider failures, adapter failures, and missing
tool execution are infrastructure outcomes, not model passes or failures.

## Scoring

`exact_contract` passes only when the final response is exactly the expected
JSON line after removing one terminal newline. Workspace tasks pass only when
the expected artifact/tests are correct and Git contains no forbidden edits.
All repetitions, including failures, remain in the report.

## Boundaries

This supports observations about these runs and the Elpis/provider path. It
cannot establish general benchmark rank, production readiness, safety, or an
Elpis causal effect. A direct-provider paired baseline would be required for
the last claim.

