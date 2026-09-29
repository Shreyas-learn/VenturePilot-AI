"""
ibm/authentication.py — IBM watsonx authentication and client initialisation.

Responsibilities:
    - Validate credentials are present before attempting connection
    - Authenticate with IBM Cloud IAM using the SDK
    - Return a cached, authenticated APIClient singleton
    - Log connection status without exposing credential values
"""

import logging
from functools import lru_cache

from ibm_watsonx_ai import APIClient, Credentials

from config.settings import settings

logger = logging.getLogger(__name__)


class WatsonxAuthenticationError(Exception):
    """Raised when IBM watsonx credentials are missing or authentication fails."""


@lru_cache(maxsize=1)
def get_watsonx_client() -> APIClient:
    """Return an authenticated IBM watsonx API client (process-level singleton).

    The client is created once on first call and cached via ``@lru_cache``.
    Subsequent calls return the same instance without re-authenticating.

    Returns:
        An authenticated :class:`~ibm_watsonx_ai.APIClient` instance.

    Raises:
        WatsonxAuthenticationError: When required credentials are absent
                                    or authentication fails.
    """
    if not settings.is_watsonx_configured():
        raise WatsonxAuthenticationError(
            "IBM watsonx credentials are not fully configured. "
            f"Missing: {', '.join(settings.missing_vars())}. "
            "Please set all required variables in your .env file."
        )

    # Log the URL (non-sensitive) but never the API key
    logger.info(
        "Connecting to IBM watsonx — url=%s, project_id=%s…",
        settings.ibm_url,
        settings.ibm_project_id[:8] + "…" if settings.ibm_project_id else "n/a",
    )

    try:
        credentials = Credentials(
            url=settings.ibm_url,
            api_key=settings.ibm_api_key,
        )
        client = APIClient(
            credentials=credentials,
            project_id=settings.ibm_project_id,
        )
        logger.info(
            "IBM watsonx client authenticated — model: %s.",
            settings.granite_model_id,
        )
        return client

    except Exception as exc:
        raise WatsonxAuthenticationError(
            f"IBM watsonx authentication failed: {exc}"
        ) from exc
