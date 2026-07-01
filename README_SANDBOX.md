---
title: Redrob AI Recruiter — Offline Ranking Demo
emoji: 🏆
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: "4.0.0"
app_file: app.py
pinned: true
license: mit
---

# 🏆 Redrob AI Recruiter — Offline Ranking Demo

> **Redrob "India Runs Data & AI Challenge" — Official Sandbox**

This Space demonstrates the **offline ranking phase** of the Redrob AI Recruiter pipeline.

## What This Demonstrates

The full pipeline has two stages:

1. **Precomputation** *(~56 minutes, completed offline)*
   - FAISS CPU vector index over 100,000 candidates
   - RecruiterAgent evaluates Top-500 (LLM-based)
   - CriticAgent adversarially reviews Top-100 (LLM-based)
   - All results cached atomically to `output/checkpoints/`

2. **Offline Ranking** *(this demo, < 1 second)*
   - Loads precomputed evaluations from disk
   - Fuses scores via `WeightedFusionStrategy`
   - Generates `submission.csv` (100 rows)
   - **Zero API calls. Zero LLMs. Zero network. CPU-only.**

## Score Fusion Formula

```
final_score = (semantic × 0.20) + (behaviour × 0.20) + (llm_adjusted × 0.60)
```

## Official Compliance

| Constraint | Status |
|---|---|
| Runtime ≤ 5 minutes | ✅ ~0.02 seconds |
| CPU only | ✅ No GPU used |
| RAM ≤ 16 GB | ✅ ~48 MB peak |
| No network during ranking | ✅ Fully offline |
| No LLM calls during ranking | ✅ Pre-cached evaluations |
| Exactly 100 candidate rows | ✅ |
| Official validator passes | ✅ |

## How to Run Locally

```bash
# Install dependencies
uv sync

# Run offline ranking
uv run python scripts/rank.py --output-dir output

# Validate
uv run python data/raw/validate_submission.py output/submission.csv

# Launch sandbox
uv run python app.py
```
