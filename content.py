
#!/usr/bin/env python3
"""
THE ASLIYAT — Phase 1: Content Generation
Multi-layer refinement: 10 options → score → top 3 → 2nd opinion → final 1
"""

import json, time
from llm import get_llm
from config import (
    NUM_CONCEPTS, NUM_FINALISTS,
    CONTENT_TEMPERATURE, SCORING_TEMPERATURE
)


def generate_concepts(topic=None):
    """
    Generate NUM_CONCEPTS meme ideas using LLM.
    Returns raw JSON with all options.
    """
    print(f"\n  📝 PHASE 1a — Generating {NUM_CONCEPTS} meme concepts...")

    llm = get_llm()
    
    prompt = f"""You are the internet's funniest, most sarcastic Indian meme creator. You write brutally relatable 2-panel "Expectation vs Reality" memes for an Instagram page followed by millions of Indian youth.
Topic: "{topic if topic else 'Everyday Indian struggle'}"

RULES FOR HIGH-IQ COMEDY:
1. NO GENERIC DESCRIPTIONS. Use ultra-specific, sarcastic, and cinematic phrasing.
   BAD EXPECTATION: "Easily getting in and out of the train"
   GOOD EXPECTATION: "Listening to Arjit Singh and looking out the window like a romantic Bollywood hero."
   
   BAD REALITY: "Train is crowded and people fall on each other."
   GOOD REALITY: "Dadar utarte waqt pair zameen par nahi hote, bas bheed ke sahare bahar phek diye jaate hain."

2. ROMANIZED HINGLISH ONLY (English alphabet). Never use Devnagari.
3. NATIVE SLANG REQUIRED: Use words like bhai, yaar, kalesh, CTC, jugaad, HR, Virar fast.
4. Keep it to EXACTLY one punchy, hard-hitting sentence per panel. Avoid bloated paragraphs.

Now, generate EXACTLY {NUM_CONCEPTS} brilliant concepts using this exact topic: "{topic if topic else 'a trending everyday Indian struggle'}"

Return ONLY valid JSON:
{{
  "topic": "main topic name",
  "options": [
    {{
      "id": 1,
      "expectation_text": "Tom Cruise style running + stunts",
      "reality_text": "2 min run = breathing issue + पानी दो",
      "emotion": "self-deprecating fitness humor",
      "relatability": "everyone has tried running once after watching a movie",
      "target_demo": "18-25 gym beginners",
      "tag_potential": "people will tag their gym buddy"
    }}
  ]
}}"""

    try:
        result = llm.text_json(
            [{"role": "user", "content": prompt}],
            temperature=CONTENT_TEMPERATURE,
            max_tokens=3000,
        )
        options = result.get("options", [])
        # Ensure we have the right count
        if len(options) < NUM_CONCEPTS:
            print(f"  ⚠ Got {len(options)} options instead of {NUM_CONCEPTS}, continuing...")
        else:
            print(f"  ✅ Generated {len(options)} meme concepts")
        print(f"  📌 Topic: {result.get('topic', 'N/A')}")
        return result
    except Exception as e:
        print(f"  ❌ Concept generation failed: {e}")
        raise


def score_and_pick(concepts: dict) -> dict:
    """
    Round 1 scoring: Rate each concept on multiple dimensions.
    Returns scores and top 3 IDs.
    """
    print("\n  📊 PHASE 1b — Scoring viral potential (Round 1)...")

    llm = get_llm()

    options_list = []
    for o in concepts["options"]:
        options_list.append(
            f'[{o["id"]}] E: "{o["expectation_text"]}" | R: "{o["reality_text"]}"\n'
            f'     Emotion: {o.get("emotion", "")} | Relatability: {o.get("relatability", "")}'
        )
    options_text = "\n".join(options_list)

    prompt = f"""You are a viral content strategist for Indian Instagram meme pages with millions of followers.
You know EXACTLY what makes Indian Gen-Z stop scrolling and tag friends.

Score each meme option (1-10) on these CRITICAL factors:
1. **relatability** — Will the viewer feel "yeh toh mere saath bhi hota hai"?
2. **humor_punch** — Is the contrast between expectation and reality sharp enough?
3. **share_urge** — Will someone save this or send it to a friend?
4. **hinglish_flow** — Does the Hindi-English mix feel natural, not forced?
5. **tag_potential** — Will people tag someone specific ("yeh tu hai" energy)?

BONUS points for:
- Bollywood references
- Daily Indian life moments (auto, chai, mom calling, etc.)
- Moment-of-truth humor (exam results, salary, marriage talks)

{options_text}

Return ONLY valid JSON:
{{
  "scores": [
    {{"id": 1, "relatability": 9, "humor_punch": 8, "share_urge": 9, "hinglish_flow": 9, "tag_potential": 8, "total": 43}}
  ],
  "top_3_ids": [3, 1, 7],
  "best_id": 3,
  "reason": "Why this one will go viral — be specific"
}}"""

    try:
        result = llm.text_json(
            [{"role": "user", "content": prompt}],
            temperature=SCORING_TEMPERATURE,
            max_tokens=1500,
        )
        top3 = result.get("top_3_ids", [])
        best = result.get("best_id", "unknown")
        reason = result.get("reason", "N/A")

        # Print top 3 with scores
        for s in result.get("scores", []):
            if s["id"] in top3:
                marker = " 👑" if s["id"] == best else ""
                print(f"     #{s['id']}: total={s['total']}/50{marker}")

        print(f"  ✅ Round 1 winner: #{best}")
        print(f"  📝 Reason: {reason}")
        return result
    except Exception as e:
        print(f"  ❌ Scoring failed: {e}")
        raise


