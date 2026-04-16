# THE ASLIYAT — Automated Meme Pipeline v2.0

> **Fully automated Expectation vs Reality meme generator for Instagram.**
> AI generates content → finds images → assembles template → QA checks → ready to post.

---

## What This Does (In 60 Seconds)

1. **AI picks a trending topic** (or you give one)
2. **Generates 10 meme ideas**, scores them, picks the best one
3. **Searches Google Images**, takes screenshots while scrolling
4. **Vision AI reviews screenshots** and picks the perfect image
5. **Downloads the chosen images** automatically
6. **Assembles your exact 2-panel template** (logo, gold text, layout)
7. **QA vision check** — verifies quality before delivering
8. **Output: Ready-to-post JPG** — you just add music and post!

---

## Quick Start (5 Minutes)

### Step 1: Install Python Packages

```bash
cd asliyat_pipeline
pip install -r requirements.txt
playwright install chromium
```

### Step 2: Get Your Free Groq API Key

1. Go to https://console.groq.com/keys
2. Create a free account
3. Copy your API key
4. Set it in terminal:

```bash
# macOS / Linux
export GROQ_API_KEY="gsk_your_key_here"

# Windows (Command Prompt)
set GROQ_API_KEY=gsk_your_key_here

# Windows (PowerShell)
$env:GROQ_API_KEY="gsk_your_key_here"
```

### Step 3: Add Your Logo

Drop your logo file as `assets/logo.png`. If you don't have one yet, the pipeline creates a text-based placeholder.

### Step 4: Run!

```bash
# AI picks the topic (recommended)
python pipeline.py

# Or give it a topic
python pipeline.py --topic "gym life"
python pipeline.py --topic "Monday morning"
python pipeline.py --topic "exam night"
python pipeline.py --topic "marriage pressure"

# Skip research, use topic directly
python pipeline.py --topic "gym life" --no-research
```

**Output appears in `output/` folder — ready to post!**

---

## Pipeline Architecture

```
┌─────────────────────────────────────────────┐
│         PHASE 0: RESEARCH                   │
│  AI suggests trending topics for Indian     │
│  Gen-Z / millennial audience                │
└────────────────┬────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────┐
│         PHASE 1: CONTENT GENERATION         │
│                                             │
│  1a. Generate 10 meme concepts              │
│  1b. Score each on 5 dimensions (Round 1)   │
│  1c. Second opinion picks winner (Round 2)  │
│  1d. Generate image search queries          │
└────────────────┬────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────┐
│         PHASE 2: IMAGE SEARCH               │
│                                             │
│  • Open Google/Bing Images                  │
│  • Scroll down, take 4 screenshots          │
│  • Vision AI reviews screenshots            │
│  • AI picks best image + gives coordinates  │
│  • Auto-download the chosen image           │
│  (Repeat for Expectation + Reality)         │
└────────────────┬────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────┐
│         PHASE 3: TEMPLATE ASSEMBLY          │
│                                             │
│  • Black 1080×1350 canvas (Instagram 4:5)   │
│  • Top panel: Image + "EXPECTATION" + text  │
│  • Gold separator line                      │
│  • Bottom panel: Image + "THE ASLIYAT"      │
│  • Logo (bottom-right)                      │
│  • @the_asliyat watermark (bottom-center)   │
└────────────────┬────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────┐
│         PHASE 4: QA CHECK                   │
│                                             │
│  • Vision AI reviews final meme             │
│  • Scores readability, relevance, branding  │
│  • Auto-retry if quality too low            │
└─────────────────────────────────────────────┘
```

---

## Configuration (config.py)

Edit `config.py` to customize everything. Key settings:

### LLM Provider

```python
# Option 1: Groq (cloud, FREE, recommended)
GROQ_API_KEY = "your_key_here"

# Option 2: Ollama (local, 100% FREE, no internet needed)
OLLAMA_ENABLED = True

# Priority: which to try first
LLM_PRIORITY = "groq_first"  # or "ollama_first"
```

### Content Settings

```python
NUM_CONCEPTS = 10        # How many ideas to generate
NUM_FINALISTS = 3        # How many to shortlist
CONTENT_TEMPERATURE = 0.92  # Higher = more creative
```

### Image Search

```python
IMAGE_SEARCH_ENGINE = "google"   # "google" or "bing"
NUM_SCREENSHOTS = 4              # Screenshots while scrolling
HEADLESS_BROWSER = True          # Set False to see browser
```

### Template

```python
CANVAS_WIDTH = 1080    # Instagram recommended
CANVAS_HEIGHT = 1350   # 4:5 ratio
COLOR_GOLD = (212, 175, 55)  # Brand gold color
```

---

