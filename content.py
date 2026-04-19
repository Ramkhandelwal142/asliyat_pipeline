#!/usr/bin/env python3
"""
THE ASLIYAT — Phase 1: Content Generation

FIXES APPLIED:
  Bug #3: Removed Devnagari from example JSON (was contradicting the instruction
          "ROMANIZED HINGLISH ONLY" — LLMs follow examples literally)
  Bug #5: Added polish_meme_text() step after winner selection — converts any
          stray Devnagari, trims overlong text, sharpens Hinglish authenticity
  Bug #6: Improved get_image_search_queries() — more surgical queries that
          target clean images, not watermarked Bollywood stills
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

    prompt = f"""You are the internet's funniest, most sarcastic Indian meme creator. You write brutally relatable 2-panel "Expectation vs Reality" memes for @the_asliyat Instagram page followed by millions of Indian youth.

Topic: "{topic if topic else 'Everyday Indian struggle'}"

RULES FOR HIGH-IQ COMEDY:
1. NO GENERIC DESCRIPTIONS. Use ultra-specific, sarcastic, cinematic phrasing.
   BAD EXPECTATION: "Easily getting in and out of the train"
   GOOD EXPECTATION: "Listening to Arijit Singh and gazing out the window like a Bollywood hero going somewhere important."

   BAD REALITY: "Train is crowded and people fall on each other."
   GOOD REALITY: "Dadar utarte waqt pair zameen par nahi hote, bas bheed ke sahare bahar phek diye jaate hain."

2. ROMANIZED HINGLISH ONLY — use English alphabet for EVERYTHING including Hindi words.
   NEVER use Devnagari script (no unicode Hindi characters at all).
   Write: "paani do" NOT "पानी दो". Write: "yaar" NOT "यार".

3. NATIVE SLANG REQUIRED: Use words like bhai, yaar, kalesh, CTC, jugaad, setting, Virar fast, bhaad mein jao.

4. Keep it to EXACTLY one punchy, hard-hitting sentence per panel. Avoid bloated text.

5. The EXPECTATION should paint an aspirational / cinematic / idealized picture.
   The REALITY should be the gut-punch twist that makes people say "yeh toh main hoon."

Now generate EXACTLY {NUM_CONCEPTS} brilliant, DIVERSE concepts on this topic: "{topic if topic else 'a trending everyday Indian struggle'}"
Make each concept attack the topic from a DIFFERENT angle — different situation, different emotion, different subgroup of audience.

Return ONLY valid JSON (all text in Roman script, zero Devnagari):
{{
  "topic": "main topic name",
  "options": [
    {{
      "id": 1,
      "expectation_text": "Running like Rocky Balboa on Marine Drive, wind in hair, full filmy vibe.",
      "reality_text": "2 minutes run karo toh saans aur self-respect dono chale jaate hain.",
      "emotion": "self-deprecating fitness humor",
      "relatability": "everyone has tried running once after watching a motivational reel",
      "target_demo": "18-28 gym beginners",
      "tag_potential": "people will tag their gym buddy"
    }}
  ]
}}"""

    try:
        result = llm.text_json(
            [{"role": "user", "content": prompt}],
            temperature=CONTENT_TEMPERATURE,
            max_tokens=4000,
        )
        options = result.get("options", [])
        if len(options) < NUM_CONCEPTS:
            print(f"  ⚠ Got {len(options)} options instead of {NUM_CONCEPTS}, continuing...")
        else:
            print(f"  ✓ Generated {len(options)} meme concepts")
        print(f"  📌 Topic: {result.get('topic', 'N/A')}")
        return result
    except Exception as e:
        print(f"  ✗ Concept generation failed: {e}")
        raise


def score_and_pick(concepts: dict) -> dict:
    """
    Round 1 scoring: Rate each concept on multiple dimensions.
    Returns scores and top 3 IDs.
    """
    print("\n  🏆 PHASE 1b — Scoring viral potential (Round 1)...")

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
2. **humor_punch** — Is the contrast between expectation and reality sharp and surprising?
3. **share_urge** — Will someone save this or send it to a friend right now?
4. **hinglish_flow** — Does the Hindi-English mix feel natural, how real people actually talk?
5. **tag_potential** — Will people tag someone specific ("yeh tu hai" energy)?

BONUS points for:
- Bollywood/pop culture references that land perfectly
- Daily Indian life moments with hyper-specific detail
- Moment-of-truth humor (salary day, exam results, marriage talks, office life)
- Phrases that become quotable ("yeh toh main hoon" reaction)

OPTIONS TO SCORE:
{options_text}

Return ONLY valid JSON:
{{
  "scores": [
    {{"id": 1, "relatability": 9, "humor_punch": 8, "share_urge": 9, "hinglish_flow": 9, "tag_potential": 8, "total": 43}}
  ],
  "top_3_ids": [3, 1, 7],
  "best_id": 3,
  "reason": "Why this one will go viral — be specific about what emotion it triggers"
}}"""

    try:
        result = llm.text_json(
            [{"role": "user", "content": prompt}],
            temperature=SCORING_TEMPERATURE,
            max_tokens=2000,
        )
        top3 = result.get("top_3_ids", [])
        best = result.get("best_id", "unknown")
        reason = result.get("reason", "N/A")

        for s in result.get("scores", []):
            if s["id"] in top3:
                marker = " 🏆" if s["id"] == best else ""
                print(f"     #{s['id']}: total={s['total']}/50{marker}")

        print(f"  ✓ Round 1 winner: #{best}")
        print(f"  💡 Reason: {reason}")
        return result
    except Exception as e:
        print(f"  ✗ Scoring failed: {e}")
        raise


