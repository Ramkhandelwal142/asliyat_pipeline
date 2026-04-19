#!/usr/bin/env python3
"""
THE ASLIYAT — Phase 2: Image Search & Download

FIX APPLIED (Critical Bug #1):
OLD BROKEN FLOW:
  Session 1: screenshots → close browser
  AI picks click_x, click_y from Session 1
  Session 2: open again → click those coords → WRONG IMAGE (results reordered!)

NEW CORRECT FLOW:
  Single session: load page → extract all image URLs from DOM →
  take screenshots → close browser → AI picks by INDEX →
  download directly by URL (no clicking, no second session)

For Bing specifically: the .iusc elements store full-size image URLs
in a JSON blob in their 'm' attribute. We extract these directly.
"""

import os, time, random, base64, re, json
from pathlib import Path
from urllib.parse import quote

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

import requests
from llm import get_llm, _img_to_b64
from config import (
    IMAGE_SEARCH_ENGINE, NUM_SCREENSHOTS, SCROLL_DISTANCE,
    HEADLESS_BROWSER, BROWSER_TIMEOUT, OUTPUT_DIR
)


def _build_search_url(query: str) -> str:
    """Build the image search URL with quality filters."""
    q = quote(query)
    if IMAGE_SEARCH_ENGINE == "bing":
        # filterui:photo-photo = photographs only (no illustrations/clipart)
        # filterui:aspect-square = closer to square crops, look better in meme panels
        return f"https://www.bing.com/images/search?q={q}&form=HDRSC2&first=1&qft=+filterui:photo-photo"
    else:
        return f"https://www.google.com/search?q={q}&tbm=isch"


def _extract_image_urls(page) -> list:
    """
    Extract full-size image URLs directly from the search results DOM.
    Bing stores full-size URLs in a JSON 'm' attribute on .iusc elements.
    This eliminates the need to click on images to find their URLs.
    Returns list of dicts: [{index, full_url, thumb_url}, ...]
    """
    try:
        if IMAGE_SEARCH_ENGINE == "bing":
            return page.evaluate("""
                () => {
                    const items = document.querySelectorAll('.iusc');
                    const results = [];
                    Array.from(items).slice(0, 25).forEach((el, i) => {
                        try {
                            const m = JSON.parse(el.getAttribute('m') || '{}');
                            const img = el.querySelector('img');
                            const full = m.murl || '';
                            const thumb = (img ? img.src : '') || m.turl || '';
                            if (full && full.startsWith('http')) {
                                results.push({
                                    index: i,
                                    full_url: full,
                                    thumb_url: thumb,
                                    title: m.t || ''
                                });
                            }
                        } catch(e) {}
                    });
                    return results;
                }
            """)
        else:
            # Google — thumbnails are base64 initially; full URL needs a click
            # We grab the largest src we can find from each result container
            return page.evaluate("""
                () => {
                    const imgs = document.querySelectorAll('img.rg_i, img.Q4LuWd, img.YQ4gaf');
                    return Array.from(imgs).slice(0, 25).map((img, i) => {
                        const src = img.getAttribute('data-src') || img.src || '';
                        return {
                            index: i,
                            full_url: src.startsWith('http') ? src : '',
                            thumb_url: src
                        };
                    }).filter(x => x.full_url);
                }
            """)
    except Exception as e:
        print(f"  ⚠ URL extraction failed: {e}")
        return []


def _take_screenshots(page, query: str) -> list:
    """Take multiple screenshots while scrolling through image search results."""
    screenshots = []
    time.sleep(1.5 + random.uniform(0.5, 1.0))
    screenshots.append(page.screenshot())

    for _ in range(NUM_SCREENSHOTS - 1):
        page.evaluate(f"window.scrollBy({{top: {SCROLL_DISTANCE}, behavior: 'smooth'}})")
        time.sleep(0.8 + random.uniform(0.3, 0.7))
        screenshots.append(page.screenshot())

    return screenshots


