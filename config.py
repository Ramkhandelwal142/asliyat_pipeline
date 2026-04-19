#!/usr/bin/env python3
"""
THE ASLIYAT — Configuration
Edit this file to customize the pipeline.
"""

import os
from pathlib import Path

# ═══════════════════════════════════════════════════════
#  DIRECTORIES
# ═══════════════════════════════════════════════════════
BASE_DIR   = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"
TEMPLATE_DIR = BASE_DIR / "templates"

# ═══════════════════════════════════════════════════════
#  LOGO & BRAND
# ═══════════════════════════════════════════════════════
LOGO_PATH   = ASSETS_DIR / "logo.png"
BRAND_NAME  = "THE ASLIYAT"
INSTA_HANDLE = "@the_asliyat"

# ═══════════════════════════════════════════════════════
#  LLM PROVIDERS
# ═══════════════════════════════════════════════════════
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
GROQ_TEXT_MODEL   = "llama-3.3-70b-versatile"
GROQ_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_TEXT_MODEL   = "llama3.3:70b"
OLLAMA_VISION_MODEL = "llava:13b"
OLLAMA_ENABLED = False

LLM_PRIORITY = "groq_first"

# ═══════════════════════════════════════════════════════
#  CONTENT GENERATION SETTINGS
# ═══════════════════════════════════════════════════════
# FIX #2: Raised from 3 → 10. More options = genuinely better selection.
# The scoring + second-opinion system only works with real diversity.
NUM_CONCEPTS = 10
NUM_FINALISTS = 3
CONTENT_TEMPERATURE = 0.92
SCORING_TEMPERATURE = 0.2
MAX_CONTENT_RETRIES = 2

# ═══════════════════════════════════════════════════════
#  IMAGE SEARCH SETTINGS
# ═══════════════════════════════════════════════════════
IMAGE_SEARCH_ENGINE = "bing"
NUM_SCREENSHOTS = 4
SCROLL_DISTANCE = 400
HEADLESS_BROWSER = os.environ.get("HEADLESS_BROWSER", "True").lower() == "true"
BROWSER_TIMEOUT = 30

# ═══════════════════════════════════════════════════════
#  TEMPLATE / CANVAS SETTINGS
# ═══════════════════════════════════════════════════════
CANVAS_WIDTH  = 1080
CANVAS_HEIGHT = 1350
PANEL_HEIGHT  = CANVAS_HEIGHT // 2   # 675px per panel

IMAGE_COLUMN_WIDTH = 560
TEXT_PADDING        = 35
SEPARATOR_THICKNESS = 4

COLOR_BLACK  = (0, 0, 0)
COLOR_WHITE  = (255, 255, 255)
COLOR_GOLD   = (212, 175, 55)
COLOR_GREY   = (140, 140, 140)

FONT_TITLE_SIZE = 54
FONT_BODY_SIZE  = 44
FONT_HANDLE_SIZE = 24
FONT_SMALL_SIZE = 20

LOGO_SIZE = 100
LOGO_POSITION = "bottom-right"

# ═══════════════════════════════════════════════════════
#  QA / QUALITY SETTINGS
# ═══════════════════════════════════════════════════════
# FIX #8: Raised min score from 6 → 7. LLMs score generously,
# so 6/10 from the AI is actually "mediocre" in real terms.
QA_MIN_SCORE = 7
QA_AUTO_RETRY = True
MAX_QA_RETRIES = 2

# ═══════════════════════════════════════════════════════
#  RESEARCH SETTINGS
# ═══════════════════════════════════════════════════════
RESEARCH_ENABLED = True
COMPETITOR_PAGES = ["@the_asliyat"]
TRENDING_REGION = "IN"

# ═══════════════════════════════════════════════════════
#  SAVED MEMES LOG
# ═══════════════════════════════════════════════════════
SAVE_LOG = True
LOG_FILE = OUTPUT_DIR / "generation_log.json"