def second_opinion(concepts: dict, top3_ids: list) -> dict:
    """
    Round 2: Final review — picks the absolute best one.
    Acts as a second pair of eyes with a different persona.
    """
    print("\n  🧠 PHASE 1c — Second opinion check (Round 2)...")

    llm = get_llm()

    top3 = [o for o in concepts["options"] if o["id"] in top3_ids]
    if len(top3) == 0:
        top3 = concepts["options"][:3]

    options_text = "\n".join([
        f'[{o["id"]}] E: "{o["expectation_text"]}" | R: "{o["reality_text"]}"\n'
        f'     Emotion: {o.get("emotion", "")} | Why relatable: {o.get("relatability", "")}'
        for o in top3
    ])

    prompt = f"""FINAL JURY — You are the last decision-maker for @the_asliyat meme page.
These 3 options made it past the first round. Pick THE BEST ONE.

Think like an Indian college student scrolling Instagram at 2 AM:
- Which one makes you go "BRO 💀💀💀"?
- Which one would you instantly forward to your WhatsApp group?
- Which one feels like YOUR life, not some AI's idea of Indian life?
- Does the Hinglish feel how real people talk, or does it sound generated?
- Which one has the strongest CONTRAST between expectation and reality?

{options_text}

Pick ONE. Be brutal in your judgment.
Return ONLY valid JSON:
{{
  "final_id": 3,
  "final_reason": "Detailed reason why this is THE one — what specific emotion does it trigger?",
  "emotional_trigger": "What exact feeling does it evoke? (e.g., nostalgic cringe, relatable shame, bittersweet, pure chaos comedy)",
  "audience_reaction": "Predicted comment section reaction in one line"
}}"""

    try:
        result = llm.text_json(
            [{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=400,
        )
        final_id = result["final_id"]

        chosen = None
        for o in concepts["options"]:
            if o["id"] == final_id:
                chosen = o
                break
        if not chosen:
            chosen = top3[0]

        print(f"  ✓ FINAL PICK: #{final_id}")
        print(f"     E: \"{chosen['expectation_text']}\"")
        print(f"     R: \"{chosen['reality_text']}\"")
        print(f"  💡 Trigger: {result.get('emotional_trigger', 'N/A')}")
        print(f"  🎯 Prediction: {result.get('audience_reaction', 'N/A')}")
        return chosen
    except Exception as e:
        print(f"  ✗ Second opinion failed: {e}")
        return top3[0] if top3 else concepts["options"][0]


def polish_meme_text(meme: dict) -> dict:
    """
    FIX #5 — New step: Polish & sharpen the chosen meme text.

    Catches:
    - Any Devnagari that slipped through (converts to Roman)
    - Text that's too long for the template (> 15 words)
    - Hinglish that sounds AI-generated vs authentic
    - Weak phrasing that could be sharper/funnier
    """
    print("\n  ✨ PHASE 1d — Polishing meme text for maximum impact...")

    llm = get_llm()

    prompt = f"""You are the sharp-eyed final editor for @the_asliyat meme page.
Your job: take this meme text and polish it to perfection WITHOUT changing the core concept.

CURRENT TEXT:
- Expectation: "{meme['expectation_text']}"
- Reality: "{meme['reality_text']}"

POLISHING CHECKLIST:
1. ROMANIZED HINGLISH ONLY — if ANY Devnagari characters exist, convert them to Roman
   e.g. "पानी दो yaar" → "paani do yaar"
   
2. LENGTH — max 15 words per panel. If longer, cut aggressively while keeping the punch.
   Shorter is almost always better for memes.

3. SPECIFICITY — replace generic phrases with hyper-specific ones that hit harder
   "very tired" → "aankhein band ho rahi thi bhai"
   "feeling sad" → "chup chap chai pee ke so gaye"

4. HINGLISH AUTHENTICITY — should sound like a 22-year-old typing in a group chat
   NOT like an AI translating English to Hindi
   Use casual shortcuts: "karna tha", "ho gaya", "chal yaar", "kya bolun"

5. THE GUT PUNCH — the REALITY line must land like a surprise twist. 
   If it's predictable, make it more unexpected.

Return ONLY valid JSON:
{{
  "expectation_text": "polished expectation in Roman script only",
  "reality_text": "polished reality in Roman script only",
  "changed": true,
  "changes_made": "brief note on what was improved"
}}"""

    try:
        result = llm.text_json(
            [{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=350,
        )
        new_exp = result.get("expectation_text", "").strip()
        new_real = result.get("reality_text", "").strip()

        if new_exp and new_real:
            meme = dict(meme)  # Don't mutate original
            meme["expectation_text"] = new_exp
            meme["reality_text"] = new_real
            if result.get("changed"):
                print(f"  ✓ Polished: {result.get('changes_made', 'improved')}")
                print(f"     E: \"{new_exp}\"")
                print(f"     R: \"{new_real}\"")
            else:
                print("  ✓ Text already clean — no changes needed")
        return meme
    except Exception as e:
        print(f"  ⚠ Polish step failed ({e}), using original text")
        return meme


def get_image_search_queries(meme: dict) -> dict:
    """
    FIX #6 — Improved image search query generation.

    Old approach generated generic queries like "Bollywood hero cinematic"
    which return watermarked film stills with text overlays.

    New approach:
    - Expectation: clean stock-photo style aspirational imagery
    - Reality: specific Indian meme expressions / authentic relatable moments
    - Avoids watermarked copyrighted content
    """
    print("\n  🖼  PHASE 1e — Generating image search queries...")

    llm = get_llm()

    prompt = f"""You are an expert at finding the PERFECT images for Indian Instagram memes.

MEME CONTENT:
- EXPECTATION: "{meme['expectation_text']}"
- REALITY: "{meme['reality_text']}"
- EMOTION: {meme.get('emotion', 'relatable humor')}

Generate two highly specific image search queries.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXPECTATION IMAGE — should look aspirational, cinematic, CLEAN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Goal: The IDEALIZED version of the situation. Makes viewer think "kash mera bhi aisa hota."

Good query patterns:
- For professional scenarios: "confident professional businessman HD portrait"
- For fitness: "athlete training epic motivation aesthetic"
- For travel: "person scenic mountain view happy adventure"  
- For study: "student focused library aesthetic calm"

Add "HD" or "4K" or "professional photo" to get clean images.
AVOID: "Bollywood" (returns watermarked film stills), "movie scene" (copyrighted)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REALITY IMAGE — should look relatable, tired, or authentically struggling
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Goal: What ACTUALLY happens. Makes viewer say "yeh toh main hoon."

BEST OPTIONS for Indian relatability:
- Specific Indian meme faces: "Ranbir Kapoor done expression meme", "Ranveer Singh shocked meme"
- Relatable reaction shots: "Indian man tired office expression"
- Exhaustion: "person sleeping desk exhausted funny"
- Chaos: "person stressed overwhelmed hair mess"

Indian celebrity meme faces work GREAT — their faces are universally recognizable.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AVOID in both queries:
- "shutterstock" or "getty" in query
- Terms that return images with embedded text/watermarks
- Very niche terms that return 0 results

Return ONLY valid JSON:
{{
  "expectation_query": "specific clean aspirational image search query",
  "reality_query": "specific relatable tired/funny Indian image search query",
  "expectation_context": "what this image should look like",
  "reality_context": "what this image should look like",
  "notes": "any special instructions for image selection"
}}"""

    try:
        result = llm.text_json(
            [{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=500,
        )
        print(f"  📌 Expectation: \"{result['expectation_query']}\"")
        print(f"  📌 Reality: \"{result['reality_query']}\"")
        return result
    except Exception as e:
        print(f"  ✗ Query generation failed: {e}")
        return {
            "expectation_query": meme["expectation_text"][:40] + " aspirational HD",
            "reality_query": meme["reality_text"][:40] + " Indian meme tired face",
            "notes": "fallback queries"
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

    # Step 3: Second opinion — final pick
    best_meme = second_opinion(concepts, top3_ids)

    # Step 4: Polish the text (NEW — Bug #5 fix)
    best_meme = polish_meme_text(best_meme)

    # Step 5: Generate image search queries
    queries = get_image_search_queries(best_meme)

    return best_meme, queries
