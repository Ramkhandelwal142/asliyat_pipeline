#!/usr/bin/env python3
"""
THE ASLIYAT — Phase 3: Meme Template Assembly

FIX #7: Added dynamic font sizing — if text is too long to fit in the text column,
the font size reduces progressively until everything fits cleanly.
Old behavior: text silently overflowed outside the panel. Looked broken.
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from config import (
    CANVAS_WIDTH, CANVAS_HEIGHT, PANEL_HEIGHT,
    IMAGE_COLUMN_WIDTH, TEXT_PADDING, SEPARATOR_THICKNESS,
    COLOR_BLACK, COLOR_WHITE, COLOR_GOLD, COLOR_GREY,
    FONT_TITLE_SIZE, FONT_BODY_SIZE, FONT_HANDLE_SIZE,
    LOGO_PATH, LOGO_SIZE, LOGO_POSITION,
    BRAND_NAME, INSTA_HANDLE, ASSETS_DIR
)


def _load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    """Load the best available font, with fallbacks for all platforms."""
    candidates = []

    if bold:
        candidates = [
            str(ASSETS_DIR / "fonts" / "bold.ttf"),
            str(ASSETS_DIR / "fonts" / "Montserrat-Bold.ttf"),
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial Bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/verdanab.ttf",
        ]
    else:
        candidates = [
            str(ASSETS_DIR / "fonts" / "regular.ttf"),
            str(ASSETS_DIR / "fonts" / "Montserrat-Regular.ttf"),
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-Regular.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]

    for font_path in candidates:
        try:
            return ImageFont.truetype(font_path, size)
        except (OSError, IOError):
            continue

    print("  ⚠ No custom font found — using Pillow default. Drop a .ttf in assets/fonts/ for better results.")
    return ImageFont.load_default()


def _wrap_text(text: str, font, max_width: int, draw: ImageDraw.Draw) -> list:
    """Wrap text to fit within max_width pixels. Returns list of lines."""
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines if lines else [text]


def _fit_text(
    text: str,
    draw: ImageDraw.Draw,
    max_width: int,
    max_height: int,
    initial_size: int,
    min_size: int = 24,
    bold: bool = True,
    line_spacing: int = 10
) -> tuple:
    """
    FIX #7: Dynamic font sizing.
    Tries font sizes from initial_size down to min_size until the text
    fits within (max_width x max_height). Returns (font, wrapped_lines, actual_size).
    """
    size = initial_size
    while size >= min_size:
        font = _load_font(size, bold=bold)
        lines = _wrap_text(text, font, max_width, draw)
        # Calculate total height needed
        line_height = draw.textbbox((0, 0), "Ag", font=font)[3] + line_spacing
        total_height = line_height * len(lines)
        if total_height <= max_height:
            return font, lines, size
        size -= 4  # Reduce by 4pt steps

    # If even min_size doesn't fit, use it anyway (better than nothing)
    font = _load_font(min_size, bold=bold)
    lines = _wrap_text(text, font, max_width, draw)
    return font, lines, min_size


def _smart_crop(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """
    Smart crop: fills the target area while keeping important content centered.
    """
    iw, ih = img.size
    scale = max(target_w / iw, target_h / ih)
    new_w = int(iw * scale)
    new_h = int(ih * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def _paste_image(canvas: Image.Image, img_path: str, x: int, y: int, w: int, h: int):
    """Load, crop, and paste an image onto the canvas."""
    try:
        img = Image.open(img_path).convert("RGB")
        img = _smart_crop(img, w, h)
        canvas.paste(img, (x, y))
        return True
    except Exception as e:
        print(f"  ⚠ Image paste failed ({e})")
        draw = ImageDraw.Draw(canvas)
        draw.rectangle([x, y, x + w, y + h], fill=(20, 20, 20))
        draw.text((x + 20, y + h // 2), "[Image Error]", fill=COLOR_GREY, font=_load_font(24))
        return False


def _paste_logo(canvas: Image.Image, logo_path: str, x: int, y: int, size: int = LOGO_SIZE):
    """Paste logo with transparency support."""
    try:
        logo = Image.open(logo_path).convert("RGBA")
        logo = logo.resize((size, size), Image.LANCZOS)
        canvas.paste(logo, (x, y), logo)
        return True
    except FileNotFoundError:
        draw = ImageDraw.Draw(canvas)
        font = _load_font(22, bold=True)
        draw.text((x, y + 35), "THE ASLIYAT", fill=COLOR_GOLD, font=font)
        return False
    except Exception as e:
        print(f"  ⚠ Logo paste failed ({e})")
        return False


def assemble_meme(meme: dict, exp_img_path: str, real_img_path: str, output_path: str) -> str:
    """
    Assemble the complete 2-panel meme.
    Returns the output file path.
    """
    print("\n  🎨 PHASE 3 — Assembling meme template...")

    canvas = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), COLOR_BLACK)
    draw = ImageDraw.Draw(canvas)

    # Fixed fonts for labels/watermark
    f_title  = _load_font(FONT_TITLE_SIZE, bold=True)
    f_brand  = _load_font(FONT_TITLE_SIZE - 4, bold=True)
    f_handle = _load_font(FONT_HANDLE_SIZE, bold=False)

    # Text area dimensions
    text_x = IMAGE_COLUMN_WIDTH + TEXT_PADDING
    text_w = CANVAS_WIDTH - IMAGE_COLUMN_WIDTH - (TEXT_PADDING * 2)

    # ─────────────────────────────────────────────
    #  PANEL 1: EXPECTATION (Top Half)
    # ─────────────────────────────────────────────
    _paste_image(canvas, exp_img_path, 0, 0, IMAGE_COLUMN_WIDTH, PANEL_HEIGHT)

    # "EXPECTATION" label
    draw.text((text_x, 38), "EXPECTATION", font=f_title, fill=COLOR_WHITE)

    # FIX #7: Dynamic font sizing for body text
    # Available height: from y=120 to PANEL_HEIGHT - 40 (leave margin above gold line)
    body_max_h = PANEL_HEIGHT - 120 - 40
    f_exp, exp_lines, exp_size = _fit_text(
        meme["expectation_text"], draw,
        max_width=text_w, max_height=body_max_h,
        initial_size=FONT_BODY_SIZE, min_size=24,
        line_spacing=12
    )
    if exp_size < FONT_BODY_SIZE:
        print(f"  ℹ Expectation text: font reduced {FONT_BODY_SIZE}→{exp_size}pt to fit")

    y_pos = 120
    for line in exp_lines:
        draw.text((text_x, y_pos), line, font=f_exp, fill=COLOR_WHITE)
        bbox = draw.textbbox((0, 0), "Ag", font=f_exp)
        y_pos += (bbox[3] - bbox[1]) + 12

    # ─────────────────────────────────────────────
    #  GOLD SEPARATOR LINE
    # ─────────────────────────────────────────────
    sep_y = PANEL_HEIGHT - (SEPARATOR_THICKNESS // 2)
    draw.rectangle(
        [0, sep_y, CANVAS_WIDTH, sep_y + SEPARATOR_THICKNESS],
        fill=COLOR_GOLD
    )

    # ─────────────────────────────────────────────
    #  PANEL 2: THE ASLIYAT / REALITY (Bottom Half)
    # ─────────────────────────────────────────────
    panel2_y = PANEL_HEIGHT + SEPARATOR_THICKNESS
    _paste_image(canvas, real_img_path, 0, panel2_y, IMAGE_COLUMN_WIDTH, CANVAS_HEIGHT - panel2_y)

    # "THE ASLIYAT" label in gold
    draw.text((text_x, panel2_y + 38), "THE ASLIYAT", font=f_brand, fill=COLOR_GOLD)

    # FIX #7: Dynamic font sizing for reality text too
    real_max_h = (CANVAS_HEIGHT - panel2_y) - 120 - 50  # leave room for watermark
    f_real, real_lines, real_size = _fit_text(
        meme["reality_text"], draw,
        max_width=text_w, max_height=real_max_h,
        initial_size=FONT_BODY_SIZE, min_size=24,
        line_spacing=12
    )
    if real_size < FONT_BODY_SIZE:
        print(f"  ℹ Reality text: font reduced {FONT_BODY_SIZE}→{real_size}pt to fit")

    y_pos = panel2_y + 120
    for line in real_lines:
        draw.text((text_x, y_pos), line, font=f_real, fill=COLOR_WHITE)
        bbox = draw.textbbox((0, 0), "Ag", font=f_real)
        y_pos += (bbox[3] - bbox[1]) + 12

    # ─────────────────────────────────────────────
    #  LOGO (bottom-right or bottom-left)
    # ─────────────────────────────────────────────
    logo_x = (CANVAS_WIDTH - LOGO_SIZE - 15) if LOGO_POSITION == "bottom-right" else 15
    logo_y = CANVAS_HEIGHT - LOGO_SIZE - 15
    _paste_logo(canvas, str(LOGO_PATH), logo_x, logo_y)

    # ─────────────────────────────────────────────
    #  WATERMARK: @the_asliyat (bottom center)
    # ─────────────────────────────────────────────
    handle_bbox = draw.textbbox((0, 0), INSTA_HANDLE, font=f_handle)
    handle_w = handle_bbox[2] - handle_bbox[0]
    handle_x = (CANVAS_WIDTH - handle_w) // 2
    draw.text((handle_x, CANVAS_HEIGHT - 34), INSTA_HANDLE, font=f_handle, fill=COLOR_GREY)

    # ─────────────────────────────────────────────
    #  SAVE
    # ─────────────────────────────────────────────
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    canvas.save(output_path, quality=95, optimize=True)
    file_size = os.path.getsize(output_path) // 1024
    print(f"  ✓ Meme assembled: {output_path} ({file_size}KB)")

    return output_path
