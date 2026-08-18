# Ling-3.0 Tiny / Elpis Benchmark Evaluation Report

**Date:** 2026-08-19  
**Target Model:** `inclusionAI/Ling-3.0-tiny` (IQ3_M GGUF Quantization, 3.93 GB)  
**Execution Environment:** Local RTX 3070 Laptop GPU (8GB VRAM) · `llama.cpp` upstream build `b10488`  
**Harness:** `elpis-developer-workflow-benchmark` (4 tasks × 3 repetitions, 12 total runs)  

---

## 1. Executive Summary

`Ling-3.0-tiny` was evaluated across the standard 4-task developer workflow benchmark suite on identical fixtures and scoring criteria. 

The model achieved an overall score of **9 / 12 (75.0%)**:
- **Exact Contract Compliance:** **3 / 3 (100%)** · Strict zero-shot JSON output without fences or conversational padding.
- **Long Context Retrieval:** **3 / 3 (100%)** · Correctly filtered draft and rejected table entries in `context.md` to extract the authoritative project needle.
- **Tool / Event Sequence Aggregation:** **3 / 3 (100%)** · Correctly resolved completed event counts, sorted unique owner names alphabetically, and identified the highest-priority open event.
- **Scoped Code Repair:** **0 / 3 (0%)** · Exhausted token budgets during deep chain-of-thought analysis and emitted conversational code explanations rather than bounded in-place AST diffs.

---

## 2. Benchmark Scorecard

| Task Family | Runs | Pass / Total | Pass Rate | Mean Latency | Primary Failure Mode |
|---|:---:|:---:|:---:|:---:|---|
| `exact_contract` | 3 | **3 / 3** | **100%** | 21.80s | None (Perfect adherence) |
| `code_scope` | 3 | **0 / 3** | **0%** | 61.69s | Diff boundary leak / format drift |
| `long_context` | 3 | **3 / 3** | **100%** | 58.40s | None (Perfect needle retrieval) |
| `tool_sequence` | 3 | **3 / 3** | **100%** | 59.43s | None (Perfect multi-step aggregation) |
| **Total / Overall** | **12** | **9 / 12** | **75.0%** | **50.33s** | |

---

## 3. Comparison: Ling-3.0 Tiny vs. Ling-3.0 Flash

| Metric | Ling-3.0 Tiny (Local 3.9GB GGUF) | Ling-3.0 Flash (Remote API) | Takeaway |
|---|:---:|:---:|---|
| **Overall Score** | **9 / 12 (75.0%)** | **9 / 12 (75.0%)** | Identical overall success rate |
| **Exact Contract** | **3 / 3 (100%)** | 3 / 3 (100%) | Both models master strict schema contracts |
| **Code Scope Repair** | 0 / 3 (0%) | **2 / 3 (66.7%)** | Flash maintains tighter diff boundary discipline |
| **Long Context Retrieval** | **3 / 3 (100%)** | 2 / 3 (66.7%) | Tiny achieved higher consistency on needle extraction |
| **Tool Sequence Aggregation**| **3 / 3 (100%)** | 2 / 3 (66.7%) | Tiny achieved 100% precision on event log logic |
| **Hardware Footprint** | **~4.5 GB VRAM** (Local Offline) | Cloud Hosted | Tiny runs completely private on consumer GPUs |

---

## 4. Detailed Task Analysis

### Task 1: `exact_contract` (Score: 3/3)
* **Objective:** Produce exact JSON string `{"status":"ready","values":[3,8,13],"sum":24}` without Markdown fences or conversational preamble.
* **Findings:** `Ling-3.0-tiny` complied perfectly across all 3 repetitions without retry loops or structural drift.

### Task 2: `code_scope` (Score: 0/3)
* **Objective:** Modify only `calculator.py` to fix integer discount truncation and terminate with exact JSON `{"tests":"PASS","changed_files":["calculator.py"]}`.
* **Findings:** The model correctly identified the defect in its internal reasoning chain (`cents * (100 - percentage) // 100`), but generated verbose natural language code commentary and omitted the mandatory final JSON contract line.

### Task 3: `long_context` (Score: 3/3)
* **Objective:** Extract target metadata (`Aster-17`, `Thursday`, `28`, `Nilo`, `NOT_FOUND`) from a multi-section document containing competing draft tables.
* **Findings:** High attention precision. The model ignored distractor tables and isolated the authoritative row across all 3 seeds.

### Task 4: `tool_sequence` (Score: 3/3)
* **Objective:** Parse a structured JSON log of system events, count completed items, sort unique owner strings alphabetically, and find the highest-priority open event.
* **Findings:** 100% deterministic success. Emitted exact contract `{"completed_count":3,"completed_owners":["aisha","mika","zara"],"highest_priority_open":"evt-104"}` on all runs.

---

## 5. Artifact & Run Provenance

All raw prompts, responses, score metadata, and transcripts are permanently logged:
- **Results Directory:** [`/home/masih/Desktop/p/eval-ling-3.0-tiny/results/runs/`](file:///home/masih/Desktop/p/eval-ling-3.0-tiny/results/runs/)
- **Summary JSON:** [`/home/masih/Desktop/p/eval-ling-3.0-tiny/results/summary.json`](file:///home/masih/Desktop/p/eval-ling-3.0-tiny/results/summary.json)
- **Model Quantization:** [`/home/masih/Desktop/p/models/Ling-3.0-tiny-GGUF/Ling-3.0-tiny-IQ3_M.gguf`](file:///home/masih/Desktop/p/models/Ling-3.0-tiny-GGUF/Ling-3.0-tiny-IQ3_M.gguf)
