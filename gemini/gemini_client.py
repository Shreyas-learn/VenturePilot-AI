"""
gemini/gemini_client.py — LLM generation with automatic provider fallback.

Primary provider:   Google Gemini  (GEMINI_MODEL, default: gemini-2.5-flash)
Fallback 1:         Google Gemini  (GEMINI_FALLBACK_MODEL, default: gemini-1.5-flash)
Fallback 2:         Groq           (GROQ_API_KEY + GROQ_MODEL, optional)

When the primary model returns a transient error (503, overloaded, timeout),
the client automatically tries the next provider in order without user action.

The public interface is a single function:

    generate(prompt)  →  str

All other modules call only this function — they never know which provider
actually ran the request.
"""

import logging
import time
from typing import Optional

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config.settings import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Typed exceptions
# ---------------------------------------------------------------------------

class GeminiAuthenticationError(Exception):
    """Raised when all providers fail due to missing/invalid credentials."""


class GeminiGenerationError(Exception):
    """Raised when a single provider attempt fails (transient — retried)."""


class AllProvidersFailedError(Exception):
    """Raised when every provider in the fallback chain has been exhausted."""


# ---------------------------------------------------------------------------
# Lazy client singletons
# ---------------------------------------------------------------------------

_gemini_client = None
_groq_client   = None


def _get_gemini_client():
    """Return a cached google.genai Client, or raise GeminiAuthenticationError."""
    global _gemini_client
    if _gemini_client is not None:
        return _gemini_client

    api_key = settings.gemini_api_key
    if not api_key:
        raise GeminiAuthenticationError(
            "GEMINI_API_KEY is not set. "
            "Add it to your .env file or Streamlit Cloud secrets."
        )
    try:
        from google import genai  # type: ignore
        _gemini_client = genai.Client(api_key=api_key)
        logger.info("Gemini client initialised.")
        return _gemini_client
    except ImportError as exc:
        raise GeminiAuthenticationError(
            "google-genai package is not installed. Run: pip install google-genai"
        ) from exc
    except Exception as exc:
        raise GeminiAuthenticationError(
            f"Failed to initialise Gemini client: {exc}"
        ) from exc


