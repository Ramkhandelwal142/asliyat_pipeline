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
LOGO_PATH   = ASSETS_DIR / "logo.png"      # Drop your logo PNG here
BRAND_NAME  = "THE ASLIYAT"
INSTA_HANDLE = "@the_asliyat"

# ═══════════════════════════════════════════════════════
#  LLM PROVIDERS  (fill in the ones you want to use)
# ═══════════════════════════════════════════════════════

# --- Option 1: Groq (cloud, FREE, recommended) ---
# Get your key: https://console.groq.com/keys
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
GROQ_TEXT_MODEL   = "llama-3.3-70b-versatile"                    # Best free text model
GROQ_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"  # Multimodal model from user's list

# --- Option 2: Ollama (local, 100% FREE, zero internet needed) ---
# Install: https://ollama.com  then run: ollama pull llama3.3:70b
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_TEXT_MODEL   = "llama3.3:70b"       # For text generation
OLLAMA_VISION_MODEL = "llava:13b"           # For image analysis (vision)
OLLAMA_ENABLED = False  # Set True if you have Ollama running locally

# --- Provider Priority ---
# "groq_first" = try Groq, fallback to Ollama if Groq fails
# "ollama_first" = try Ollama, fallback to Groq
# "groq_only"   = only use Groq
# "ollama_only" = only use Ollama
LLM_PRIORITY = "groq_first"

# ═══════════════════════════════════════════════════════
#  CONTENT GENERATION SETTINGS
# ═══════════════════════════════════════════════════════
NUM_CONCEPTS = 3           # How many meme ideas to generate
NUM_FINALISTS = 3           # How many to shortlist after scoring
CONTENT_TEMPERATURE = 0.92  # Higher = more creative
SCORING_TEMPERATURE = 0.2   # Lower = more consistent scoring
MAX_CONTENT_RETRIES = 2     # How many times to retry if QA fails

# ═══════════════════════════════════════════════════════
#  IMAGE SEARCH SETTINGS
# ═══════════════════════════════════════════════════════
IMAGE_SEARCH_ENGINE = "bing"   # "google" or "bing"
NUM_SCREENSHOTS = 4              # How many scroll screenshots to take
SCROLL_DISTANCE = 400            # Pixels to scroll between screenshots
HEADLESS_BROWSER = os.environ.get("HEADLESS_BROWSER", "True").lower() == "true"          # Required for cloud servers
BROWSER_TIMEOUT = 30             # Seconds before giving up on a page load

# ═══════════════════════════════════════════════════════
#  TEMPLATE / CANVAS SETTINGS
# ═══════════════════════════════════════════════════════
# Instagram 4:5 ratio (1080x1350 recommended)
CANVAS_WIDTH  = 1080
CANVAS_HEIGHT = 1350
PANEL_HEIGHT  = CANVAS_HEIGHT // 2   # 675px per panel

# Layout
IMAGE_COLUMN_WIDTH = 560    # Left column (image)
TEXT_PADDING        = 35    # Padding around text area
SEPARATOR_THICKNESS = 4     # Gold line between panels

# Colors (R, G, B)
COLOR_BLACK  = (0, 0, 0)
COLOR_WHITE  = (255, 255, 255)
COLOR_GOLD   = (212, 175, 55)
COLOR_GREY   = (140, 140, 140)

# Font sizes
FONT_TITLE_SIZE = 54        # "EXPECTATION" / "THE ASLIYAT"
FONT_BODY_SIZE  = 44        # Meme text
FONT_HANDLE_SIZE = 24       # "@the_asliyat" watermark
FONT_SMALL_SIZE = 20        # Small labels

# Logo
LOGO_SIZE = 100             # Logo dimensions (square)
LOGO_POSITION = "bottom-right"  # or "bottom-left"

# ═══════════════════════════════════════════════════════
#  QA / QUALITY SETTINGS
# ═══════════════════════════════════════════════════════
QA_MIN_SCORE = 6            # Minimum engagement score (1-10) to pass
QA_AUTO_RETRY = True        # Auto-regenerate if QA fails
MAX_QA_RETRIES = 2          # Max retry attempts

# ═══════════════════════════════════════════════════════
#  RESEARCH SETTINGS
# ═══════════════════════════════════════════════════════
RESEARCH_ENABLED = True     # Enable trending topic research
COMPETITOR_PAGES = [        # Instagram pages to monitor (optional)
    "@the_asliyat",
    # Add more pages to monitor:
    # "@funnymemes",
    # "@indianmemes",
]
TRENDING_REGION = "IN"      # Region for trending topics

# ═══════════════════════════════════════════════════════
#  SAVED MEMES LOG
# ═══════════════════════════════════════════════════════
SAVE_LOG = True             # Save generation history
LOG_FILE = OUTPUT_DIR / "generation_log.json"
