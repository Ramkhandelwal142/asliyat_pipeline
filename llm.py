#!/usr/bin/env python3
"""
THE ASLIYAT — LLM Abstraction Layer
Supports Groq (cloud, free) and Ollama (local, free).
Auto-fallback between providers.
"""

import json, base64, re, time
from pathlib import Path
import requests

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

from config import (
    GROQ_API_KEY, GROQ_TEXT_MODEL, GROQ_VISION_MODEL,
    OLLAMA_BASE_URL, OLLAMA_TEXT_MODEL, OLLAMA_VISION_MODEL, OLLAMA_ENABLED,
    LLM_PRIORITY, COLOR_GOLD
)


def _img_to_b64(path_or_bytes) -> str:
    """Convert image file path or bytes to base64 string."""
    if isinstance(path_or_bytes, (str, Path)):
        with open(path_or_bytes, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return base64.b64encode(path_or_bytes).decode()


def _clean_json(raw: str) -> str:
    """Strip markdown fences from LLM JSON response."""
    raw = raw.strip()
    # Remove ```json ... ``` or ``` ... ```
    raw = re.sub(r"```json\s*", "", raw)
    raw = re.sub(r"```\s*", "", raw)
    return raw.strip()


class LLMProvider:
    """Unified LLM interface with auto-fallback between Groq and Ollama."""

    def __init__(self):
        self.groq_client = None
        self.ollama_available = False
        self._init_providers()

    def _init_providers(self):
        """Initialize available LLM providers."""
        # Check Groq
        if HAS_GROQ and GROQ_API_KEY and GROQ_API_KEY != "your_groq_api_key_here":
            try:
                self.groq_client = Groq(api_key=GROQ_API_KEY)
                # Quick test call
                resp = self.groq_client.chat.completions.create(
                    model=GROQ_TEXT_MODEL,
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=5,
                )
                print("  ✅ Groq connected successfully")
            except Exception as e:
                print(f"  ⚠ Groq init failed: {e}")
                self.groq_client = None
        else:
            if GROQ_API_KEY == "your_groq_api_key_here":
                print("  ℹ Groq: Add your API key in config.py or GROQ_API_KEY env var")
            else:
                print("  ⚠ Groq: groq package not installed. Run: pip install groq")

        # Check Ollama
        if OLLAMA_ENABLED:
            try:
                resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
                if resp.status_code == 200:
                    models = [m["name"] for m in resp.json().get("models", [])]
                    if OLLAMA_TEXT_MODEL in models:
                        self.ollama_available = True
                        print(f"  ✅ Ollama connected — {len(models)} models available")
                    else:
                        print(f"  ⚠ Ollama: Model '{OLLAMA_TEXT_MODEL}' not found. Run: ollama pull {OLLAMA_TEXT_MODEL}")
                else:
                    print("  ⚠ Ollama: Not responding. Is it running?")
            except requests.ConnectionError:
                print("  ⚠ Ollama: Cannot connect. Start it with: ollama serve")

        # Summary
        providers = []
        if self.groq_client:
            providers.append("Groq")
        if self.ollama_available:
            providers.append("Ollama")
        if not providers:
            print("  ❌ No LLM provider available! Set up Groq or Ollama.")
        else:
            print(f"  🔄 Active providers: {', '.join(providers)} (priority: {LLM_PRIORITY})")

    def _should_try(self, provider: str) -> bool:
        """Check if we should try a given provider based on priority."""
        if provider == "groq":
            if LLM_PRIORITY in ("groq_first", "groq_only"):
                return self.groq_client is not None
            elif LLM_PRIORITY == "ollama_first":
                return not self.ollama_available and self.groq_client is not None
        elif provider == "ollama":
            if LLM_PRIORITY in ("ollama_first", "ollama_only"):
                return self.ollama_available
            elif LLM_PRIORITY == "groq_first":
                return not self.groq_client and self.ollama_available
        return False

    def _try_ollama(self) -> bool:
        return self.ollama_available and LLM_PRIORITY != "groq_only"

    def text(self, messages: list, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """Send text-only messages. Auto-fallback between providers."""
        # Try primary provider first
        if self.groq_client and self._should_try("groq"):
            try:
                return self._groq_text(messages, temperature, max_tokens)
            except Exception as e:
                print(f"  ⚠ Groq text failed: {e}")

        # Fallback
        if self.ollama_available and LLM_PRIORITY != "groq_only":
            try:
                return self._ollama_text(messages, temperature)
            except Exception as e:
                print(f"  ⚠ Ollama text failed: {e}")

        raise RuntimeError("No LLM provider available for text generation")

    def vision(self, messages: list, max_tokens: int = 800) -> str:
        """Send vision (image + text) messages. Auto-fallback."""
        if self.groq_client and self._should_try("groq"):
            try:
                return self._groq_vision(messages, max_tokens)
            except Exception as e:
                print(f"  ⚠ Groq vision failed: {e}")

        if self.ollama_available and LLM_PRIORITY != "groq_only":
            try:
                return self._ollama_vision(messages)
            except Exception as e:
                print(f"  ⚠ Ollama vision failed: {e}")

        raise RuntimeError("No LLM provider available for vision")

    # ── Groq Implementations ───────────────────────────

    def _groq_text(self, messages, temperature, max_tokens):
        resp = self.groq_client.chat.completions.create(
            model=GROQ_TEXT_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content

    def _groq_vision(self, messages, max_tokens):
        resp = self.groq_client.chat.completions.create(
            model=GROQ_VISION_MODEL,
            messages=messages,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content

    # ── Ollama Implementations ─────────────────────────

    def _ollama_text(self, messages, temperature):
        # Convert OpenAI-format messages to Ollama format
        ollama_messages = []
        for m in messages:
            content = m.get("content", "")
            if isinstance(content, str):
                ollama_messages.append({"role": m["role"], "content": content})
            elif isinstance(content, list):
                # Extract text parts only for non-vision calls
                text_parts = [p["text"] for p in content if p.get("type") == "text"]
                ollama_messages.append({"role": m["role"], "content": "\n".join(text_parts)})

        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": OLLAMA_TEXT_MODEL,
                "messages": ollama_messages,
                "stream": False,
                "options": {"temperature": temperature},
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]

    def _ollama_vision(self, messages):
        ollama_messages = []
        for m in messages:
            content = m.get("content", "")
            if isinstance(content, str):
                ollama_messages.append({"role": m["role"], "content": content})
            elif isinstance(content, list):
                # Build content with images for Ollama
                text_parts = []
                images = []
                for p in content:
                    if p.get("type") == "text":
                        text_parts.append(p["text"])
                    elif p.get("type") == "image_url":
                        url = p["image_url"]["url"]
                        # Extract base64 from data URL
                        if url.startswith("data:image"):
                            b64 = url.split(",", 1)[1]
                            images.append(b64)
                        else:
                            # Download and convert
                            try:
                                r = requests.get(url, timeout=10)
                                images.append(base64.b64encode(r.content).decode())
                            except:
                                pass
                msg = {"role": m["role"], "content": "\n".join(text_parts)}
                if images:
                    msg["images"] = images
                ollama_messages.append(msg)

        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": OLLAMA_VISION_MODEL,
                "messages": ollama_messages,
                "stream": False,
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]

    def text_json(self, messages: list, temperature: float = 0.7, max_tokens: int = 2000) -> dict:
        """Text call that expects JSON response. Parses and returns dict."""
        raw = self.text(messages, temperature, max_tokens)
        try:
            return json.loads(_clean_json(raw))
        except json.JSONDecodeError as e:
            print(f"  ⚠ JSON parse failed, retrying...")
            # Retry once with stronger instruction
            messages[-1]["content"] = str(messages[-1]["content"]) + "\n\nIMPORTANT: Return ONLY valid JSON. No other text."
            raw2 = self.text(messages, temperature, max_tokens)
            try:
                return json.loads(_clean_json(raw2))
            except:
                print(f"  ⚠ JSON parse failed twice. Raw response:\n{raw[:300]}")
                raise

    def vision_json(self, messages: list, max_tokens: int = 800) -> dict:
        """Vision call that expects JSON response. Parses and returns dict."""
        raw = self.vision(messages, max_tokens)
        try:
            return json.loads(_clean_json(raw))
        except json.JSONDecodeError:
            print(f"  ⚠ Vision JSON parse failed. Raw: {raw[:200]}")
            return {}


# ── Singleton ─────────────────────────────────────────
_llm_instance = None

def get_llm() -> LLMProvider:
    """Get or create the singleton LLM provider."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LLMProvider()
    return _llm_instance
