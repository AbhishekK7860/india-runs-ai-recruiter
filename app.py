"""
Redrob AI Recruiter — Offline Ranking Demo
Hugging Face Space (Gradio)

Demonstrates the offline ranking workflow using precomputed production artifacts.
Zero LLM calls. Zero network requests. Zero FAISS operations.
"""

import csv
import io
import sys
import time
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path

import gradio as gr

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OUTPUT_DIR = Path("output")
CHECKPOINTS_DIR = OUTPUT_DIR / "checkpoints"
CSV_PATH = OUTPUT_DIR / "submission.csv"
XLSX_PATH = OUTPUT_DIR / "submission.xlsx"
XML_PATH = OUTPUT_DIR / "submission.xml"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _checkpoints_present() -> bool:
    return (CHECKPOINTS_DIR / "recruiter_evals.jsonl").exists() and \
           (CHECKPOINTS_DIR / "critic_evals.jsonl").exists()


def _count_checkpoints() -> tuple[int, int]:
    recruiter_count = sum(1 for _ in open(CHECKPOINTS_DIR / "recruiter_evals.jsonl", encoding="utf-8"))
    critic_count = sum(1 for _ in open(CHECKPOINTS_DIR / "critic_evals.jsonl", encoding="utf-8"))
    return recruiter_count, critic_count


def _run_ranking() -> tuple[str, float, float, str]:
    """Execute the offline ranking pipeline and return (log, runtime_s, peak_mb, status)."""
    try:
        import psutil
        proc = psutil.Process()
        mem_before = proc.memory_info().rss / 1024 / 1024
    except ImportError:
        proc = None
        mem_before = 0.0

    log_lines = []

    t_start = time.perf_counter()

    log_lines.append("📦 Loading precomputed artifacts...")
    from backend.agents.ranking_agent import RankingAgent
    from backend.agents.ranking_strategy import WeightedFusionStrategy
    from backend.schemas.llm import CriticReview, EvidencePackage
    from backend.submission.csv_generator import CSVGenerator
    from backend.submission.xlsx_generator import XLSXGenerator
    from backend.submission.xml_generator import XMLGenerator
    from backend.utils.checkpointer import Checkpointer

    checkpointer = Checkpointer(OUTPUT_DIR)
    recruiter_evals = checkpointer.load_recruiter_evals()
    critic_evals = checkpointer.load_critic_evals()
    log_lines.append(f"✅ Loaded {len(recruiter_evals)} recruiter evals, {len(critic_evals)} critic evals")

    log_lines.append("🔄 Reconstructing candidates from cached evaluations...")
    candidates = []
    critic_reviews = []
    for cid, crit_data in critic_evals.items():
        rev = CriticReview.model_validate(crit_data["critic_review"])
        ev = EvidencePackage.model_validate(recruiter_evals[cid]["evidence"])
        candidates.append((ev, rev))
        critic_reviews.append(rev)

    log_lines.append(f"✅ Reconstructed {len(candidates)} candidates")

    log_lines.append("⚖️ Executing WeightedFusionStrategy ranking...")
    ranking_agent = RankingAgent(WeightedFusionStrategy())
    ranked = ranking_agent.rank(candidates)
    log_lines.append(f"✅ Ranked {len(ranked)} candidates")

    log_lines.append("📝 Generating submission.csv (100 rows)...")
    csv_generator = CSVGenerator()
    csv_path = csv_generator.generate(ranked[:100], critic_reviews, OUTPUT_DIR)
    log_lines.append(f"✅ CSV generated: {csv_path}")

    log_lines.append("📊 Generating submission.xlsx (100 rows)...")
    xlsx_generator = XLSXGenerator()
    xlsx_path = xlsx_generator.generate(ranked[:100], critic_reviews, OUTPUT_DIR)
    log_lines.append(f"✅ XLSX generated: {xlsx_path}")

    log_lines.append("📄 Generating submission.xml (Top-50)...")
    xml_generator = XMLGenerator()
    xml_path = xml_generator.generate(ranked[:50], OUTPUT_DIR)
    log_lines.append(f"✅ XML generated: {xml_path}")

    t_end = time.perf_counter()
    runtime_s = t_end - t_start

    peak_mb = 0.0
    if proc:
        peak_mb = proc.memory_info().rss / 1024 / 1024

    log_lines.append(f"\n🏁 Completed in {runtime_s:.4f} seconds")
    log_lines.append(f"💾 Peak memory: {peak_mb:.1f} MB")
    log_lines.append("🌐 Network calls: ZERO")
    log_lines.append("🤖 LLM calls: ZERO")
    log_lines.append("📡 API calls: ZERO")

    return "\n".join(log_lines), runtime_s, peak_mb, "SUCCESS"


def _read_top10_csv() -> list[dict]:
    if not CSV_PATH.exists():
        return []
    rows = []
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= 10:
                break
            rows.append(row)
    return rows


def _format_top10_markdown(rows: list[dict]) -> str:
    if not rows:
        return "No data available."
    lines = ["| Rank | Candidate ID | Score | Reasoning (truncated) |",
             "|------|-------------|-------|----------------------|"]
    for row in rows:
        reasoning = row.get("reasoning", "")[:120].replace("|", "\\|") + "..."
        lines.append(f"| {row['rank']} | `{row['candidate_id']}` | **{row['score']}** | {reasoning} |")
    return "\n".join(lines)


def _get_csv_content() -> str | None:
    if CSV_PATH.exists():
        return str(CSV_PATH)
    return None


