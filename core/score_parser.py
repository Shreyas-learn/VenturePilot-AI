"""
core/score_parser.py — Parse Gemini's readiness score response.

Responsibilities:
    - Extract the numeric score table from the raw Gemini text
    - Map dimension names to their integer scores
    - Compute the validated total
    - Return (total_score, score_breakdown) as a typed tuple

The parser is tolerant: if it cannot find a score for a dimension it
defaults to 0 rather than raising, so the application never crashes on
an unexpected model format.
"""

import logging
import re
from typing import Optional

from config.constants import SCORE_DIMENSIONS

logger = logging.getLogger(__name__)

# Matches a Markdown table row such as:
#   | Innovation | 20 | 16 | Strong novel approach |
#   | **TOTAL**  | **100** | **78** | ... |
_ROW_PATTERN = re.compile(
    r"\|\s*\*{0,2}(.+?)\*{0,2}\s*\|\s*\*{0,2}(\d+)\*{0,2}\s*\|\s*\*{0,2}(\d+)\*{0,2}\s*\|",
    re.IGNORECASE,
)

# Matches a plain "Score: 78" or "Total Score: 78" line as fallback
_PLAIN_TOTAL_PATTERN = re.compile(
    r"(?:total\s+)?score[:\s]+(\d+)\s*/?\s*100",
    re.IGNORECASE,
)


def parse_score(raw_text: str) -> tuple[int, dict[str, int]]:
    """Extract readiness score and dimension breakdown from Gemini output.

    Tries two strategies in order:
        1. Parse the Markdown score table row by row.
        2. Fall back to a plain "Score: N / 100" pattern.

    Args:
        raw_text: Full text of the Gemini response containing the score section.

    Returns:
        A tuple of (total_score, breakdown_dict) where:
            - total_score is an int in 0–100.
            - breakdown_dict maps dimension name → score int.
        Returns (0, {}) when no score can be extracted.
    """
    breakdown = _parse_table(raw_text)

    if breakdown:
        total = _sum_breakdown(breakdown)
        # If the model returned a TOTAL row, prefer that value
        total_from_table = _extract_total_row(raw_text)
        if total_from_table is not None:
            total = total_from_table
        logger.info(
            "Score parsed from table — total=%d, dimensions=%s",
            total,
            breakdown,
        )
        return total, breakdown

    # Fallback: plain text score
    plain_total = _extract_plain_total(raw_text)
    if plain_total is not None:
        logger.info("Score parsed from plain text — total=%d", plain_total)
        return plain_total, {}

    logger.warning("Could not extract readiness score from Gemini response.")
    return 0, {}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _parse_table(raw_text: str) -> dict[str, int]:
    """Extract dimension → score mapping from a Markdown table.

    Args:
        raw_text: Full Gemini response text.

    Returns:
        Dict of matched dimension names to their scores, or empty dict.
    """
    breakdown: dict[str, int] = {}
    known_dimensions = list(SCORE_DIMENSIONS.keys())

    for match in _ROW_PATTERN.finditer(raw_text):
        row_label = match.group(1).strip()
        score_str = match.group(3).strip()

        # Skip header rows and TOTAL row — handled separately
        if row_label.upper() in {"DIMENSION", "TOTAL"}:
            continue

        matched_dim = _match_dimension(row_label, known_dimensions)
        if matched_dim:
            try:
                breakdown[matched_dim] = min(
                    int(score_str), SCORE_DIMENSIONS[matched_dim]
                )
            except ValueError:
                logger.debug("Non-numeric score for dimension '%s': %s", row_label, score_str)

    return breakdown


def _extract_total_row(raw_text: str) -> Optional[int]:
    """Extract the TOTAL row value from the score table.

    Args:
        raw_text: Full Gemini response text.

    Returns:
        Integer total, or None if not found.
    """
    total_pattern = re.compile(
        r"\|\s*\*{0,2}TOTAL\*{0,2}\s*\|\s*\*{0,2}100\*{0,2}\s*\|\s*\*{0,2}(\d+)\*{0,2}\s*\|",
        re.IGNORECASE,
    )
    match = total_pattern.search(raw_text)
    if match:
        return min(int(match.group(1)), 100)
    return None


def _extract_plain_total(raw_text: str) -> Optional[int]:
    """Extract a score from a plain-text "Total Score: N / 100" line.

    Args:
        raw_text: Full Gemini response text.

    Returns:
        Integer score, or None.
    """
    match = _PLAIN_TOTAL_PATTERN.search(raw_text)
    if match:
        return min(int(match.group(1)), 100)
    return None


def _sum_breakdown(breakdown: dict[str, int]) -> int:
    """Return the sum of all dimension scores, capped at 100.

    Args:
        breakdown: Dimension → score mapping.

    Returns:
        Integer total in 0–100.
    """
    return min(sum(breakdown.values()), 100)


def _match_dimension(label: str, candidates: list[str]) -> Optional[str]:
    """Case-insensitive fuzzy match of a row label to a known dimension name.

    Args:
        label:      Row label string from the table.
        candidates: Known dimension names from SCORE_DIMENSIONS.

    Returns:
        Matched dimension name string, or None.
    """
    label_clean = re.sub(r"[^a-z0-9 ]", "", label.lower()).strip()

    for candidate in candidates:
        candidate_clean = re.sub(r"[^a-z0-9 ]", "", candidate.lower()).strip()
        # Check first word match
        if candidate_clean.split()[0] in label_clean:
            return candidate
        if label_clean in candidate_clean or candidate_clean in label_clean:
            return candidate
    return None