def _ask_vision_to_pick_by_index(screenshots: list, image_data: list, query: str, label: str) -> int:
    """
    Send screenshots to vision AI and ask it to pick the best image by INDEX.
    Returns integer index (0-based) mapped to image_data list.

    The AI sees the visual layout and picks which image number (position)
    looks best. We then map that to the actual URL from image_data.
    """
    llm = get_llm()
    n = len(image_data)

    if n == 0:
        return 0

    criteria = {
        "expectation": (
            "ASPIRATIONAL, cinematic, cool, clean — like a movie scene, hero moment, or dream scenario. "
            "Should make viewer think 'wish mera bhi aisa hota'. "
            "Prefer: clean composition, no text overlays, confident/polished look."
        ),
        "reality": (
            "RELATABLE, exhausted, done, funny, or authentically struggling. "
            "Prefer INDIAN FACES — they resonate far more with our audience. "
            "Think: tired office worker, confused student, overwhelmed desi guy. "
            "The viewer should think 'yeh toh main hoon bhai'."
        )
    }.get(label, "best quality, relevant to the search query")

    content = [
        {
            "type": "text",
            "text": f"""These are image search result screenshots for: "{query}"

I need the BEST image for the {label.upper()} panel of an Indian meme page (@the_asliyat).
There are {n} images available (numbered 0 to {n-1} in left-to-right, top-to-bottom order).

WHAT I NEED FOR {label.upper()}:
{criteria}

AVOID:
- Images with text overlays, watermarks, or logos from other pages
- Blurry or low-resolution images
- Stock photo watermarks (Getty, Shutterstock stamps)
- Images that don't clearly show what I need

Pick the single best image by its position number.

Return ONLY valid JSON:
{{
  "best_index": 2,
  "description": "what this image shows",
  "why": "why it fits the {label} panel perfectly",
  "confidence": 8
}}"""
        }
    ]

    for ss in screenshots:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{_img_to_b64(ss)}"}
        })

    try:
        result = llm.vision_json([{"role": "user", "content": content}], max_tokens=300)
        idx = int(result.get("best_index", 0))
        desc = result.get("description", "unknown")
        conf = result.get("confidence", "?")
        print(f"  🎯 AI chose index {idx}: \"{desc}\" (confidence: {conf}/10)")
        # Clamp to valid range
        return max(0, min(idx, n - 1))
    except Exception as e:
        print(f"  ⚠ Vision selection failed: {e}")
        return 0


def _download_from_url(url: str, save_path: str) -> bool:
    """Download an image directly from a URL."""
    if not url or not url.startswith("http"):
        return False
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.bing.com/" if IMAGE_SEARCH_ENGINE == "bing" else "https://www.google.com/",
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
        }
        r = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        if r.status_code == 200 and len(r.content) > 5000:
            content_type = r.headers.get("content-type", "")
            if "image" in content_type or any(url.lower().endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp")):
                with open(save_path, "wb") as f:
                    f.write(r.content)
                print(f"  ✓ Downloaded: {save_path} ({len(r.content) // 1024}KB)")
                return True
    except Exception as e:
        print(f"  ✗ Download error for {url[:60]}...: {e}")
    return False


def _create_placeholder(save_path: str, label: str):
    """Create a placeholder image if download fails."""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (560, 675), (25, 25, 25))
    d = ImageDraw.Draw(img)
    try:
        font_path = "C:/Windows/Fonts/arial.ttf"
        font = ImageFont.truetype(font_path, 28) if os.path.exists(font_path) else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
    d.text((20, 310), f"[{label}]", fill=(140, 140, 140), font=font)
    img.save(save_path)
    print(f"  ⚠ Created placeholder: {save_path}")


