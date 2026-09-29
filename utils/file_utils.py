"""
utils/file_utils.py — File read/write helper functions.

Centralises all direct filesystem access so the rest of the application
never needs to open files manually.
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def read_text_file(path: str) -> str:
    """Read and return the contents of a UTF-8 text file.

    Args:
        path: Absolute or relative path to the file.

    Returns:
        File contents as a string.

    Raises:
        FileNotFoundError: When the file does not exist.
        IOError:           On other read failures.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    content = file_path.read_text(encoding="utf-8")
    logger.debug("Read %d characters from %s", len(content), path)
    return content


def write_text_file(path: str, content: str) -> None:
    """Write a string to a UTF-8 text file, creating parent directories.

    Args:
        path:    Target file path.
        content: Text content to write.
    """
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    logger.debug("Wrote %d characters to %s", len(content), path)


def read_prompt_template(template_name: str) -> str:
    """Load a prompt template from the prompts/ directory.

    Args:
        template_name: Filename without path, e.g. ``"business_blueprint.md"``.

    Returns:
        Template content as a string.

    Raises:
        FileNotFoundError: When the template file does not exist.
    """
    template_path = os.path.join("prompts", template_name)
    return read_text_file(template_path)


def ensure_dir(path: str) -> str:
    """Create a directory (and parents) if it does not already exist.

    Args:
        path: Directory path to ensure.

    Returns:
        The same path, for chaining convenience.
    """
    os.makedirs(path, exist_ok=True)
    return path
