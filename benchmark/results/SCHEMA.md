# Run record schema

Each real run should retain a `run.json` with at least:

```json
{
  "benchmark_id": "elpis-developer-workflows-v0.1",
  "task_id": "context_pressure_01",
  "arm": "elpis",
  "repetition": 1,
  "provider": "openrouter",
  "model_id": "provider/model",
  "prompt_sha256": "...",
  "fixture_sha256": "...",
  "elpis_binary_sha256": "...",
  "sandbox": "workspace-write",
  "approval_mode": "never",
  "end_to_end_pass": false,
  "failure_class": "provider_error",
  "elapsed_seconds": null,
  "input_tokens": null,
  "output_tokens": null,
  "peak_context_tokens": null,
  "tool_calls": null,
  "raw_transcript": "transcript.txt",
  "workspace": "workspace",
  "isolated_state": "temporary",
  "runner_status": 1
}
```

`null` means the provider or runner did not expose the measurement. It must not
be silently converted to zero.

`isolated_state` is `temporary` in the current runner: the per-run
`CODEX_HOME` stays outside the result tree so credentials and large caches are
not archived.
