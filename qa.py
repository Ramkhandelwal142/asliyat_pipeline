#!/usr/bin/env python3
"""
THE ASLIYAT — Phase 4: QA Check
Vision AI reviews the assembled meme for quality.
Auto-retry loop if quality doesn't meet standards.
"""

import json, os
from llm import get_llm, _img_to_b64
from config import QA_MIN_SCORE, QA_AUTO_RETRY, MAX_QA_RETRIES


def qa_check(image_path: str) -> dict:
    """
    Run QA vision check on the assembled meme.
    Returns dict with scores and pass/fail status.
    """
    print("\n  🔎 PHASE 4 — QA Vision Check...")

    llm = get_llm()

    vision_msg = [{
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{_img_to_b64(image_path)}"}
            },
            {
                "type": "text",
                "text": """You are a QUALITY ASSURANCE reviewer for @the_asliyat Instagram meme page.
You have EXACT STANDARDS for what gets posted. Review this meme ruthlessly.

CHECK THESE CRITERIA:
1. **text_readable** — Is all text clearly readable? Any overlap with image? Font too small?
2. **images_relevant** — Do the images match the text? Expectation image looks aspirational? Reality image looks relatable?
3. **branding_visible** — Is "THE ASLIYAT" in gold clearly visible? Is logo visible? Is @the_asliyat watermark readable?
4. **layout_clean** — Is the layout clean? Gold separator visible? Proper spacing? No visual clutter?
5. **emotional_impact** — Will this make someone stop scrolling? Does it trigger an emotion?
6. **hinglish_natural** — Does the Hindi-English mix feel natural, like how real people talk?

RATE overall engagement_score from 1-10 (10 = guaranteed viral).

Return ONLY valid JSON:
{
  "passed": true,
  "text_readable": true,
  "images_relevant": true,
  "branding_visible": true,
  "layout_clean": true,
  "emotional_impact": true,
  "hinglish_natural": true,
  "engagement_score": 8,
  "issues": [],
  "fix_suggestions": [],
  "verdict": "Ready to post — this will go viral"
}"""
            }
        ]
    }]

    try:
        result = llm.vision_json(vision_msg, max_tokens=500)

        # Ensure all fields exist
        result.setdefault("passed", True)
        result.setdefault("engagement_score", 5)
        result.setdefault("issues", [])
        result.setdefault("verdict", "Unknown")

        return result
    except Exception as e:
        print(f"  ⚠ QA vision failed: {e}")
        return {
            "passed": True,
            "engagement_score": 0,
            "issues": [f"QA error: {e}"],
            "verdict": "Could not analyze — review manually"
        }


def run_qa_with_retry(image_path: str, generate_callback) -> dict:
    """
    Run QA check with auto-retry loop.
    If QA fails and AUTO_RETRY is enabled, regenerates with feedback.

    Args:
        image_path: Path to assembled meme image
        generate_callback: Function to call for regeneration (returns new image_path)

    Returns: Final QA result dict
    """
    qa_result = qa_check(image_path)

    if not QA_AUTO_RETRY or qa_result.get("passed", True):
        return qa_result

    # QA failed — retry loop
    for attempt in range(1, MAX_QA_RETRIES + 1):
        print(f"\n  🔄 QA Failed — Retry {attempt}/{MAX_QA_RETRIES}")
        print(f"     Issues: {', '.join(qa_result.get('issues', []))}")
        print(f"     Suggestions: {', '.join(qa_result.get('fix_suggestions', ['regenerate']))}")

        # Generate new meme with QA feedback
        new_image_path = generate_callback(qa_result)
        if not new_image_path or not os.path.exists(new_image_path):
            print("  ⚠ Regeneration failed, keeping current image")
            break

        # Run QA again
        qa_result = qa_check(new_image_path)
        if qa_result.get("passed", True):
            print(f"  ✅ Retry successful!")
            # Update the image path reference
            image_path = new_image_path
            break

    return qa_result, image_path


def format_qa_report(qa_result: dict) -> str:
    """Format QA result for console output."""
    score = qa_result.get("engagement_score", "?")
    passed = qa_result.get("passed", False)
    verdict = qa_result.get("verdict", "Unknown")

    status = "✅ PASSED" if passed else "⚠ REVIEW NEEDED"
    report = f"  {status}  |  Engagement: {score}/10"
    report += f"\n  Verdict: {verdict}"

    if qa_result.get("issues"):
        report += f"\n  Issues: {', '.join(qa_result['issues'])}"
    if qa_result.get("fix_suggestions"):
        report += f"\n  Fixes: {', '.join(qa_result['fix_suggestions'])}"

    return report
