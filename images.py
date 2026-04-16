#!/usr/bin/env python3
"""
THE ASLIYAT — Phase 2: Image Search & Download
Opens Google/Bing → takes screenshots while scrolling → AI picks best → downloads it.
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


def _take_screenshots(page, query: str) -> list:
    """Take multiple screenshots while scrolling through image search results."""
    screenshots = []

    # First screenshot before any scroll
    time.sleep(1.5 + random.uniform(0.5, 1.0))
    screenshots.append(page.screenshot())

    for i in range(NUM_SCREENSHOTS - 1):
        # Smooth scroll
        page.evaluate(f"window.scrollBy({{top: {SCROLL_DISTANCE}, behavior: 'smooth'}})")
        time.sleep(0.8 + random.uniform(0.3, 0.7))
        screenshots.append(page.screenshot())

    return screenshots


def _ask_vision_to_pick(screenshots: list, query: str, label: str) -> dict:
    """
    Send screenshots to vision AI and ask it to pick the best image.
    Returns dict with click coordinates and description.
    """
    llm = get_llm()

    # Build vision message with all screenshots
    content = [
        {
            "type": "text",
            "text": f"""These are Google Image search result screenshots for: "{query}"
I need ONE image for the {label.upper()} panel of an Indian meme (@the_asliyat).

INSTRUCTIONS:
1. Look at ALL {len(screenshots)} screenshots carefully
2. Find the SINGLE BEST image that matches the search intent
3. The image should be: high quality, no watermarks, no text overlays, clearly visible

Tell me EXACTLY where to click to select this image:
- Which screenshot number (0-{len(screenshots)-1})
- Approximate click coordinates (x, y) on a 1280×900 viewport
- Describe the image you chose

