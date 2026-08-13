#!/usr/bin/env python3
"""Score one finished task using only its declared mechanical contract."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANSI = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def load_task(task_id: str) -> dict:
    data = json.loads((ROOT / "tasks.json").read_text(encoding="utf-8"))
    for task in data["tasks"]:
        if task["id"] == task_id:
            return task
    raise SystemExit(f"unknown task: {task_id}")


def result(task_id: str, status: str, reason: str, **extra: object) -> dict:
    return {"task": task_id, "status": status, "reason": reason, **extra}


def changed_paths(workspace: Path) -> list[str]:
    raw = subprocess.run(
        ["git", "-C", str(workspace), "status", "--short", "--untracked-files=all"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    paths = []
    for line in raw:
        path = line[3:] if len(line) >= 3 else ""
        if path.endswith(".pyc") or "/__pycache__/" in path:
            continue
        paths.append(path)
    return sorted(paths)


def expected_paths(task: dict) -> list[str]:
    if task["score"] == "python_tests_and_scope":
        return sorted(task["allowed_changes"])
    if task["score"] == "json_artifact_and_scope":
        return [task["expected_file"]]
    if task["score"] == "phase_continuity_and_scope":
        return sorted(task["allowed_changes"])
    return []


def score_tests_and_scope(task: dict, workspace: Path) -> tuple[str, str]:
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=workspace,
        capture_output=True,
        text=True,
    )
    paths = changed_paths(workspace)
    allowed = expected_paths(task)
    if completed.returncode != 0:
        return "fail", "unit tests failed"
    if paths != allowed:
        return "fail", f"changed paths were {paths}, expected {allowed}"
    return "pass", "unit tests passed and only allowed source changed"


def score_json_artifact(task: dict, workspace: Path) -> tuple[str, str]:
    artifact = workspace / task["expected_file"]
    if not artifact.is_file():
        return "fail", f"missing {task['expected_file']}"
    try:
        actual = json.loads(artifact.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return "fail", f"invalid JSON: {exc}"
    if actual != task["expected_json"]:
        return "fail", "JSON artifact does not match the declared answer"
    paths = changed_paths(workspace)
    allowed = expected_paths(task)
    if paths != allowed:
        return "fail", f"changed paths were {paths}, expected {allowed}"
    return "pass", "exact JSON artifact and no forbidden changes"


def score_exact(task: dict, response: Path | None, transcript: Path | None) -> tuple[str, str]:
    if response:
        if not response.is_file():
            return "fail", "response file is missing"
        actual = response.read_text(encoding="utf-8").rstrip("\n")
        return ("pass", "exact response matched") if actual == task["expected"] else ("fail", "response was not exact")
    if not transcript or not transcript.is_file():
        return "fail", "a response file or transcript is required"
    text = ANSI.sub("", transcript.read_text(encoding="utf-8", errors="replace")).replace("\r", "")
    # ponytail: command-line prompts are not echoed by real TUI runs, so one
    # exact assistant line is sufficient; structured response files remain the
    # upgrade path for non-TUI adapters.
    matches = sum(line.strip() == task["expected"] for line in text.splitlines())
    if matches >= 1:
        return "pass", "exact response line captured"
    return "fail", f"expected response was not captured (matches={matches})"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_id")
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--response", type=Path)
    parser.add_argument("--transcript", type=Path)
    parser.add_argument("--phase-log", type=Path)
    args = parser.parse_args()
    task = load_task(args.task_id)
    workspace = args.workspace.resolve()
    if not workspace.is_dir():
        payload = result(args.task_id, "fail", "workspace is missing")
    elif task["score"] == "exact_response":
        status, reason = score_exact(task, args.response, args.transcript)
        payload = result(args.task_id, status, reason)
    elif task["score"] in {"python_tests_and_scope", "pressure_code"}:
        status, reason = score_tests_and_scope(task, workspace)
        payload = result(args.task_id, status, reason)
    elif task["score"] == "json_artifact_and_scope":
        status, reason = score_json_artifact(task, workspace)
        payload = result(args.task_id, status, reason)
    elif task["score"] == "phase_continuity_and_scope":
        if not args.phase_log or "PHASE_ONE_DONE" not in args.phase_log.read_text(encoding="utf-8", errors="replace"):
            payload = result(args.task_id, "fail", "phase log lacks PHASE_ONE_DONE")
        else:
            status, reason = score_tests_and_scope(task, workspace)
            payload = result(args.task_id, status, reason + "; phase marker present")
    else:
        payload = result(args.task_id, "fail", f"unsupported score type: {task['score']}")
    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