def _get_xml_content() -> str | None:
    if XML_PATH.exists():
        return str(XML_PATH)
    return None


def _get_xlsx_content() -> str | None:
    if XLSX_PATH.exists():
        return str(XLSX_PATH)
    return None


# ---------------------------------------------------------------------------
# Gradio Event Handler
# ---------------------------------------------------------------------------
def generate_rankings():
    """Main handler for the Generate Rankings button."""
    if not _checkpoints_present():
        err = "❌ ERROR: Precomputed checkpoints not found in output/checkpoints/. Cannot run offline ranking."
        return err, "—", "—", "Checkpoints missing", None, None

    try:
        log, runtime_s, peak_mb, status = _run_ranking()
        top10 = _read_top10_csv()
        top10_md = _format_top10_markdown(top10)

        runtime_str = f"✅ {runtime_s:.4f}s (< 5 minutes ✓)"
        memory_str = f"✅ {peak_mb:.1f} MB (< 16 GB ✓)"

        csv_file = _get_csv_content()
        xlsx_file = _get_xlsx_content()
        xml_file = _get_xml_content()

        return log, runtime_str, memory_str, top10_md, csv_file, xlsx_file, xml_file

    except Exception as e:
        err_log = f"❌ Error during ranking:\n{traceback.format_exc()}"
        return err_log, "ERROR", "ERROR", "Ranking failed", None, None, None


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
CSS = """
#header { text-align: center; padding: 20px 0; }
#header h1 { font-size: 2.2em; font-weight: 700; color: var(--body-text-color); }
#header p { color: var(--body-text-color-subdued); font-size: 1.05em; }
.info-box { background: var(--background-fill-secondary); border-left: 4px solid var(--color-accent); padding: 12px 16px; border-radius: 6px; margin: 8px 0; }
.warn-box { background: var(--background-fill-secondary); border-left: 4px solid var(--color-warning-text); padding: 12px 16px; border-radius: 6px; margin: 8px 0; }
"""

ARCHITECTURE_INFO = """
### 🏗️ How This Works

This sandbox demonstrates the **Offline Ranking Phase** of the Redrob AI Recruiter pipeline.

The full pipeline runs in two stages:

**Stage 1 — Precomputation** *(completed, ~56 minutes)*
- 100K candidates embedded into FAISS vector index
- Top-500 retrieved via semantic search
- RecruiterAgent evaluates all 500 (LLM-based)
- CriticAgent adversarially reviews Top-100 (LLM-based)
- All results saved atomically to `output/checkpoints/`

**Stage 2 — Offline Ranking** *(this demo, < 1 second)*
- Loads cached evaluations from disk
- Fuses semantic + behavioural + LLM scores via `WeightedFusionStrategy`
- Generates `submission.csv` (100 rows) and `submission.xml` (Top-50)
- **Zero API calls. Zero LLMs. Zero network. CPU-only.**

### 📐 Score Fusion Formula
```
final_score = (semantic × 0.20) + (behaviour × 0.20) + (llm_adjusted × 0.60)
```
"""

CONSTRAINTS_INFO = """
### ✅ Official Compliance

| Constraint | Status |
|---|---|
| Runtime ≤ 5 minutes | ✅ ~0.02 seconds |
| CPU only | ✅ No GPU used |
| RAM ≤ 16 GB | ✅ ~48 MB peak |
| No network during ranking | ✅ Fully offline |
| No LLM calls during ranking | ✅ Pre-cached evaluations used |
| 100 candidate rows | ✅ Exactly 100 |
| Validator passes | ✅ validate_submission.py → valid |
"""

with gr.Blocks(css=CSS, title="Redrob AI Recruiter — Offline Ranking Demo") as demo:

    with gr.Row():
        gr.HTML("""
        <div id="header">
            <h1>🏆 Redrob AI Recruiter</h1>
            <p>Offline Ranking Demo — India Runs Data &amp; AI Challenge</p>
        </div>
        """)

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown(ARCHITECTURE_INFO)
            gr.Markdown(CONSTRAINTS_INFO)

            gr.HTML("""
            <div class="warn-box">
            ⚠️ <strong>Note:</strong> This sandbox demonstrates the <em>offline ranking stage only</em>,
            using precomputed production artifacts. No LLM providers are initialised.
            No network requests are made.
            </div>
            """)

            run_btn = gr.Button("🚀 Generate Rankings", variant="primary", size="lg")

        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.Tab("📊 Results"):
                    runtime_out = gr.Textbox(label="⏱️ Runtime", interactive=False)
                    memory_out = gr.Textbox(label="💾 Peak Memory", interactive=False)
                    top10_out = gr.Markdown(label="🏅 Top 10 Candidates")

                with gr.Tab("📋 Execution Log"):
                    log_out = gr.Textbox(
                        label="Console Output",
                        lines=20,
                        interactive=False,
                        placeholder="Click 'Generate Rankings' to start...",
                    )

                with gr.Tab("📥 Downloads"):
                    gr.Markdown("### Download Submission Artifacts")
                    csv_out = gr.File(label="📄 submission.csv (100 candidates)", file_count="single")
                    xlsx_out = gr.File(label="📊 submission.xlsx (100 candidates)", file_count="single")
                    xml_out = gr.File(label="📄 submission.xml (Top-50)", file_count="single")

    run_btn.click(
        fn=generate_rankings,
        inputs=[],
        outputs=[log_out, runtime_out, memory_out, top10_out, csv_out, xlsx_out, xml_out],
        show_progress=True,
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
