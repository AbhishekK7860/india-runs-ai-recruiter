---
title: Redrob AI Recruiter — Offline Ranking Demo
emoji: 🏆
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 6.19.0
python_version: "3.12"
app_file: app.py
pinned: true
license: apache-2.0 
---

# 🏆 India Runs AI Recruiter

> **Redrob "India Runs Data & AI Challenge" — Official Hackathon Submission**
>
> A production-grade, multi-agent AI pipeline for semantic candidate retrieval and structured LLM-based ranking over 100,000 candidates.

---

## 📌 Project Overview

This repository implements a complete, end-to-end AI recruiting pipeline that:

1. **Embeds 100,000 candidate profiles** into a FAISS CPU vector index using `sentence-transformers`.
2. **Retrieves the top-500 semantic matches** using cosine similarity against the job description.
3. **Evaluates all 500 candidates** using a structured `RecruiterAgent` (LLM-based, with prompt injection defense and PII scrubbing).
4. **Deeply reviews the Top-100 candidates** using an adversarial `CriticAgent` designed to detect hallucinations and correct bias.
5. **Fuses scores deterministically** using a `WeightedFusionStrategy` combining semantic, behavioral, and LLM-adjusted scores.
6. **Produces a fully offline-reproducible submission** in under 1 second, with zero API dependencies at ranking time.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    PRECOMPUTATION PHASE                      │
│                  (scripts/run_pipeline.py)                   │
│                                                              │
│  Dataset (100K candidates)                                   │
│       │                                                      │
│       ▼                                                      │
│  DataPipeline ──► Pydantic validation + normalization        │
│       │                                                      │
│       ▼                                                      │
│  TextEncoder ──► sentence-transformers embeddings            │
│       │                                                      │
│       ▼                                                      │
│  FAISS CPU Index ──► 100K vectors (data/index/)              │
│       │                                                      │
│       ▼                                                      │
│  SemanticSearcher ──► Top-500 candidates retrieved           │
│       │                                                      │
│       ▼                                                      │
│  SecurityFilter ──► PII scrub + prompt injection defense     │
│       │                                                      │
│       ▼                                                      │
│  EvidenceBuilder ──► Structured evidence packages            │
│       │                                                      │
│       ▼                                                      │
│  RecruiterAgent ──► LLM evaluation of 500 candidates        │
│       │                                                      │
│       ▼                                                      │
│  CriticAgent ──► Adversarial review of Top-100              │
│       │                                                      │
│       ▼                                                      │
│  Checkpointer ──► Atomic JSONL checkpoint writes            │
│                   (output/checkpoints/)                      │
└──────────────────────────────────────────────────────────────┘
                           │
                 Cached Artifacts on Disk
                           │
┌──────────────────────────▼───────────────────────────────────┐
│                    OFFLINE RANKING PHASE                     │
│                    (scripts/rank.py)                         │
│                                                              │
│  Checkpointer.load_recruiter_evals()                         │
│  Checkpointer.load_critic_evals()                            │
│       │                                                      │
│       ▼                                                      │
│  EvidencePackage + CriticReview (Pydantic deserialization)   │
│       │                                                      │
│       ▼                                                      │
│  RankingAgent(WeightedFusionStrategy())                      │
│       │   score = 0.2×semantic + 0.2×behaviour + 0.6×llm    │
│       │                                                      │
│       ▼                                                      │
│  CSVGenerator ──► output/submission.csv (100 rows)           │
│  XMLGenerator ──► output/submission.xml (Top-50)             │
└──────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

| Feature | Description |
|---|---|
| **100K-scale FAISS retrieval** | CPU-only, sub-second vector search over entire dataset |
| **Structured LLM evaluation** | Pydantic-validated outputs; retry-on-failure; no hallucinations committed |
| **Adversarial Critic Agent** | Dedicated pass to correct recruiter over-scoring and bias |
| **Security Checkpoint** | PII scrubbing (SSNs, credit cards) + prompt injection detection before any LLM call |
| **Atomic Checkpointing** | Resume-safe JSONL writes; pipeline can be interrupted and resumed at any point |
| **Offline Ranking** | Sub-second, zero-network, zero-LLM final ranking from cached artifacts |
| **Deterministic Tie-Breaking** | Descending score, ascending candidate ID for reproducible results |
| **Official Validator Compliant** | Passes `validate_submission.py` with 100 rows, correct headers, UTF-8 |

---

## 🤖 AI Pipeline

### Score Fusion Formula

```
final_score = (semantic_score × 0.20)
            + (behaviour_score × 0.20)
            + (llm_adjusted_score × 0.60)
```

