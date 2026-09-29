"""
utils/logger.py — Centralised logging configuration.

All modules obtain their logger via get_logger(__name__).
Logs are written to both the console and logs/app.log with rotation.

Log format:
    2024-01-15 10:30:00 | INFO     | module.name | message

Sensitive values (API keys, credentials) must NEVER be passed to any
logger call. The logger itself provides no redaction — callers are
responsible for not logging secret data.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

_LOGS_DIR = "logs"
_LOG_FILE = os.path.join(_LOGS_DIR, "app.log")
_MAX_BYTES = 5 * 1024 * 1024   # 5 MB per file
_BACKUP_COUNT = 3               # Keep 3 rotated files

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def _configure_root_logger() -> None:
    """Configure the root logger once at application startup.

    Safe to call multiple times — configuration is applied only once
    due to the module-level ``_configured`` guard.
    """
    global _configured
    if _configured:
        return

    # Read log level from settings without importing at module level
    # (avoids circular dependency during very early startup)
    try:
        from config.settings import settings
        level_str = settings.log_level.upper()
    except Exception:
        level_str = "INFO"

    level = getattr(logging, level_str, logging.INFO)
    formatter = logging.Formatter(_FORMAT, datefmt=_DATE_FORMAT)

    os.makedirs(_LOGS_DIR, exist_ok=True)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    file_handler = RotatingFileHandler(
        _LOG_FILE,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(console_handler)
    root.addHandler(file_handler)

    _configured = True

    # Emit startup banner once
    startup_logger = logging.getLogger("ventpilot.startup")
    startup_logger.info(
        "=" * 60
    )
    startup_logger.info("VenturePilot AI — application starting up.")
    startup_logger.info("Log level: %s | Log file: %s", level_str, _LOG_FILE)
    startup_logger.info(
        "=" * 60
    )


def get_logger(name: str) -> logging.Logger:
    """Return a named logger, configuring the root logger on first call.

    Args:
        name: Typically ``__name__`` of the calling module.

    Returns:
        A configured :class:`logging.Logger` instance.
    """
    _configure_root_logger()
    return logging.getLogger(name)