Return ONLY valid JSON:
{{
  "best_screenshot": 0,
  "click_x": 320,
  "click_y": 220,
  "image_description": "description of the chosen image",
  "confidence": 8,
  "reason": "why this image is the best fit"
}}"""
        }
    ]

    for ss in screenshots:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{_img_to_b64(ss)}"}
        })

    try:
        result = llm.vision_json([{"role": "user", "content": content}], max_tokens=600)
        return result
    except Exception as e:
        print(f"  ⚠ Vision selection failed: {e}")
        return {"click_x": 300, "click_y": 250, "best_screenshot": 0, "image_description": "fallback"}


def _download_chosen_image(query: str, click_x: int, click_y: int, save_path: str) -> bool:
    """
    Open image search again, click the chosen position, and download the full-size image.
    Returns True if successful.
    """
    if not HAS_PLAYWRIGHT:
        print("  ⚠ Playwright not installed — skipping image download")
        return False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS_BROWSER)
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = ctx.new_page()

        # Track image downloads
        downloaded_images = []

        def handle_response(response):
            ct = response.headers.get("content-type", "")
            if "image" in ct and response.url.startswith("http"):
                downloaded_images.append(response.url)

        page.on("response", handle_response)

        if IMAGE_SEARCH_ENGINE == "bing":
            url = f"https://www.bing.com/images/search?q={quote(query)}&form=HDRSC2&first=1&qft=+filterui:photo-photo"
        else:
            # Google Images with filter for photos only
            url = f"https://www.google.com/search?q={quote(query)}&tbm=isch&tbs=sur:f&safe=off"

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=BROWSER_TIMEOUT * 1000)
        except:
            try:
                page.goto(url, wait_until="load", timeout=BROWSER_TIMEOUT * 1000)
            except Exception as e:
                print(f"  ⚠ Page load timeout: {e}")
                browser.close()
                return False

        time.sleep(2 + random.uniform(0.5, 1.0))

        # Click on the chosen image
        page.mouse.click(click_x, click_y)
        time.sleep(2.5)

        img_url = None

        # Try Google's full-size image preview
        if IMAGE_SEARCH_ENGINE == "google":
            try:
                # Google shows a larger preview on click
                el = page.query_selector("img.sFlh5c") or page.query_selector("img.iPVvYb")
                if el:
                    src = el.get_attribute("src")
                    if src and src.startswith("http"):
                        img_url = src
            except:
                pass

            if not img_url:
                # Try the "View image" / "Visit" button
                try:
                    links = page.query_selector_all("a")
                    for link in links:
                        href = link.get_attribute("href") or ""
                        if "gstatic" in href or "lh3.googleusercontent" in href:
                            img_url = href
                            break
                except:
                    pass

        if not img_url:
            # Try Bing's preview panel
            try:
                el = page.query_selector("img.mimg") or page.query_selector(".mainImage img")
                if el:
                    src = el.get_attribute("src")
                    if src and src.startswith("http"):
                        img_url = src
            except:
                pass

        # Last resort: pick largest downloaded image
        if not img_url and downloaded_images:
            img_url = max(downloaded_images, key=len)

        browser.close()

    # Download the image file
    if img_url:
        try:
            r = requests.get(
                img_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                timeout=15,
                allow_redirects=True,
            )
            if r.status_code == 200 and len(r.content) > 5000:
                with open(save_path, "wb") as f:
                    f.write(r.content)
                print(f"  ✅ Downloaded: {save_path} ({len(r.content)//1024}KB)")
                return True
        except Exception as e:
            print(f"  ⚠ Download error: {e}")

    return False


def _create_placeholder(save_path: str, label: str):
    """Create a placeholder image if download fails."""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (560, 675), (25, 25, 25))
    d = ImageDraw.Draw(img)
    # Try to use a better font
    try:
        # Fallback for Windows
        font_path = "C:/Windows/Fonts/arial.ttf"
        if os.path.exists(font_path):
            font = ImageFont.truetype(font_path, 28)
        else:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    d.text((20, 310), f"[{label}]", fill=(140, 140, 140), font=font)
    img.save(save_path)
    print(f"  ⚠ Created placeholder: {save_path}")


def search_and_download(query: str, label: str, out_dir: str) -> str:
    """
    Complete image search pipeline:
    1. Open search engine
    2. Take scroll screenshots
    3. AI picks best image
    4. Download the chosen image
    Returns path to downloaded image.
    """
    if not HAS_PLAYWRIGHT:
        print(f"  ⚠ Playwright not installed. Install with: pip install playwright && playwright install chromium")
        img_path = os.path.join(out_dir, f"{label}.jpg")
        _create_placeholder(img_path, label)
        return img_path

    print(f"\n  🔎 Searching images for '{label}' panel...")
    print(f"     Query: \"{query}\"")

    screenshots = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS_BROWSER)
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = ctx.new_page()

        if IMAGE_SEARCH_ENGINE == "bing":
            url = f"https://www.bing.com/images/search?q={quote(query)}&form=HDRSC2&first=1&qft=+filterui:photo-photo"
        else:
            url = f"https://www.google.com/search?q={quote(query)}&tbm=isch&tbs=sur:f&safe=off"

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=BROWSER_TIMEOUT * 1000)
        except:
            try:
                page.goto(url, wait_until="load", timeout=BROWSER_TIMEOUT * 1000)
            except Exception as e:
                print(f"  ⚠ Search page failed to load: {e}")
                browser.close()
                img_path = os.path.join(out_dir, f"{label}.jpg")
                _create_placeholder(img_path, label)
                return img_path

        screenshots = _take_screenshots(page, query)
        browser.close()

    print(f"  📸 Took {len(screenshots)} screenshots")

    # Ask Vision AI to pick the best image
    print(f"  🤖 AI analyzing screenshots for {label} image...")
    vision = _ask_vision_to_pick(screenshots, query, label)

    cx = vision.get("click_x", 300)
    cy = vision.get("click_y", 250)
    desc = vision.get("image_description", "unknown")
    conf = vision.get("confidence", "?")

    print(f"  🎯 AI chose: \"{desc}\" (confidence: {conf}/10)")

    # Download the chosen image
    img_path = os.path.join(out_dir, f"{label}.jpg")
    success = _download_chosen_image(query, cx, cy, img_path)

    if not success:
        # Retry with slightly adjusted coordinates
        print(f"  🔄 Retry with adjusted coordinates...")
        success = _download_chosen_image(query, cx + 50, cy, img_path)

    if not success:
        _create_placeholder(img_path, label)

    return img_path


def run_image_pipeline(queries: dict, out_dir: str) -> tuple:
    """
    Search and download both expectation and reality images.
    Returns: (expectation_image_path, reality_image_path)
    """
    os.makedirs(out_dir, exist_ok=True)

    # Search for expectation image
    exp_path = search_and_download(
        queries["expectation_query"],
        "expectation",
        out_dir,
    )

    time.sleep(1 + random.uniform(0.5, 1.0))

    # Search for reality image
    real_path = search_and_download(
        queries["reality_query"],
        "reality",
        out_dir,
    )

    return exp_path, real_path