- **Semantic Score**: FAISS cosine similarity (normalized 0–100)
- **Behaviour Score**: Deterministic quality signals from resume metadata (0–100)
- **LLM Adjusted Score**: `CriticAgent.adjusted_fit_score` — corrected from `RecruiterAgent.fit_score` (0–100)
- **Hallucination Penalty**: −10 points applied if `CriticAgent` flags hallucinated skills

### Security Architecture

Before any candidate text reaches an LLM:
1. **PII Scrubbing**: SSNs and credit card numbers are detected and removed; categories are logged but never forwarded.
2. **Prompt Injection Defense**: If the candidate text contains override instructions, the candidate is routed to human review and flagged — never evaluated by LLM.

---

## 📁 Repository Structure

```
india-runs-ai-recruiter/
├── backend/
│   ├── agents/                  # All AI agents
│   │   ├── ranking_agent.py     # Final fusion + sorting
│   │   ├── ranking_strategy.py  # WeightedFusionStrategy
│   │   ├── recruiter_agent.py   # LLM candidate evaluation
│   │   ├── critic_agent.py      # Adversarial hallucination review
│   │   ├── jd_analyst.py        # Job description extraction
│   │   └── security_filter.py   # PII + prompt injection defense
│   ├── embeddings/              # sentence-transformers encoder + cache
│   ├── retrieval/               # FAISS semantic searcher
│   ├── services/                # DataPipeline, EvidenceBuilder
│   ├── submission/              # CSVGenerator, XMLGenerator, validator
│   ├── reporting/               # Explainability report generator
│   ├── evaluation/              # Benchmark suite
│   └── utils/                   # Checkpointer, logger
├── configs/
│   └── prompts.yaml             # All LLM prompts (frozen)
├── data/
│   ├── raw/                     # Dataset, job description, validator
│   └── index/                   # FAISS index (154MB) + metadata
├── scripts/
│   ├── rank.py                  # ✅ Official offline reproduce command
│   ├── run_pipeline.py          # Full precomputation pipeline
│   ├── build_index.py           # FAISS index construction
│   └── ...                      # Development utilities
├── output/
│   ├── submission.csv           # ✅ Final submission (100 ranked candidates)
│   ├── submission.xml           # XML representation (Top-50)
│   ├── benchmark_report.json    # Pipeline latency metrics
│   ├── explainability_report.md # Per-candidate decision explanations
│   └── checkpoints/             # Immutable precomputed artifacts
│       ├── recruiter_evals.jsonl   # 500 recruiter evaluations
│       ├── critic_evals.jsonl      # 100 critic reviews
│       └── pipeline_state.json     # Execution fingerprint
├── submission_metadata.yaml     # ✅ Official submission metadata
├── pyproject.toml
└── README.md
```

---

## 🚀 Reproduction Guide

### Prerequisites

