#!/usr/bin/env python3
"""Run one frozen task through an external agent binary.

The runner is deliberately outside Elpis. It requires --execute before it can
start a model process.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
MANIFEST = ROOT / "tasks.json"
PREPARE = ROOT / "scripts" / "prepare.py"
SCORE = ROOT / "scripts" / "score.py"
PHASE_RUNNER = ROOT / "scripts" / "pty_phases.py"
ONE_SHOT_RUNNER = PROJECT_ROOT / "scripts" / "pty_run.py"
DEFAULT_AGENT = os.environ.get("ELPIS_BIN", "elpis")
DIRECT_DEFAULT_AGENT = os.environ.get("DIRECT_AGENT_BIN", "codex")
ERROR_MARKERS = re.compile(r"Stream disconnected before completion|unexpected status [0-9]+|provider returned error", re.I)


def direct_codex_config(model: str) -> str:
    """Return an isolated direct-Codex config without copying user state."""
    return "\n".join(
        [
            f"model = {json.dumps(model)}",
            'model_provider = "openrouter"',
            'approval_policy = "never"',
            'sandbox_mode = "workspace-write"',
            'model_reasoning_effort = "minimal"',
            'model_verbosity = "low"',
            "",
            "[model_providers.openrouter]",
            'name = "OpenRouter"',
            'base_url = "https://openrouter.ai/api/v1"',
            'env_key = "OPENROUTER_API_KEY"',
            'wire_api = "responses"',
            "request_max_retries = 0",
            "stream_max_retries = 0",
            "",
        ]
    )


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_task(task_id: str) -> dict:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for task in data["tasks"]:
        if task["id"] == task_id:
            return task
    raise SystemExit(f"unknown task: {task_id}")


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def digest_tree(path: Path | None) -> str:
    if not path:
        return ""
    digest = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if not item.is_file() or "__pycache__" in item.parts or item.suffix == ".pyc":
            continue
        digest.update(str(item.relative_to(path)).encode())
        digest.update(item.read_bytes())
    return digest.hexdigest()


def task_prompts(task: dict) -> list[Path]:
    values = task["prompt"] if isinstance(task["prompt"], list) else [task["prompt"]]
    return [ROOT / value for value in values]


def score_args(task: dict, workspace: Path, transcript: Path, response: Path | None = None) -> list[str]:
    args = [sys.executable, str(SCORE), task["id"], str(workspace)]
    if task["score"] == "exact_response":
        args += ["--response", str(response)] if response is not None else ["--transcript", str(transcript)]
    elif task["score"] == "phase_continuity_and_scope":
        args += ["--phase-log", str(transcript)]
    return args


def run_score(task: dict, workspace: Path, transcript: Path, response: Path | None = None) -> tuple[bool, dict | None]:
    completed = subprocess.run(score_args(task, workspace, transcript, response), capture_output=True, text=True)
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return False, None
    return completed.returncode == 0 and payload.get("status") == "pass", payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_id")
    parser.add_argument("arm", choices=["direct", "elpis"])
    parser.add_argument("repetition", type=int)
    parser.add_argument("--agent-bin")
    parser.add_argument("--provider", default=os.environ.get("ELPIS_PROVIDER", "openrouter"))
    parser.add_argument("--model", default=os.environ.get("ELPIS_MODEL", "inclusionai/ling-3.0-flash"))
    parser.add_argument("--sandbox", default="workspace-write")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--execute", action="store_true", help="start the external agent process")
    args = parser.parse_args()
    if args.repetition < 1:
        raise SystemExit("repetition must be positive")
    if args.agent_bin is None:
        env_name = "DIRECT_AGENT_BIN" if args.arm == "direct" else "ELPIS_BIN"
        default_agent = DIRECT_DEFAULT_AGENT if args.arm == "direct" else DEFAULT_AGENT
        args.agent_bin = os.environ.get(env_name, default_agent)
    if args.arm == "direct" and args.provider != "openrouter":
        raise SystemExit("the direct adapter currently supports only provider=openrouter")
    task = load_task(args.task_id)
    run_id = f"{args.arm}__{args.task_id}__r{args.repetition:02d}"
    run_dir = ROOT / "results" / "runs" / run_id
    if run_dir.exists():
        raise SystemExit(f"run already exists: {run_dir} (raw runs are immutable)")
    workspace = run_dir / "workspace"
    transcript = run_dir / "transcript.txt"
    stop_file = run_dir / "stop"
    prompts = task_prompts(task)
    response = run_dir / "response.txt" if args.arm == "direct" and len(prompts) == 1 else None
    prompt_hash = hashlib.sha256(b"\0".join(path.read_bytes() for path in prompts)).hexdigest()
    fixture_hash = digest_tree(ROOT / task["fixture"]) if task.get("fixture") else ""
    command = [args.agent_bin, "--model", args.model, "--sandbox", args.sandbox, "--ask-for-approval", "never", "--no-alt-screen"]
    if len(prompts) == 1:
        command += [str(prompts[0])]
    else:
        command += [str(prompts[0]), str(prompts[1])]
    dry_run = {
        "run_id": run_id,
        "task": args.task_id,
        "arm": args.arm,
        "agent_bin": args.agent_bin,
        "provider": args.provider,
        "model": args.model,
        "prompts": [str(path) for path in prompts],
        "execute": args.execute,
    }
    if not args.execute:
        print(json.dumps(dry_run, indent=2, sort_keys=True))
        return 0
    if args.arm == "direct" and not os.environ.get("OPENROUTER_API_KEY"):
        raise SystemExit("direct arm requires OPENROUTER_API_KEY; no model call was started")
    resolved_agent = shutil.which(args.agent_bin)
    agent_path = Path(resolved_agent or args.agent_bin)
    args.agent_bin = str(agent_path)
    if not agent_path.is_file() or not os.access(agent_path, os.X_OK):
        raise SystemExit(f"agent binary is not executable: {args.agent_bin}")
    run_dir.mkdir(parents=True)
    subprocess.run([sys.executable, str(PREPARE), args.task_id, str(workspace)], check=True)
    started = utc_now()
    environment = os.environ.copy()
    environment.update({
        "ELPIS_MODEL": args.model,
        "TERM": "xterm-256color",
    })
    if args.arm == "direct":
        codex_home = Path(tempfile.mkdtemp(prefix=f"elpis-benchmark-{run_id}-", dir="/tmp"))
        (codex_home / "config.toml").write_text(direct_codex_config(args.model), encoding="utf-8")
        environment.update({
            "BENCHMARK_ARM": "direct",
            "DIRECT_AGENT_BIN": args.agent_bin,
            "CODEX_HOME": str(codex_home),
        })
    else:
        codex_home = Path(tempfile.mkdtemp(prefix=f"elpis-benchmark-{run_id}-", dir="/tmp"))
        (codex_home / "config.toml").write_text(
            'approval_policy = "never"\n'
            'sandbox_mode = "workspace-write"\n'
            'model_reasoning_effort = "minimal"\n'
            'model_verbosity = "low"\n',
            encoding="utf-8",
        )
        environment.update({
            "BENCHMARK_ARM": "elpis",
            "ELPIS_BIN": args.agent_bin,
            "ELPIS_PROVIDER": args.provider,
            "CODEX_HOME": str(codex_home),
        })
        environment.pop("ELPIS_CODEX_HOME", None)
    runner = PHASE_RUNNER if len(prompts) == 2 else ONE_SHOT_RUNNER
    if len(prompts) == 2:
        runner_command = [sys.executable, str(runner), str(workspace), str(transcript), str(prompts[0]), str(prompts[1]), args.sandbox, "--timeout", str(args.timeout), "--stop-file", str(stop_file)]
    else:
        runner_command = [sys.executable, str(runner), str(workspace), str(transcript), str(prompts[0]), args.sandbox, "--timeout", str(args.timeout), "--stop-file", str(stop_file)]
        if response is not None:
            runner_command += ["--response", str(response)]
    with (run_dir / "runner.log").open("w", encoding="utf-8") as runner_log:
        process = subprocess.Popen(runner_command, stdout=runner_log, stderr=subprocess.STDOUT, env=environment)
        completion_status = "timeout"
        score_payload = None
        while process.poll() is None:
            if transcript.exists():
                passed, score_payload = run_score(task, workspace, transcript, response)
                if passed:
                    completion_status = "pass"
                    stop_file.touch()
                    break
                if ERROR_MARKERS.search(transcript.read_text(encoding="utf-8", errors="replace")):
                    completion_status = "provider_error"
                    stop_file.touch()
                    break
            time.sleep(0.25)
        process_status = process.wait()
    if completion_status == "timeout":
        passed, score_payload = run_score(task, workspace, transcript, response)
        if passed:
            completion_status = "pass"
        elif transcript.exists() and ERROR_MARKERS.search(transcript.read_text(encoding="utf-8", errors="replace")):
            completion_status = "provider_error"
        elif process_status == 124:
            completion_status = "timeout_before_score"
        else:
            completion_status = "launcher_error"
    if score_payload is not None:
        (run_dir / "score.json").write_text(json.dumps(score_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    finished = utc_now()
    metadata = {
        "benchmark_id": "elpis-developer-workflows-v0.1",
        "run_id": run_id,
        "task_id": args.task_id,
        "arm": args.arm,
        "repetition": args.repetition,
        "started_at_utc": started,
        "finished_at_utc": finished,
        "provider": args.provider,
        "model_id": args.model,
        "agent_binary_sha256": digest_file(agent_path),
        "prompt_sha256": prompt_hash,
        "fixture_sha256": fixture_hash,
        "sandbox": args.sandbox,
        "approval_mode": "never",
        "process_status": process_status,
        "completion_status": completion_status,
        "end_to_end_pass": completion_status == "pass",
        "raw_transcript": "transcript.txt",
        "workspace": "workspace",
        "isolated_state": "temporary",
    }
    (run_dir / "run.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    stop_file.unlink(missing_ok=True)
    print(json.dumps({"run_id": run_id, "completion_status": completion_status, "process_status": process_status}, sort_keys=True))
    return 0 if completion_status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