def search_and_download(query: str, label: str, out_dir: str) -> str:
    """
    Complete image search pipeline — SINGLE BROWSER SESSION.

    Flow:
    1. Open browser once
    2. Load search results
    3. Extract full-size image URLs directly from DOM (no clicking needed)
    4. Take scroll screenshots for visual AI review
    5. Close browser
    6. AI picks best image by index (not coordinates)
    7. Download directly from the URL at that index
    8. Fallback: try other URLs until one works

    Returns path to downloaded image.
    """
    if not HAS_PLAYWRIGHT:
        print(f"  ✗ Playwright not installed.")
        img_path = os.path.join(out_dir, f"{label}.jpg")
        _create_placeholder(img_path, label)
        return img_path

    print(f"\n  🔍 Searching images for '{label}' panel...")
    print(f"     Query: \"{query}\"")

    img_path = os.path.join(out_dir, f"{label}.jpg")
    search_url = _build_search_url(query)

    image_data = []
    screenshots = []

    # ── Single browser session ──────────────────────────────────────────
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS_BROWSER)
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = ctx.new_page()

        try:
            page.goto(search_url, wait_until="domcontentloaded", timeout=BROWSER_TIMEOUT * 1000)
        except Exception:
            try:
                page.goto(search_url, wait_until="load", timeout=BROWSER_TIMEOUT * 1000)
            except Exception as e:
                print(f"  ✗ Search page failed to load: {e}")
                browser.close()
                _create_placeholder(img_path, label)
                return img_path

        # Wait for images to render
        time.sleep(2 + random.uniform(0.3, 0.7))

        # Step 1: Extract URLs from DOM (before scrolling)
        image_data = _extract_image_urls(page)
        print(f"  📦 Extracted {len(image_data)} image URLs from DOM")

        # Step 2: Take screenshots while scrolling (for AI visual review)
        screenshots = _take_screenshots(page, query)

        browser.close()
    # ── Browser closed — now work with data we already have ─────────────

    print(f"  📸 Took {len(screenshots)} screenshots")

    if not image_data:
        print("  ⚠ No image URLs extracted — using placeholder")
        _create_placeholder(img_path, label)
        return img_path

    # Step 3: AI picks best image by index
    print(f"  🤖 AI analyzing for best {label} image...")
    best_index = _ask_vision_to_pick_by_index(screenshots, image_data, query, label)

    # Step 4: Download — try best choice first, then fallbacks
    success = False

    # Try AI's top pick
    if best_index < len(image_data):
        chosen = image_data[best_index]
        success = _download_from_url(chosen.get("full_url", ""), img_path)
        if not success:
            # Try thumbnail URL as backup
            success = _download_from_url(chosen.get("thumb_url", ""), img_path)

    # If AI's pick failed, try others in order of proximity
    if not success:
        print("  🔄 AI's top pick failed — trying other candidates...")
        tried = {best_index}
        # Try nearby indices first (best_index ± 1, ± 2, etc.)
        candidates = sorted(range(len(image_data)), key=lambda i: abs(i - best_index))
        for idx in candidates:
            if idx in tried:
                continue
            tried.add(idx)
            img_info = image_data[idx]
            success = _download_from_url(img_info.get("full_url", ""), img_path)
            if success:
                print(f"  ✓ Used fallback image at index {idx}")
                break
            # Small delay to avoid hammering
            time.sleep(0.5)

    if not success:
        print(f"  ⚠ All downloads failed — using placeholder")
        _create_placeholder(img_path, label)

    return img_path


def run_image_pipeline(queries: dict, out_dir: str) -> tuple:
    """
    Search and download both expectation and reality images.
    Returns: (expectation_image_path, reality_image_path)
    """
    os.makedirs(out_dir, exist_ok=True)

    exp_path = search_and_download(
        queries["expectation_query"],
        "expectation",
        out_dir,
    )

    time.sleep(1 + random.uniform(0.5, 1.0))

    real_path = search_and_download(
        queries["reality_query"],
        "reality",
        out_dir,
    )

    return exp_path, real_path
