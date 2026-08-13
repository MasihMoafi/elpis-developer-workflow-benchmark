#!/usr/bin/env python3
"""Create one disposable benchmark workspace from the frozen manifest."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tasks.json"


def load_task(task_id: str) -> dict:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for task in data["tasks"]:
        if task["id"] == task_id:
            return task
    raise SystemExit(f"unknown task: {task_id}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_id")
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    task = load_task(args.task_id)
    destination = args.destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        raise SystemExit(f"refusing non-empty destination: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    fixture = task.get("fixture")
    if fixture:
        shutil.copytree(ROOT / fixture, destination, dirs_exist_ok=True)
    else:
        (destination / ".workspace-marker").write_text("benchmark workspace\n", encoding="utf-8")
    if fixture:
        subprocess.run(["git", "init", "-q", str(destination)], check=True)
        subprocess.run(["git", "-C", str(destination), "config", "user.name", "benchmark"], check=True)
        subprocess.run(["git", "-C", str(destination), "config", "user.email", "benchmark@localhost"], check=True)
        subprocess.run(["git", "-C", str(destination), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(destination), "commit", "-qm", "baseline"], check=True)
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
