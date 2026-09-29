"""
config/settings.py — Application settings loaded from environment variables.

All external configuration is centralised here. No module in the application
reads os.environ directly — everything comes through this module.

Design rules:
  - Required credentials raise ConfigurationError when absent; they are
    never silently defaulted to an unusable value.
  - Optional tunables have safe, documented defaults.
  - Generation parameters live here so they are tunable without touching
    source code.
"""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


class ConfigurationError(Exception):
    """Raised when required environment variables are missing at startup."""


@dataclass(frozen=True)
class Settings:
    """Immutable application settings resolved at process startup.

    Required credentials are read from the environment. If any are missing,
    call :meth:`validate` (or let :func:`_make_settings` do it) before use.
    """

    # ------------------------------------------------------------------
    # Google Gemini — required at runtime
    # ------------------------------------------------------------------
    gemini_api_key: str = field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY", "")
    )
    # Configurable model — no hardcoded default that may become obsolete.
    # gemini-2.0-flash is the recommended current model (fast, capable).
    gemini_model: str = field(
        default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    )

    # ------------------------------------------------------------------
    # Gemini generation parameters (all configurable via .env)
    # ------------------------------------------------------------------
    # Lower temperature (0.2) for factual, structured business reports
    gemini_temperature: float = field(
        default_factory=lambda: float(os.getenv("GEMINI_TEMPERATURE", "0.2"))
    )
    gemini_top_p: float = field(
        default_factory=lambda: float(os.getenv("GEMINI_TOP_P", "0.9"))
    )
    gemini_max_output_tokens: int = field(
        default_factory=lambda: int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "8192"))
    )

    # ------------------------------------------------------------------
    # RAG pipeline parameters (all configurable via .env)
    # ------------------------------------------------------------------
    rag_chunk_size: int = field(
        default_factory=lambda: int(os.getenv("RAG_CHUNK_SIZE", "800"))
    )
    rag_chunk_overlap: int = field(
        default_factory=lambda: int(os.getenv("RAG_CHUNK_OVERLAP", "150"))
    )
    rag_top_k: int = field(
        default_factory=lambda: int(os.getenv("RAG_TOP_K", "5"))
    )
    rag_similarity_threshold: float = field(
        default_factory=lambda: float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.8"))
    )
    rag_max_context_chars: int = field(
        default_factory=lambda: int(os.getenv("RAG_MAX_CONTEXT_CHARS", "3000"))
    )

    # ------------------------------------------------------------------
    # Embedding provider preference
    # ------------------------------------------------------------------
    # "sentence-transformers" → use local model (recommended; no external API needed)
    preferred_embedding_provider: str = field(
        default_factory=lambda: os.getenv(
            "PREFERRED_EMBEDDING_PROVIDER", "sentence-transformers"
        ).lower().strip()
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    app_env: str = field(
        default_factory=lambda: os.getenv("APP_ENV", "development")
    )
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO")
    )

    # ------------------------------------------------------------------
    # Storage paths
    # ------------------------------------------------------------------
    knowledge_base_path: str = field(
        default_factory=lambda: os.getenv("KNOWLEDGE_BASE_PATH", "knowledge_base")
    )
    chroma_db_path: str = field(
        default_factory=lambda: os.getenv("CHROMA_DB_PATH", "chroma_db")
    )
    exports_dir: str = field(
        default_factory=lambda: os.getenv("EXPORTS_DIR", "exports")
    )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def is_gemini_configured(self) -> bool:
        """Return True when the Gemini API key is present."""
        return bool(self.gemini_api_key)

    def missing_vars(self) -> list[str]:
        """Return the names of required environment variables that are not set.

        Returns:
            List of missing variable name strings, or empty list if all present.
        """
        missing: list[str] = []
        if not self.gemini_api_key:
            missing.append("GEMINI_API_KEY")
        return missing

    def validate(self) -> None:
        """Raise :class:`ConfigurationError` if any required variable is unset.

        Call this once at application startup (before the first Gemini API call)
        so misconfiguration surfaces immediately with a clear message.

        Raises:
            ConfigurationError: Lists every missing variable in the message.
        """
        missing = self.missing_vars()
        if missing:
            raise ConfigurationError(
                "VenturePilot AI cannot start — the following required environment "
                f"variables are not set: {', '.join(missing)}.\n"
                "Please copy .env.example to .env and fill in your Gemini API key "
                "before running the application."
            )

    def is_development(self) -> bool:
        """Return True when running in development mode."""
        return self.app_env.lower() == "development"


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

settings = Settings()