def second_opinion(concepts: dict, top3_ids: list) -> dict:
    """
    Round 2: Final review by a "different persona" — picks the absolute best one.
    This acts as a second pair of eyes to catch anything the first round missed.
    """
    print("\n  🔍 PHASE 1c — Second opinion check (Round 2)...")

    llm = get_llm()

    top3 = [o for o in concepts["options"] if o["id"] in top3_ids]
    if len(top3) == 0:
        top3 = concepts["options"][:3]  # Fallback

    options_text = "\n".join([
        f'[{o["id"]}] E: "{o["expectation_text"]}" | R: "{o["reality_text"]}"'
        f'\n     Emotion: {o.get("emotion", "")} | Why relatable: {o.get("relatability", "")}'
        for o in top3
    ])

    prompt = f"""FINAL JURY — You are the last decision-maker for @the_asliyat meme page.
These 3 options made it past the first round. Pick THE BEST ONE.

Think like an Indian college student scrolling Instagram at 2 AM:
- Which one makes you go "BRO 😂😂😂"?
- Which one would you instantly forward to your WhatsApp group?
- Which one feels like YOUR life?
- Does the Hinglish feel like how real people talk, or does it feel AI-generated?

{options_text}

Pick ONE. Be brutal in your judgment.
Return ONLY valid JSON:
{{
  "final_id": 3,
  "final_reason": "Detailed reason why this is THE one — what emotion does it trigger?",
  "emotional_trigger": "What exact feeling does it evoke? (e.g., nostalgia, self-realization, bittersweet, pure comedy)",
  "audience_reaction": "Predicted audience reaction in one line"
}}"""

    try:
        result = llm.text_json(
            [{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=400,
        )
        final_id = result["final_id"]

        # Find the chosen option
        chosen = None
        for o in concepts["options"]:
            if o["id"] == final_id:
                chosen = o
                break
        if not chosen:
            chosen = top3[0]  # Fallback to first finalist

        print(f"  ✅ FINAL PICK: #{final_id}")
        print(f"     E: \"{chosen['expectation_text']}\"")
        print(f"     R: \"{chosen['reality_text']}\"")
        print(f"  💡 Trigger: {result.get('emotional_trigger', 'N/A')}")
        print(f"  🎯 Prediction: {result.get('audience_reaction', 'N/A')}")
        return chosen
    except Exception as e:
        print(f"  ❌ Second opinion failed: {e}")
        return top3[0] if top3 else concepts["options"][0]


def get_image_search_queries(meme: dict) -> dict:
    """
    Generate specific image search queries based on the chosen meme.
    The AI decides what images to search for based on the text content.
    """
    print("\n  🖼  PHASE 1d — Generating image search queries from meme text...")

    llm = get_llm()

    prompt = f"""You are an expert at finding the PERFECT meme images.
Given the meme text below, generate Google Image search queries.

EXPECTATION TEXT: "{meme['expectation_text']}"
REALITY TEXT: "{meme['reality_text']}"
EMOTION: {meme.get('emotion', 'relatable humor')}

RULES FOR SEARCH QUERIES:
- EXPECTATION image: Should look cinematic, cool, aspirational. Think Bollywood movie scene, hero moment.
  Use keywords like: "Bollywood scene", "cinematic shot", "hero moment", "action pose"
  Add the specific action from the text.
- REALITY image: Should look exhausted, done, funny, or painfully real.
  Prefer celebrity meme faces (Indian celebrities work best for Indian audience).
  Think: "tired Indian man meme", "done face", "confused expression"
  Add the specific emotion/action from the text.

CRITICAL: Avoid search terms that might return images with:
- Watermarks from other pages
- Text overlays
- Low resolution images
- Logos

Return ONLY valid JSON:
{{
  "expectation_query": "specific search query for expectation image",
  "expectation_keywords": ["keyword1", "keyword2"],
  "reality_query": "specific search query for reality image",
  "reality_keywords": ["keyword1", "keyword2"],
  "notes": "Any special instructions for image selection"
}}"""

    try:
        result = llm.text_json(
            [{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=400,
        )
        print(f"  🔍 Expectation: \"{result['expectation_query']}\"")
        print(f"  🔍 Reality: \"{result['reality_query']}\"")
        return result
    except Exception as e:
        print(f"  ❌ Query generation failed: {e}")
        # Fallback: simple queries from the text
        return {
            "expectation_query": meme["expectation_text"][:50],
            "reality_query": meme["reality_text"][:50],
            "notes": "fallback queries from meme text"
        }


def run_content_pipeline(topic=None):
    """
    Full content generation pipeline.
    Returns: (chosen_meme_dict, image_search_queries)
    """
    # Step 1: Generate concepts
    concepts = generate_concepts(topic)

    # Step 2: Score and pick top 3
    eval1 = score_and_pick(concepts)
    top3_ids = eval1.get("top_3_ids", [])

    # Step 3: Second opinion → final pick
    best_meme = second_opinion(concepts, top3_ids)

    # Step 4: Generate image search queries
    queries = get_image_search_queries(best_meme)

    return best_meme, queries
