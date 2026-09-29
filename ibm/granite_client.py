"""
ibm/granite_client.py — IBM Granite prompt execution and response handling.

Responsibilities:
    - Send a prompt to IBM Granite via the watsonx SDK
    - Read all generation parameters from settings (no hardcoded values)
    - Log request duration for performance visibility
    - Retry up to 3 times on transient failures with exponential back-off
    - Raise typed exceptions so callers can handle auth vs generation errors
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
from ibm_watsonx_ai.foundation_models import ModelInference

from config.settings import settings
from ibm.authentication import get_watsonx_client, WatsonxAuthenticationError

logger = logging.getLogger(__name__)


class GraniteGenerationError(Exception):
    """Raised when IBM Granite fails to generate a response."""


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(GraniteGenerationError),
    reraise=True,
)
def generate(prompt: str, params: Optional[dict] = None) -> str:
    """Send a prompt to IBM Granite and return the generated text.

    Generation parameters are read from :data:`config.settings.settings`
    so they are tuneable through environment variables without touching
    source code.  The caller may pass ``params`` to override individual
    values for a specific request.

    Retries up to 3 times with exponential back-off on transient failures.

    Args:
        prompt: The fully assembled prompt string.
        params: Optional dict to override individual generation parameters.
                Keys must be :class:`~ibm_watsonx_ai.metanames.GenTextParamsMetaNames`
                constants.

    Returns:
        The generated text response from IBM Granite.

    Raises:
        WatsonxAuthenticationError: When IBM credentials are absent or invalid.
        GraniteGenerationError:     When generation fails after all retries.
    """
    generation_params = {**settings.granite_params, **(params or {})}

    try:
        client = get_watsonx_client()

        logger.info(
            "Granite request — model=%s, max_tokens=%s, temperature=%s",
            settings.granite_model_id,
            generation_params.get("max_new_tokens"),
            generation_params.get("temperature"),
        )

        model = ModelInference(
            model_id=settings.granite_model_id,
            api_client=client,
            params=generation_params,
            project_id=settings.ibm_project_id,
        )

        t_start = time.perf_counter()
        response = model.generate_text(prompt=prompt)
        elapsed = time.perf_counter() - t_start

        logger.info(
            "Granite response received — %d chars in %.1fs.",
            len(response),
            elapsed,
        )
        return response

    except WatsonxAuthenticationError:
        raise
    except Exception as exc:
        logger.warning("Granite generation attempt failed: %s", exc)
        raise GraniteGenerationError(
            f"IBM Granite failed to generate a response: {exc}"
        ) from exc
