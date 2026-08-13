#!/usr/bin/env python3
"""Exercise every declared scorer with a local oracle, never a model."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREPARE = ROOT / "scripts" / "prepare.py"
SCORE = ROOT / "scripts" / "score.py"
MANIFEST = json.loads((ROOT / "tasks.json").read_text(encoding="utf-8"))


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], check=True, capture_output=True, text=True)


def prepare(task_id: str, destination: Path) -> None:
    run(str(PREPARE), task_id, str(destination))


def score(task_id: str, workspace: Path, *extra: str) -> dict:
    completed = subprocess.run(
        [sys.executable, str(SCORE), task_id, str(workspace), *extra],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise AssertionError(f"{task_id}: scorer failed: {completed.stdout}{completed.stderr}")
    return json.loads(completed.stdout)


def write_json(workspace: Path, value: dict) -> None:
    (workspace / "answer.json").write_text(json.dumps(value, separators=(",", ":")) + "\n", encoding="utf-8")


def patch_file(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise AssertionError(f"oracle patch did not find expected text in {path}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="elpis-benchmark-smoke-") as temp:
        root = Path(temp)
        outputs = []

        for task in MANIFEST["tasks"]:
            task_id = task["id"]
            workspace = root / task_id
            prepare(task_id, workspace)
            score_args: list[str] = []
            if task["score"] in {"python_tests_and_scope", "phase_continuity_and_scope"}:
                baseline = subprocess.run(
                    [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                    cwd=workspace,
                    capture_output=True,
                    text=True,
                )
                if baseline.returncode == 0:
                    raise AssertionError(f"{task_id}: baseline fixture unexpectedly passed")
            if task["score"] == "exact_response":
                response = root / f"{task_id}.response.txt"
                response.write_text(task["expected"] + "\n", encoding="utf-8")
                score_args = ["--response", str(response)]
            elif task_id == "scoped_code_01":
                patch_file(workspace / "calculator.py", "100 + percentage", "100 - percentage")
            elif task_id == "scoped_code_02":
                patch_file(
                    workspace / "slugify.py",
                    'return text.strip().lower().replace(" ", "_")',
                    'return re.sub(r"[^a-z0-9]+", "-", text.strip().lower()).strip("-")',
                )
            elif task_id == "long_retrieval_01":
                write_json(workspace, task["expected_json"])
            elif task_id == "long_retrieval_02":
                write_json(workspace, task["expected_json"])
            elif task_id == "tool_workflow_01":
                write_json(workspace, task["expected_json"])
            elif task_id == "tool_workflow_02":
                write_json(workspace, task["expected_json"])
            elif task_id == "context_pressure_01":
                patch_file(workspace / "settings.py", '"canary"', '"stable"')
            elif task_id == "context_pressure_02":
                write_json(workspace, task["expected_json"])
            elif task_id == "continuity_01":
                patch_file(workspace / "service.py", "limit + attempts", "limit - attempts")
                phase_log = root / f"{task_id}.phase.log"
                phase_log.write_text("inspection complete\nPHASE_ONE_DONE\n", encoding="utf-8")
                score_args = ["--phase-log", str(phase_log)]
            elif task_id == "continuity_02":
                patch_file(workspace / "release.py", "return end_hour - start_hour", "return (end_hour - start_hour) % 24")
                phase_log = root / f"{task_id}.phase.log"
                phase_log.write_text("inspection complete\nPHASE_ONE_DONE\n", encoding="utf-8")
                score_args = ["--phase-log", str(phase_log)]
            outputs.append(score(task_id, workspace, *score_args))

        if any(item["status"] != "pass" for item in outputs):
            raise AssertionError(outputs)
        print(json.dumps({"status": "pass", "tasks": len(outputs), "results": outputs}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
