#!/usr/bin/env python3
"""
THE ASLIYAT — Phase 0: Research Module

FIX #4: Old version just asked the LLM to "suggest trending topics" from
its training data — which has a months-old cutoff. It generated the same
generic topics every time (gym, Monday, exams) with zero real-world signal.

New approach:
1. Fetch ACTUAL trending searches in India from Google Trends RSS (free, no API key)
2. Also scrape quick context from a free news source
3. Feed this real-time data into the LLM prompt as grounding context
4. LLM then INTERPRETS the trends → finds meme angle → much better output
"""

import json, time, random
from datetime import datetime
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import xml.etree.ElementTree as ET
    HAS_XML = True
except ImportError:
    HAS_XML = False

from llm import get_llm
from config import RESEARCH_ENABLED, TRENDING_REGION, NUM_CONCEPTS


def _fetch_google_trends_india() -> list:
    """
    Fetch currently trending searches in India from Google Trends RSS.
    Free, no API key needed.
    Returns list of trending topic strings.
    """
    if not HAS_REQUESTS:
        return []

    try:
        # Google Trends daily trending searches RSS for India
        url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=IN"
        resp = requests.get(url, timeout=8, headers={
            "User-Agent": "Mozilla/5.0 (compatible; AsliyatBot/1.0)"
        })

        if resp.status_code != 200:
            return []

        # Parse RSS XML
        root = ET.fromstring(resp.content)
        trends = []
        for item in root.findall(".//item")[:15]:  # Top 15 trends
            title = item.find("title")
            if title is not None and title.text:
                trends.append(title.text.strip())

        print(f"  ✓ Fetched {len(trends)} real trending topics from Google Trends India")
        return trends

    except Exception as e:
        print(f"  ⚠ Google Trends fetch failed ({e}), falling back to LLM suggestions")
        return []


def _fetch_india_news_headlines() -> list:
    """
    Fetch current Indian news headlines from a free RSS source.
    Gives LLM context about what's happening in India right now.
    Returns list of headline strings.
    """
    if not HAS_REQUESTS:
        return []

    sources = [
        "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "https://feeds.feedburner.com/ndtvnews-top-stories",
    ]

    for url in sources:
        try:
            resp = requests.get(url, timeout=5, headers={
                "User-Agent": "Mozilla/5.0 (compatible; AsliyatBot/1.0)"
            })
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                headlines = []
                for item in root.findall(".//item")[:10]:
                    title = item.find("title")
                    if title is not None and title.text:
                        headlines.append(title.text.strip())
                if headlines:
                    print(f"  ✓ Fetched {len(headlines)} news headlines for context")
                    return headlines
        except Exception:
            continue

    return []


def get_trending_topics(num_topics=5):
    """
    Get trending topics for Indian meme audience.
    Now uses REAL data from Google Trends + news, not just LLM guesswork.
    """
    print("\n  🔍 PHASE 0 — Research: Finding REAL trending topics...")

    # Fetch actual trending data
    real_trends = _fetch_google_trends_india()
    news_headlines = _fetch_india_news_headlines()

    llm = get_llm()
    today = datetime.now().strftime("%d %B %Y")

    # Build context string with real data
    trends_context = ""
    if real_trends:
        trends_context += f"\nCURRENTLY TRENDING IN INDIA (Google Trends, {today}):\n"
        trends_context += "\n".join(f"  - {t}" for t in real_trends[:10])

    if news_headlines:
        trends_context += f"\n\nCURRENT INDIA NEWS HEADLINES:\n"
        trends_context += "\n".join(f"  - {h}" for h in news_headlines[:8])

    if not trends_context:
        trends_context = f"\n(Real-time data unavailable — use your knowledge of India for {today})\n"

    prompt = f"""You are a trend researcher for @the_asliyat — an Indian meme page for Gen-Z and millennials (18-30 years old).

Today is: {today}
{trends_context}

Using the REAL trending data above, identify which trends have MEME POTENTIAL.
A trend has meme potential when it connects to a relatable everyday Indian experience — work, college, family, relationships, money.

Think:
- IPL → "Expectation: watching match with full concentration | Reality: checking phone every 2 mins"
- Heatwave trend → "Expectation: summer fashion Instagram photoshoot | Reality: sweating through 3 shirts before reaching office"

Generate {num_topics} meme-worthy topics. Prioritize the REAL trending ones. Fill with evergreen if needed.

Return ONLY valid JSON:
{{
  "trending_now": ["topic 1 (from real trends)", "topic 2", ...],
  "evergreen": ["topic that always works", ...],
  "seasonal": ["topic relevant to current season/time of year", ...],
  "suggested_topic": "THE single best topic RIGHT NOW for maximum engagement",
  "reason": "Specific reason why this will go viral — what emotion/situation does it tap into?"
}}"""

    try:
        result = llm.text_json([{"role": "user", "content": prompt}], temperature=0.8, max_tokens=600)
        print(f"  ✓ Found {len(result.get('trending_now', []))} trending topics")
        print(f"  🎯 Top pick: {result.get('suggested_topic', 'N/A')}")
        print(f"  💡 Reason: {result.get('reason', 'N/A')}")
        return result
    except Exception as e:
        print(f"  ⚠ Research failed ({e}), will use AI's own topic selection")
        return {"suggested_topic": None}


def refine_topic_with_research(topic_hint=None):
    """
    If user provides a topic hint, refine it with research context.
    If not, let LLM pick based on actual trending data.
    Returns the final topic to use for meme generation.
    """
    if not RESEARCH_ENABLED:
        return topic_hint

    research = get_trending_topics()

    if topic_hint:
        llm = get_llm()
        today = datetime.now().strftime("%d %B %Y")
        prompt = f"""A user suggested this meme topic: "{topic_hint}"
Today is {today}.

Evaluate this topic for @the_asliyat audience (Indian Gen-Z/millennials).
Should we use it as-is, or slightly modify it for maximum viral potential?

Return ONLY valid JSON:
{{
  "final_topic": "refined topic (use original if already good)",
  "angle": "the specific meme angle to take",
  "tweak": "what was changed and why (or 'no change needed')"
}}"""
        try:
            result = llm.text_json([{"role": "user", "content": prompt}], temperature=0.5, max_tokens=200)
            final = result.get("final_topic", topic_hint)
            tweak = result.get("tweak", "")
            if not tweak.lower().startswith("no change"):
                print(f"  🔄 Refined topic: '{topic_hint}' → '{final}'")
                return final
            return topic_hint
        except Exception:
            return topic_hint
    else:
        suggested = research.get("suggested_topic")
        if suggested:
            print(f"  🎯 AI selected topic: {suggested}")
            return suggested
        return None
