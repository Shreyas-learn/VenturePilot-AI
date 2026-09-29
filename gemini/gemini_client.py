"""
gemini/gemini_client.py — Google Gemini API prompt execution and response handling.

Responsibilities:
    - Send a prompt to Google Gemini via the official google-genai SDK
    - Read all generation parameters from settings (no hardcoded values)
    - Log request duration for performance visibility
    - Retry up to 3 times on transient failures with exponential back-off
    - Raise typed exceptions so callers can handle auth vs generation errors

This module is the ONLY place in the application that imports or calls
google.genai.  All other modules call gemini_client.generate(prompt).

Drop-in replacement for the old ibm/granite_client.py interface.
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
# Typed exceptions (mirror the old IBM exception names so callers need
# minimal changes)
# ---------------------------------------------------------------------------

class GeminiAuthenticationError(Exception):
    """Raised when the Gemini API key is missing or authentication fails."""


class GeminiGenerationError(Exception):
    """Raised when Gemini fails to generate a response."""


# ---------------------------------------------------------------------------
# Lazy client singleton — created once, reused across calls
# ---------------------------------------------------------------------------

_gemini_client = None


def _get_client():
    """Return a cached google.genai Client instance.

    Created lazily on first call and reused for the process lifetime.
    Raises GeminiAuthenticationError when GEMINI_API_KEY is absent.

    Returns:
        An authenticated google.genai.Client instance.

    Raises:
        GeminiAuthenticationError: When the API key is missing or invalid.
    """
    global _gemini_client

    if _gemini_client is not None:
        return _gemini_client

    api_key = settings.gemini_api_key
    if not api_key:
        raise GeminiAuthenticationError(
            "GEMINI_API_KEY is not set. "
            "Please add it to your .env file or Streamlit Cloud secrets."
        )

    try:
        from google import genai  # type: ignore
        _gemini_client = genai.Client(api_key=api_key)
        logger.info(
            "Gemini client initialised — model=%s, max_tokens=%s, temperature=%s",
            settings.gemini_model,
            settings.gemini_max_output_tokens,
            settings.gemini_temperature,
        )
        return _gemini_client
    except ImportError as exc:
        raise GeminiAuthenticationError(
            "google-genai package is not installed. "
            "Run: pip install google-genai"
        ) from exc
    except Exception as exc:
        raise GeminiAuthenticationError(
            f"Failed to initialise Gemini client: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Retry decorator — retries only transient GeminiGenerationError
# ---------------------------------------------------------------------------

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=4, max=30),
    retry=retry_if_exception_type(GeminiGenerationError),
    reraise=True,
)
def generate(prompt: str, params: Optional[dict] = None) -> str:
    """Send a prompt to Google Gemini and return the generated text.

    Generation parameters are read from :data:`config.settings.settings`
    so they are tuneable through environment variables without touching
    source code.

    Retries up to 3 times with exponential back-off on transient failures.
    Authentication errors are NOT retried (they propagate immediately).

    Args:
        prompt: The fully assembled prompt string (includes startup context
                and RAG context — built by core/prompt_loader.py).
        params: Optional dict to override individual generation parameters
                for a specific request (currently unused, reserved for
                future per-call tuning).

    Returns:
        The generated text response from Google Gemini.

    Raises:
        GeminiAuthenticationError: When the API key is absent or invalid.
        GeminiGenerationError:     When generation fails after all retries.
    """
    # Authentication errors must NOT be retried — surface immediately
    try:
        client = _get_client()
    except GeminiAuthenticationError:
        raise

    try:
        from google.genai import types  # type: ignore

        generation_config = types.GenerateContentConfig(
            temperature=settings.gemini_temperature,
            top_p=settings.gemini_top_p,
            max_output_tokens=settings.gemini_max_output_tokens,
        )

        logger.info(
            "Gemini request — model=%s, max_tokens=%s, temperature=%s, "
            "prompt_length=%d chars",
            settings.gemini_model,
            settings.gemini_max_output_tokens,
            settings.gemini_temperature,
            len(prompt),
        )

        t_start = time.perf_counter()

        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=generation_config,
        )

        elapsed = time.perf_counter() - t_start

        # Extract text from response
        text = _extract_text(response)

        logger.info(
            "Gemini response received — %d chars in %.1fs.",
            len(text),
            elapsed,
        )

        return text

    except GeminiAuthenticationError:
        raise
    except Exception as exc:
        error_str = str(exc)

        # Detect permanent auth/quota errors — do NOT retry these
        # 503 / UNAVAILABLE is transient — always retry, never treat as permanent
        transient_keywords = ("503", "unavailable", "high demand", "try again")
        if any(kw in error_str.lower() for kw in transient_keywords):
            logger.warning("Gemini transient 503 — will retry: %s", exc)
            raise GeminiGenerationError(
                f"Gemini is temporarily overloaded (503). Retrying…"
            ) from exc

        permanent_keywords = (
            "api_key", "api key", "invalid", "permission", "403",
            "authentication", "quota_exceeded", "resource_exhausted",
        )
        if any(kw in error_str.lower() for kw in permanent_keywords):
            raise GeminiAuthenticationError(
                f"Gemini API authentication / quota error: {exc}"
            ) from exc

        logger.warning("Gemini generation attempt failed: %s", exc)
        raise GeminiGenerationError(
            f"Gemini failed to generate a response: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _extract_text(response) -> str:
    """Safely extract text from a Gemini GenerateContentResponse.

    Handles both normal responses and edge cases (blocked content,
    empty candidates, missing parts).

    Args:
        response: A google.genai GenerateContentResponse object.

    Returns:
        The generated text string.

    Raises:
        GeminiGenerationError: When no usable text can be extracted.
    """
    try:
        # Primary path: response.text convenience property
        text = response.text
        if text and text.strip():
            return text.strip()
    except Exception:
        pass

    # Fallback: iterate candidates and parts
    try:
        candidates = getattr(response, "candidates", None)
        if candidates:
            for candidate in candidates:
                content = getattr(candidate, "content", None)
                if content:
                    parts = getattr(content, "parts", None)
                    if parts:
                        combined = "".join(
                            getattr(p, "text", "") for p in parts
                        )
                        if combined.strip():
                            return combined.strip()

        # Check for blocked content
        prompt_feedback = getattr(response, "prompt_feedback", None)
        if prompt_feedback:
            block_reason = getattr(prompt_feedback, "block_reason", None)
            if block_reason:
                raise GeminiGenerationError(
                    f"Gemini blocked the prompt — reason: {block_reason}. "
                    "Try rephrasing your startup description."
                )
    except GeminiGenerationError:
        raise
    except Exception as exc:
        raise GeminiGenerationError(
            f"Could not extract text from Gemini response: {exc}"
        ) from exc

    raise GeminiGenerationError(
        "Gemini returned an empty or unusable response. "
        "Please try again — the model may have returned no content."
    )
