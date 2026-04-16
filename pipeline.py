#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   THE ASLIYAT — Automated Meme Pipeline v2.0              ║
║   Expectation vs Reality Generator for Instagram          ║
║                                                           ║
║   Flow:                                                    ║
║     Phase 0: Research trending topics                      ║
║     Phase 1: Generate 10 concepts → score → pick best     ║
║     Phase 2: AI-driven image search + download             ║
║     Phase 3: Assemble 2-panel meme template                ║
║     Phase 4: QA vision check + auto-retry                  ║
║                                                           ║
║   Usage:                                                   ║
║     python pipeline.py                                     ║
║     python pipeline.py --topic "gym life"                  ║
║     python pipeline.py --topic "Monday morning"            ║
║     python pipeline.py --no-research                       ║
║     python pipeline.py --headless false                    ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    OUTPUT_DIR, ASSETS_DIR, LOG_FILE, SAVE_LOG, BRAND_NAME, INSTA_HANDLE
)
from llm import get_llm
from research import refine_topic_with_research
from content import run_content_pipeline
from images import run_image_pipeline
from template import assemble_meme
from qa import qa_check, format_qa_report, run_qa_with_retry


def ensure_dirs():
    """Create required directories."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    (ASSETS_DIR / "fonts").mkdir(exist_ok=True)


def save_generation_log(result: dict):
    """Save generation history to log file."""
    if not SAVE_LOG:
        return

    logs = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, "r") as f:
                logs = json.load(f)
        except:
            logs = []

    logs.append({
        "timestamp": datetime.now().isoformat(),
        **result
    })

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2, default=str)


def print_banner():
    """Print the pipeline banner."""
    print("""
╔════════════════════════════════════════╗
║                                         ║
║   THE ASLIYAT  •  Meme Pipeline v2.0    ║
║   Expectation vs Reality Generator      ║
║                                         ║
╚════════════════════════════════════════╝
""")


def run(topic: str = None, no_research: bool = False):
    """
    Main pipeline runner.

    Args:
        topic: Optional topic hint. If None, AI picks trending topic.
        no_research: Skip research phase if True.
    """
    print_banner()
    start_time = time.time()

    ensure_dirs()

    # ── Initialize LLM ─────────────────────────────────────
    print("🧠 Initializing AI providers...")
    try:
        llm = get_llm()
    except Exception as e:
        print(f"❌ Failed to initialize AI: {e}")
        print("   Please set up Groq API key or Ollama. See README.md for help.")
        return None

    # ── Phase 0: Research ──────────────────────────────────
    if not no_research:
        print("\n" + "="*50)
        print("  PHASE 0 — TRENDING TOPIC RESEARCH")
        print("="*50)
        topic = refine_topic_with_research(topic)
    else:
        print("\n  ℹ Research skipped (--no-research flag)")

    # ── Phase 1: Content Generation ────────────────────────
    print("\n" + "="*50)
    print("  PHASE 1 — CONTENT GENERATION")
    print("="*50)
    best_meme, queries = run_content_pipeline(topic)

    print(f"\n  ✅ FINAL MEME SELECTED:")
    print(f"     Topic: {topic or 'AI-chosen'}")
    print(f"     EXPECTATION → {best_meme['expectation_text']}")
    print(f"     THE ASLIYAT → {best_meme['reality_text']}")

    # ── Phase 2: Image Search & Download ───────────────────
    print("\n" + "="*50)
    print("  PHASE 2 — IMAGE SEARCH & DOWNLOAD")
    print("="*50)
    exp_path, real_path = run_image_pipeline(queries, str(OUTPUT_DIR))

    # ── Phase 3: Template Assembly ─────────────────────────
    print("\n" + "="*50)
    print("  PHASE 3 — MEME ASSEMBLY")
    print("="*50)
    ts = int(time.time())
    out_path = str(OUTPUT_DIR / f"asliyat_{ts}.jpg")
    assemble_meme(best_meme, exp_path, real_path, out_path)

    # ── Phase 4: QA Check ──────────────────────────────────
    print("\n" + "="*50)
    print("  PHASE 4 — QA VISION CHECK")
    print("="*50)

    # Use simple QA (not retry loop) for cleaner output
    qa_result = qa_check(out_path)
    print(format_qa_report(qa_result))

    # ── Final Summary ──────────────────────────────────────
    elapsed = time.time() - start_time
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)

    print("\n" + "="*50)
    print("  🎉 PIPELINE COMPLETE")
    print("="*50)
    print(f"  📁 Output: {out_path}")
    print(f"  ⏱  Time: {mins}m {secs}s")
    print(f"  📊 QA Score: {qa_result.get('engagement_score', '?')}/10")
    print(f"\n  → Review the image and post manually on Instagram")
    print(f"  → Add trending audio/music in the Instagram app")
    print(f"  → Use relevant hashtags: #theasliyat #expectationvsreality #memes")
    print()

    # ── Save log ───────────────────────────────────────────
    result = {
        "topic": topic,
        "meme": best_meme,
        "queries": queries,
        "expectation_image": exp_path,
        "reality_image": real_path,
        "output": out_path,
        "qa": qa_result,
        "time_seconds": round(elapsed, 1),
    }
    save_generation_log(result)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="THE ASLIYAT — Automated Meme Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pipeline.py                           AI picks trending topic
  python pipeline.py --topic "gym life"        Use specific topic
  python pipeline.py --topic "exam night"      Exam season meme
  python pipeline.py --topic "marriage"        Marriage pressure meme
  python pipeline.py --no-research             Skip research, use topic directly
  python pipeline.py --headless false          Show browser while searching
        """
    )
    parser.add_argument(
        "--topic", "-t",
        type=str, default=None,
        help="Topic hint for the meme (e.g., 'gym life', 'Monday morning')"
    )
    parser.add_argument(
        "--no-research", "-nr",
        action="store_true",
        help="Skip trending topic research phase"
    )

    args = parser.parse_args()
    run(topic=args.topic, no_research=args.no_research)


if __name__ == "__main__":
    main()
