#!/usr/bin/env python3
"""
THE ASLIYAT — Phase 0: Research Module
Finds trending topics and competitor content ideas.
"""

import json, time, random
from llm import get_llm
from config import RESEARCH_ENABLED, TRENDING_REGION, NUM_CONCEPTS


def get_trending_topics(num_topics=5):
    """
    Use LLM to suggest trending/relatable topics for Indian meme audience.
    This doesn't require any API — the LLM uses its training data + current knowledge.
    """
    print("\n  🔍 PHASE 0 — Research: Finding trending topics...")

    llm = get_llm()

    prompt = f"""You are a trend researcher for an Indian meme Instagram page (@the_asliyat).
Your audience is Indian Gen-Z and millennials (18-30 years old).

Generate {num_topics} trending, highly relatable topics for Expectation vs Reality memes right now.
Consider:
- Current season/time of year events
- Indian cultural moments, festivals, daily life
- Viral trends on Instagram/Reels
- Student life, corporate life, relationships, family
- Current news events that have meme potential
- Relatable everyday Indian situations

Return ONLY valid JSON:
{{
  "trending_now": ["topic 1", "topic 2", ...],
  "evergreen": ["evergreen topic 1", ...],
  "seasonal": ["seasonal topic 1", ...],
  "suggested_topic": "THE single best topic to use RIGHT NOW for maximum engagement",
  "reason": "Why this topic will go viral"
}}"""

    try:
        result = llm.text_json([{"role": "user", "content": prompt}], temperature=0.8)
        print(f"  ✅ Found {len(result.get('trending_now', []))} trending topics")
        print(f"  🎯 Top pick: {result.get('suggested_topic', 'N/A')}")
        print(f"  📝 Reason: {result.get('reason', 'N/A')}")
        return result
    except Exception as e:
        print(f"  ⚠ Research failed ({e}), will use AI's own topic selection")
        return {"suggested_topic": None}


def refine_topic_with_research(topic_hint=None):
    """
    If user provides a topic hint, refine it. If not, let LLM pick based on trends.
    Returns the final topic to use for meme generation.
    """
    if not RESEARCH_ENABLED:
        return topic_hint  # Skip research, use user hint or None

    research = get_trending_topics()

    if topic_hint:
        # User gave a topic — use research to validate/enhance
        llm = get_llm()
        prompt = f"""A user suggested this meme topic: "{topic_hint}"

Based on current trends for Indian Gen-Z/millennial audience, evaluate this topic.
Should we use it as-is, or slightly modify it for maximum viral potential?

Return ONLY valid JSON:
{{
  "final_topic": "refined topic (use original if already good)",
  "angle": "the specific meme angle to take",
  "tweak": "what was changed and why (or 'no change needed' if keeping original)"
}}"""
        try:
            result = llm.text_json([{"role": "user", "content": prompt}], temperature=0.5)
            final = result.get("final_topic", topic_hint)
            print(f"  🔄 Refined topic: '{topic_hint}' → '{final}'")
            if result.get("tweak", "").startswith("no change"):
                return topic_hint
            return final
        except:
            return topic_hint
    else:
        # No user hint — use research suggestion
        suggested = research.get("suggested_topic")
        if suggested:
            print(f"  🎯 AI selected topic: {suggested}")
            return suggested
        return None
