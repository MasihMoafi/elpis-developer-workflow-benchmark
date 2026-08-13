#!/usr/bin/env python3
"""Static validation for the frozen task suite."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tasks.json"


def fail(message: str) -> None:
    raise SystemExit(message)


def main() -> int:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    tasks = data.get("tasks", [])
    if len(tasks) != 12:
        fail(f"expected 12 frozen tasks, found {len(tasks)}")
    ids = [task["id"] for task in tasks]
    if len(ids) != len(set(ids)):
        fail("task IDs are not unique")
    families = {family["id"] for family in data["task_families"]}
    if {task["family"] for task in tasks} != families:
        fail("task family coverage is incomplete")
    for task in tasks:
        prompts = task["prompt"] if isinstance(task["prompt"], list) else [task["prompt"]]
        for prompt in prompts:
            path = ROOT / prompt
            if not path.is_file() or not path.read_text(encoding="utf-8").strip():
                fail(f"missing or empty prompt: {prompt}")
        fixture = task.get("fixture")
        if fixture and not (ROOT / fixture).is_dir():
            fail(f"missing fixture: {fixture}")
        if task["score"] == "exact_response" and not task.get("expected"):
            fail(f"missing exact expected response: {task['id']}")
        if task["score"] == "json_artifact_and_scope" and not task.get("expected_json"):
            fail(f"missing JSON oracle: {task['id']}")
    for path in (ROOT / "fixtures").rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    continuity = data["sub_benchmarks"][0]
    case_lines = [line.split("\t") for line in (ROOT / continuity["cases"]).read_text(encoding="utf-8").splitlines() if line.strip()][1:]
    if len(case_lines) != 30 or {row[1] for row in case_lines} != {"exact", "semantic", "negative"}:
        fail("continuity recall must contain 30 cases in three groups")
    if any(sum(row[1] == group for row in case_lines) != 10 for group in ("exact", "semantic", "negative")):
        fail("continuity recall groups must contain ten cases each")
    continuity_fixture = (ROOT / continuity["fixture"]).read_text(encoding="utf-8")
    if "ORCHID-ANCHOR-731" not in continuity_fixture or "ABSENT-" not in continuity_fixture:
        fail("continuity fixture is missing planted or absent tokens")
    for task_id in ("context_pressure_01", "context_pressure_02"):
        task = next(task for task in tasks if task["id"] == task_id)
        script = ROOT / task["fixture"] / ("emit_log.py" if task_id.endswith("01") else "emit_incidents.py")
        output = subprocess.run([sys.executable, str(script)], check=True, capture_output=True, text=True).stdout
        if len(output) < task["pressure_output_chars"]:
            fail(f"{task_id} output is too small: {len(output)} chars")
        if "AUTHORITATIVE" not in output:
            fail(f"{task_id} lacks an authoritative record")
    print("benchmark task validation passed: 12 tasks, 6 families, 30 continuity probes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