def _get_groq_client():
    """Return a cached Groq client, or None if Groq is not configured."""
    global _groq_client
    if _groq_client is not None:
        return _groq_client

    api_key = settings.groq_api_key
    if not api_key:
        return None
    try:
        from groq import Groq  # type: ignore
        _groq_client = Groq(api_key=api_key)
        logger.info("Groq client initialised — model=%s.", settings.groq_model)
        return _groq_client
    except ImportError:
        logger.warning("groq package not installed — Groq fallback unavailable.")
        return None
    except Exception as exc:
        logger.warning("Failed to initialise Groq client: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Public entry point — fallback chain
# ---------------------------------------------------------------------------

def generate(prompt: str, params: Optional[dict] = None) -> str:
    """Generate text from a prompt, with automatic fallback across providers.

    Tries providers in order:
        1. Gemini primary model   (GEMINI_MODEL)
        2. Gemini fallback model  (GEMINI_FALLBACK_MODEL)
        3. Groq                   (GROQ_API_KEY + GROQ_MODEL, if configured)

    Args:
        prompt: Fully assembled prompt string (startup context + RAG context).
        params: Reserved for future use.

    Returns:
        Generated text string from whichever provider succeeded.

    Raises:
        GeminiAuthenticationError: When GEMINI_API_KEY is missing.
        AllProvidersFailedError:   When every provider has been exhausted.
    """
    errors: list[str] = []

    # ── 1. Primary Gemini model ──────────────────────────────────────────────
    try:
        logger.info("Attempting primary model: %s", settings.gemini_model)
        return _call_gemini_with_retry(settings.gemini_model, prompt)
    except GeminiAuthenticationError:
        raise  # auth failure — no point trying other models with same key
    except Exception as exc:
        logger.warning("Primary model failed: %s", exc)
        errors.append(f"Primary ({settings.gemini_model}): {exc}")

    # ── 2. Gemini fallback model ─────────────────────────────────────────────
    if settings.gemini_fallback_model and settings.gemini_fallback_model != settings.gemini_model:
        try:
            logger.info("Trying fallback Gemini model: %s", settings.gemini_fallback_model)
            return _call_gemini_with_retry(settings.gemini_fallback_model, prompt)
        except GeminiAuthenticationError:
            raise
        except Exception as exc:
            logger.warning("Fallback Gemini model failed: %s", exc)
            errors.append(f"Fallback Gemini ({settings.gemini_fallback_model}): {exc}")

    # ── 3. Groq ──────────────────────────────────────────────────────────────
    groq_client = _get_groq_client()
    if groq_client:
        try:
            logger.info("Trying Groq fallback: %s", settings.groq_model)
            return _call_groq(groq_client, prompt)
        except Exception as exc:
            logger.warning("Groq fallback failed: %s", exc)
            errors.append(f"Groq ({settings.groq_model}): {exc}")

    # ── All providers exhausted ───────────────────────────────────────────────
    summary = " | ".join(errors)
    raise AllProvidersFailedError(
        f"All AI providers are currently unavailable. Please try again in a few minutes.\n"
        f"Details: {summary}"
    )


# ---------------------------------------------------------------------------
# Per-provider call implementations
# ---------------------------------------------------------------------------

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=4, max=20),
    retry=retry_if_exception_type(GeminiGenerationError),
    reraise=True,
)
def _call_gemini_with_retry(model: str, prompt: str) -> str:
    """Call a specific Gemini model with retry on transient errors."""
    try:
        client = _get_gemini_client()
    except GeminiAuthenticationError:
        raise

    try:
        from google.genai import types  # type: ignore

        config = types.GenerateContentConfig(
            temperature=settings.gemini_temperature,
            top_p=settings.gemini_top_p,
            max_output_tokens=settings.gemini_max_output_tokens,
        )

        t_start = time.perf_counter()
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config,
        )
        elapsed = time.perf_counter() - t_start

        text = _extract_gemini_text(response)
        logger.info("Gemini (%s) responded — %d chars in %.1fs.", model, len(text), elapsed)
        return text

    except GeminiAuthenticationError:
        raise
    except Exception as exc:
        error_str = str(exc)

        # 503 / overloaded → transient, retry
        if any(kw in error_str.lower() for kw in ("503", "unavailable", "high demand", "overload")):
            logger.warning("Gemini %s transient 503 — retrying: %s", model, exc)
            raise GeminiGenerationError(f"Gemini {model} overloaded (503).") from exc

        # 404 / not found → model deprecated, don't retry
        if any(kw in error_str.lower() for kw in ("404", "not_found", "no longer available")):
            raise Exception(f"Gemini model {model} not found (404): {exc}") from exc

        # auth / quota → permanent
        if any(kw in error_str.lower() for kw in ("api_key", "invalid", "403", "permission", "quota_exceeded")):
            raise GeminiAuthenticationError(f"Gemini auth/quota error: {exc}") from exc

        logger.warning("Gemini %s error: %s", model, exc)
        raise GeminiGenerationError(f"Gemini {model} failed: {exc}") from exc


def _call_groq(client, prompt: str) -> str:
    """Call Groq API with the configured model."""
    t_start = time.perf_counter()
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=settings.gemini_temperature,
        max_tokens=settings.gemini_max_output_tokens,
    )
    elapsed = time.perf_counter() - t_start
    text = response.choices[0].message.content or ""
    if not text.strip():
        raise Exception("Groq returned an empty response.")
    logger.info("Groq (%s) responded — %d chars in %.1fs.", settings.groq_model, len(text), elapsed)
    return text.strip()


# ---------------------------------------------------------------------------
# Gemini response text extraction
# ---------------------------------------------------------------------------

def _extract_gemini_text(response) -> str:
    """Safely extract text from a Gemini GenerateContentResponse."""
    try:
        text = response.text
        if text and text.strip():
            return text.strip()
    except Exception:
        pass

    try:
        candidates = getattr(response, "candidates", None)
        if candidates:
            for candidate in candidates:
                content = getattr(candidate, "content", None)
                if content:
                    parts = getattr(content, "parts", None)
                    if parts:
                        combined = "".join(getattr(p, "text", "") for p in parts)
                        if combined.strip():
                            return combined.strip()

        prompt_feedback = getattr(response, "prompt_feedback", None)
        if prompt_feedback:
            block_reason = getattr(prompt_feedback, "block_reason", None)
            if block_reason:
                raise GeminiGenerationError(
                    f"Gemini blocked the prompt — reason: {block_reason}."
                )
    except GeminiGenerationError:
        raise
    except Exception as exc:
        raise GeminiGenerationError(f"Could not extract Gemini response text: {exc}") from exc

    raise GeminiGenerationError("Gemini returned an empty response.")