## Ollama Setup (100% FREE, No Internet Needed)

If you want to run everything locally with zero API costs:

### 1. Install Ollama

```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: Download from https://ollama.com/download
```

### 2. Pull Models

```bash
# Text generation model (best quality)
ollama pull llama3.3:70b

# Vision model (for image analysis)
ollama pull llava:13b

# Or smaller/faster alternatives:
ollama pull llama3.1:8b    # Faster, less creative
ollama pull llava:7b       # Faster vision
```

### 3. Enable in config.py

```python
OLLAMA_ENABLED = True
LLM_PRIORITY = "ollama_only"  # or "ollama_first"
```

### Model Comparison

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| llama3.3:70b | 40GB | Slow | Best | Final content, creative writing |
| llama3.1:8b | 4.7GB | Fast | Good | Scoring, quick analysis |
| llama3.2:3b | 2GB | Very Fast | Decent | Simple tasks, fallback |
| llava:13b | 8GB | Medium | Good | Vision/image analysis |
| llava:7b | 4.7GB | Fast | Decent | Quick image checks |

**Recommendation:** Use `llama3.3:70b` for content + `llava:13b` for vision if you have 16GB+ RAM. Otherwise use the 8b versions.

---

## Custom Fonts

Drop your fonts in `assets/fonts/`:

```
assets/fonts/
├── bold.ttf              # Montserrat-Bold.ttf or any bold font
└── regular.ttf           # Montserrat-Regular.ttf or any regular font
```

The pipeline auto-detects these fonts. Without custom fonts, it uses system defaults.

**Recommended fonts (free):**
- [Montserrat](https://fonts.google.com/specimen/Montserrat) — clean, modern
- [Poppins](https://fonts.google.com/specimen/Poppins) — trendy, great for memes
- [Bebas Neue](https://fonts.google.com/specimen/Bebas+Neue) — bold headers

---

## Folder Structure

```
asliyat_pipeline/
├── pipeline.py           ← Main script (run this)
├── config.py             ← All settings (edit this)
├── llm.py                ← LLM abstraction (Groq + Ollama)
├── research.py           ← Phase 0: Trending topics
├── content.py            ← Phase 1: Content generation
├── images.py             ← Phase 2: Image search + download
├── template.py           ← Phase 3: Meme assembly
├── qa.py                 ← Phase 4: QA check
├── requirements.txt      ← Python packages
├── README.md             ← This file
├── assets/
│   ├── logo.png          ← YOUR LOGO (add here)
│   └── fonts/
│       ├── bold.ttf      ← Bold font (optional)
│       └── regular.ttf   ← Regular font (optional)
└── output/
    ├── asliyat_1712345678.jpg    ← Generated memes
    └── generation_log.json       ← History of all generations
```

---

## CLI Reference

```bash
python pipeline.py                                    # AI picks topic
python pipeline.py --topic "gym life"                 # Specific topic
python pipeline.py -t "exam night"                    # Short form
python pipeline.py --no-research                      # Skip research
python pipeline.py -t "Monday morning" --no-research  # Combined
```

---

## Troubleshooting

### "Groq: Add your API key"
→ Set `GROQ_API_KEY` environment variable or edit `config.py`

### "Playwright not installed"
→ Run: `pip install playwright && playwright install chromium`

### "Ollama: Cannot connect"
→ Start Ollama: `ollama serve` (or just run `ollama` in terminal)

### "Ollama: Model not found"
→ Pull it: `ollama pull llama3.3:70b`

### Images not downloading?
→ Set `HEADLESS_BROWSER = False` in config.py to see the browser and debug

### Groq rate limit?
→ Add `time.sleep(2)` between API calls, or use Ollama as fallback

### Font looks bad?
→ Drop a .ttf font in `assets/fonts/bold.ttf`

### "No LLM provider available"
→ You need either Groq API key OR Ollama running. Set up at least one.

---

## Cost

| Component | Cost |
|-----------|------|
| Groq API | **FREE** (generous rate limits) |
| Ollama (local) | **FREE** (uses your PC) |
| Playwright | **FREE** |
| Pillow | **FREE** |
| Google/Bing Images | **FREE** |

**Total cost: $0.00 forever.**

---

## What Makes This Special

1. **Multi-layer AI review** — Not just one AI call, but a 3-round selection process
2. **Vision-based image selection** — AI literally looks at search results and picks the best image
3. **Auto-scroll + screenshot** — Simulates human browsing behavior
4. **Dual provider support** — Groq (cloud) + Ollama (local), auto-fallback
5. **Exact template replication** — Matches your @the_asliyat brand perfectly
6. **Quality loop** — QA check with auto-retry if meme doesn't meet standards
7. **Zero cost** — Everything runs on free tiers