- Python 3.12+
- [`uv`](https://github.com/astral-sh/uv) package manager

```bash
pip install uv
```

### Installation

```bash
git clone <repo-url>
cd india-runs-ai-recruiter
uv sync
```

---

### Stage 1 — Precomputation *(Already Completed — Optional)*

> ⚠️ **This step is NOT required for reproduction.** The precomputed checkpoints are already in `output/checkpoints/`.

Precomputation takes approximately **56 minutes** and requires an active `OPENROUTER_API_KEY`.

```bash
cp .env.example .env
# Fill in your API key in .env

uv run python scripts/run_pipeline.py \
  --dataset "data/raw/candidates.jsonl" \
  --job-dir "data/raw" \
  --job-id "job_description" \
  --output-dir "output"
```

**What this does:**
- Normalizes and embeds all 100K candidates
- Retrieves Top-500 via FAISS semantic search
- Runs RecruiterAgent on all 500 (LLM calls, with checkpoint/resume)
- Runs CriticAgent on Top-100 (LLM calls, with checkpoint/resume)
- Saves all results atomically to `output/checkpoints/`

**Resume support:** If interrupted, re-run the same command. The pipeline automatically skips completed candidates and resumes from the last checkpoint.

---

### Stage 2 — Offline Ranking *(Official Reproduce Command)*

**This is the official reproduction command.** Runs completely offline in under 1 second.

```bash
uv run python scripts/rank.py --output-dir output
```

**What this does:**
- Loads cached evaluations from `output/checkpoints/`
- Fuses scores using `WeightedFusionStrategy`
- Generates `output/submission.csv` (100 rows)
- Generates `output/submission.xml` (Top-50)

**Guarantees:**
- ✅ Zero API calls
- ✅ Zero LLM inference
- ✅ Zero embedding generation
- ✅ Zero FAISS operations
- ✅ CPU-only
- ✅ Runtime < 5 minutes (measured: ~0.02 seconds internal logic)

---

### Stage 3 — Validation

```bash
uv run python data/raw/validate_submission.py output/submission.csv
# Expected output: "Submission is valid."
```

---

### Stage 4 — Sandbox Demo *(Optional)*

A Gradio web UI (`app.py`) is included to interactively demonstrate the offline ranking workflow:

```bash
uv run python app.py
# Opens at http://localhost:7860
```

The sandbox wraps `scripts/rank.py` exactly and exposes:
- A **Generate Rankings** button that executes the offline pipeline
- Execution log, runtime, and peak memory display
- Top-10 candidates table
- Download links for `submission.csv` and `submission.xml`

> **Live Sandbox:** [https://huggingface.co/spaces/Abhi786020/india-runs-ai-recruiter](https://huggingface.co/spaces/Abhi786020/india-runs-ai-recruiter)

**Note:** This sandbox demonstrates the offline ranking phase using precomputed production artifacts. It performs zero LLM, API, or network calls.

---

## 📊 Performance Metrics

| Metric | Value |
|---|---|
| **Offline ranking runtime** | ~0.02 seconds (internal) / ~1 second wall-clock |
| **Peak RAM (offline ranking)** | ~48 MB |
| **Precomputation time** | ~56 minutes |
| **Candidates in FAISS index** | 100,000 |
| **Recruiter evaluations completed** | 500 |
| **Critic evaluations completed** | 100 |
| **Final submission rows** | 100 |
| **Validator result** | ✅ Submission is valid |

---

## 💻 Hardware Requirements

### Offline Ranking (Stage 2 — Competition Evaluation)

| Resource | Requirement |
|---|---|
| **CPU** | Any modern CPU (no GPU required) |
| **RAM** | < 100 MB |
| **Disk** | < 10 MB (checkpoints only) |
| **Network** | None (fully offline) |
| **Runtime** | < 5 minutes |

### Precomputation (Stage 1 — Optional)

| Resource | Requirement |
|---|---|
| **CPU** | Multi-core recommended |
| **RAM** | ~4 GB (FAISS index + embeddings in memory) |
| **Disk** | ~2 GB (FAISS index + full dataset) |
| **Network** | Required (OpenRouter API) |
| **Runtime** | ~56 minutes |

---

## 🔒 Checkpoint System & Resume Capability

The pipeline uses an **atomic checkpoint system** for production fault tolerance:

- Every recruiter and critic evaluation is **atomically appended** to JSONL files before proceeding to the next candidate.
- `pipeline_state.json` records a fingerprint of the dataset hash, FAISS index hash, provider, model, and prompt configuration.
- On resume, **all fingerprints are verified**. If any differ (e.g., different model or modified prompts), the pipeline aborts to guarantee deterministic results.
- Completed candidates are loaded from cache; only incomplete candidates are sent to LLM calls.

---

## 🧪 Code Quality & Testing

```bash
# Run full test suite
uv run pytest

# Lint check
uv run ruff check .
```

The codebase enforces:
- **100% type-hinted** with Pydantic strict validation
- **Structured logging** via `structlog`
- **ruff** linting compliance

---

## 📋 Submission Artifacts

| File | Description |
|---|---|
| `output/submission.csv` | **Primary submission** — 100 ranked candidates |
| `output/submission.xml` | XML format — Top-50 candidates |
| `output/explainability_report.md` | Per-candidate reasoning explanations |
| `output/benchmark_report.json` | Pipeline latency and performance metrics |
| `submission_metadata.yaml` | Official hackathon metadata |

---

## 🔮 Key Architecture Decisions

**Why FAISS CPU instead of GPU?**
GPU inference is prohibited during the ranking step. The FAISS CPU index achieves sub-second retrieval over 100K vectors with < 200MB memory, satisfying both constraints.

**Why a Critic Agent?**
LLMs systematically over-score candidates. The Critic Agent provides a dedicated adversarial pass to reduce hallucinated skill claims and correct inflated scores before final fusion.

**Why split Precomputation and Offline Ranking?**
To strictly satisfy the "≤5 minute, no network, CPU-only" ranking constraint while still leveraging the full power of LLM evaluation during precomputation.

**Why atomic checkpoints?**
Production resilience. A 56-minute pipeline must survive network timeouts, API rate limits, and machine restarts without losing completed work or duplicating expensive LLM calls.
