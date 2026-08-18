#!/usr/bin/env python3
"""Dedicated evaluation runner for Ling-3.0-tiny across the 4 developer workflow tasks.

Tasks:
1. exact_contract: Zero-shot strict JSON compliance
2. code_scope: Scoped code repair in calculator.py
3. long_context: Selective retrieval from context.md
4. tool_sequence: Multi-step reasoning over events.json
"""

import os
import sys
import json
import time
import shutil
import urllib.request
from pathlib import Path

ROOT = Path("/home/masih/Desktop/p/eval-ling-3.0-tiny")
RESULTS_DIR = ROOT / "results" / "runs"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
SERVER_URL = "http://127.0.0.1:8080/v1/chat/completions"

print(f"=== Initializing Ling-3.0-tiny Benchmark Runner ===")
print(f"Inference Endpoint: {SERVER_URL}")
print(f"Results Directory: {RESULTS_DIR}")

def generate_response(prompt_text: str, max_new_tokens: int = 1024, temperature: float = 0.0) -> tuple[str, float]:
    payload = {
        "messages": [{"role": "user", "content": prompt_text}],
        "temperature": temperature,
        "max_tokens": max_new_tokens
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(SERVER_URL, data=data, headers={"Content-Type": "application/json"})
    
    t0 = time.monotonic()
    with urllib.request.urlopen(req) as response:
        res_json = json.loads(response.read().decode("utf-8"))
    elapsed = round(time.monotonic() - t0, 2)
    
    msg = res_json["choices"][0]["message"]
    content = (msg.get("content") or "").strip()
    reasoning = (msg.get("reasoning_content") or "").strip()
    
    # If the model finished with content, return content; otherwise include reasoning
    full_output = content if content else reasoning
    return full_output, elapsed

def run_task_exact_contract(rep: int = 1):
    task_id = "exact_contract"
    run_id = f"ling_tiny__{task_id}__r{rep:02d}"
    run_dir = RESULTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    prompt_file = ROOT / "prompts" / "exact_contract.md"
    prompt_content = prompt_file.read_text(encoding="utf-8")
    
    print(f"--> Running {run_id}...")
    response, elapsed = generate_response(prompt_content, max_new_tokens=512)
    
    # Save transcript
    transcript_file = run_dir / "transcript.txt"
    transcript_file.write_text(f"Prompt:\n{prompt_content}\n\nResponse:\n{response}\n", encoding="utf-8")
    
    expected = '{"status":"ready","values":[3,8,13],"sum":24}'
    is_pass = expected in response and ("```" not in response)
    
    score = {
        "task": task_id,
        "run_id": run_id,
        "status": "pass" if is_pass else "fail",
        "reason": "Exact JSON returned without fences" if is_pass else f"Output did not match expected JSON strictly: {response[:100]}",
        "elapsed_seconds": elapsed
    }
    (run_dir / "score.json").write_text(json.dumps(score, indent=2), encoding="utf-8")
    print(f"    Result: {score['status']} ({score['reason']}) in {elapsed}s")
    return score

def run_task_code_scope(rep: int = 1):
    task_id = "code_scope"
    run_id = f"ling_tiny__{task_id}__r{rep:02d}"
    run_dir = RESULTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    workspace_dir = run_dir / "workspace"
    if workspace_dir.exists():
        shutil.rmtree(workspace_dir)
    shutil.copytree(ROOT / "fixtures" / "calculator", workspace_dir)
    
    prompt_base = (ROOT / "prompts" / "code_scope.md").read_text(encoding="utf-8")
    calc_py = (workspace_dir / "calculator.py").read_text(encoding="utf-8")
    readme = (workspace_dir / "README.md").read_text(encoding="utf-8")
    
    full_prompt = f"{prompt_base}\n\n### README.md:\n{readme}\n\n### calculator.py:\n```python\n{calc_py}\n```\nProvide the corrected calculator.py code and the required final JSON line."
    
    print(f"--> Running {run_id}...")
    response, elapsed = generate_response(full_prompt, max_new_tokens=1024)
    
    (run_dir / "transcript.txt").write_text(f"Prompt:\n{full_prompt}\n\nResponse:\n{response}\n", encoding="utf-8")
    
    has_discount_logic = "discount" in response and ("int(" in response or "//" in response or "math.floor" in response)
    has_json = '{"tests":"PASS","changed_files":["calculator.py"]}' in response
    
    is_pass = has_discount_logic and has_json
    score = {
        "task": task_id,
        "run_id": run_id,
        "status": "pass" if is_pass else "fail",
        "reason": "Correct repair logic and contract JSON emitted" if is_pass else "Missing discount truncation or strict contract format",
        "elapsed_seconds": elapsed
    }
    (run_dir / "score.json").write_text(json.dumps(score, indent=2), encoding="utf-8")
    print(f"    Result: {score['status']} in {elapsed}s")
    return score

def run_task_long_context(rep: int = 1):
    task_id = "long_context"
    run_id = f"ling_tiny__{task_id}__r{rep:02d}"
    run_dir = RESULTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    workspace_dir = run_dir / "workspace"
    if workspace_dir.exists():
        shutil.rmtree(workspace_dir)
    shutil.copytree(ROOT / "fixtures" / "long-context", workspace_dir)
    
    prompt_base = (ROOT / "prompts" / "long_context.md").read_text(encoding="utf-8")
    context_md = (workspace_dir / "context.md").read_text(encoding="utf-8")
    
    full_prompt = f"{prompt_base}\n\n### context.md:\n{context_md}"
    
    print(f"--> Running {run_id}...")
    response, elapsed = generate_response(full_prompt, max_new_tokens=1024)
    
    (run_dir / "transcript.txt").write_text(f"Prompt:\n{full_prompt}\n\nResponse:\n{response}\n", encoding="utf-8")
    
    expected_answer = '{"project_code":"Aster-17","launch_day":"Thursday","retention_days":28,"owner":"Nilo","support_tier":"NOT_FOUND"}'
    is_pass = expected_answer in response
    
    if is_pass:
        (workspace_dir / "answer.json").write_text(expected_answer, encoding="utf-8")
        
    score = {
        "task": task_id,
        "run_id": run_id,
        "status": "pass" if is_pass else "fail",
        "reason": "Exact needle data extracted from AUTHORITATIVE row" if is_pass else "Failed to extract exact needle contract",
        "elapsed_seconds": elapsed
    }
    (run_dir / "score.json").write_text(json.dumps(score, indent=2), encoding="utf-8")
    print(f"    Result: {score['status']} in {elapsed}s")
    return score

def run_task_tool_sequence(rep: int = 1):
    task_id = "tool_sequence"
    run_id = f"ling_tiny__{task_id}__r{rep:02d}"
    run_dir = RESULTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    workspace_dir = run_dir / "workspace"
    if workspace_dir.exists():
        shutil.rmtree(workspace_dir)
    shutil.copytree(ROOT / "fixtures" / "tool-sequence", workspace_dir)
    
    prompt_base = (ROOT / "prompts" / "tool_sequence.md").read_text(encoding="utf-8")
    events_json = (workspace_dir / "events.json").read_text(encoding="utf-8")
    
    full_prompt = f"{prompt_base}\n\n### events.json:\n{events_json}"
    
    print(f"--> Running {run_id}...")
    response, elapsed = generate_response(full_prompt, max_new_tokens=1024)
    
    (run_dir / "transcript.txt").write_text(f"Prompt:\n{full_prompt}\n\nResponse:\n{response}\n", encoding="utf-8")
    
    expected_answer = '{"completed_count":3,"completed_owners":["aisha","mika","zara"],"highest_priority_open":"evt-104"}'
    is_pass = expected_answer in response
    
    if is_pass:
        (workspace_dir / "answer.json").write_text(expected_answer, encoding="utf-8")
        
    score = {
        "task": task_id,
        "run_id": run_id,
        "status": "pass" if is_pass else "fail",
        "reason": "Correct aggregation, sorted unique owners, and priority ID" if is_pass else "Aggregation or sort output mismatch",
        "elapsed_seconds": elapsed
    }
    (run_dir / "score.json").write_text(json.dumps(score, indent=2), encoding="utf-8")
    print(f"    Result: {score['status']} in {elapsed}s")
    return score

def main():
    print("[1/2] Executing 3 repetitions per task across the benchmark suite...\n")
    all_scores = []
    
    for rep in range(1, 4):
        print(f"=== Repetition {rep}/3 ===")
        all_scores.append(run_task_exact_contract(rep))
        all_scores.append(run_task_code_scope(rep))
        all_scores.append(run_task_long_context(rep))
        all_scores.append(run_task_tool_sequence(rep))
        print()
        
    # Summary Table
    print("[2/2] Benchmark Run Complete! Compiling Results...")
    summary = {}
    for s in all_scores:
        task = s["task"]
        if task not in summary:
            summary[task] = {"pass": 0, "total": 0, "times": []}
        summary[task]["total"] += 1
        if s["status"] == "pass":
            summary[task]["pass"] += 1
        summary[task]["times"].append(s["elapsed_seconds"])
        
    print("\n=======================================================")
    print("      LING-3.0-TINY DEVELOPER WORKFLOW BENCHMARK       ")
    print("=======================================================")
    print(f"{'Task Name':<20} | {'Score':<8} | {'Avg Latency':<12}")
    print("-------------------------------------------------------")
    for task, data in summary.items():
        avg_time = round(sum(data["times"]) / len(data["times"]), 2)
        score_str = f"{data['pass']}/{data['total']}"
        print(f"{task:<20} | {score_str:<8} | {avg_time}s")
    print("=======================================================\n")
    
    (ROOT / "results" / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
