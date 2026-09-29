"""
core/orchestrator.py — Blueprint generation orchestrator.

Coordinates the full report generation workflow:

    StartupInput
        └─► rag_pipeline.get_context()   (domain-specific RAG retrieval)
        └─► build_prompt()               (template + context assembly)
        └─► gemini_client.generate()     (Google Gemini API call)
        └─► _parse_sections()            (Markdown → named sections dict)
        └─► ReportBuilder.build()        (final Report dataclass)

Each prompt template call retrieves its own domain-specific RAG context
so that funding prompts get funding passages, market prompts get market
passages, and so on.
"""

import logging
import re
from typing import Dict

from core.startup_input import StartupInput
from core.report_builder import ReportBuilder, Report
from core.prompt_loader import build_prompt
from core.score_parser import parse_score
from gemini import gemini_client
from gemini.gemini_client import GeminiAuthenticationError, GeminiGenerationError
from rag.rag_pipeline import get_context

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt template → section name mapping
# Each template produces multiple sections; the keys are the exact section
# names defined in config/constants.REPORT_SECTIONS.
# ---------------------------------------------------------------------------

_PROMPT_SECTION_MAP: Dict[str, list[str]] = {
    "business_blueprint.md": [
        "Executive Summary",
        "Problem Statement",
        "Proposed Solution",
        "Vision & Mission",
        "Target Customers",
        "Value Proposition",
        "Business Model Canvas",
        "Revenue Model",
    ],
    "market_analysis.md": [
        "Competitor Analysis",
        "SWOT Analysis",
        "Go-To-Market Strategy",
    ],
    "funding.md": [
        "Estimated Budget",
        "Funding Opportunities",
        "Government Schemes",
        "Incubator Recommendations",
    ],
    "startup_score.md": [
        "12-Month Roadmap",
        "Risks & Mitigation",
        "Startup Readiness Score",
    ],
    "investor_pitch.md": [
        "Final Recommendation",
        "Investor Elevator Pitch",
        "Immediate Next Steps",
    ],
}

# Sections deferred to a future phase
_DEFERRED_SECTIONS = {"Startup Readiness Score"}


def generate_blueprint(startup_input: StartupInput) -> Report:
    """Generate a full startup blueprint for the given input.

    Orchestrates 5 Gemini API calls (one per prompt template), parses the
    responses into named sections, and assembles a Report.

    Args:
        startup_input: Validated startup details submitted by the user.

    Returns:
        A fully populated :class:`Report` instance.

    Raises:
        GeminiAuthenticationError: Propagated when credentials are missing.
        GeminiGenerationError:     Propagated after all retries are exhausted.
    """
    logger.info(
        "Starting blueprint generation — startup='%s', industry='%s', stage='%s'",
        startup_input.startup_name,
        startup_input.industry,
        startup_input.startup_stage,
    )

    all_sections: Dict[str, str] = {}

    for template_name, expected_sections in _PROMPT_SECTION_MAP.items():
        raw_response = _call_gemini(template_name, startup_input)
        if "<br>" in raw_response.lower():
            logger.info("Gemini returned HTML <br> tags — cleaning up.")
        parsed = _parse_sections(raw_response, expected_sections)
        all_sections.update(parsed)

    # Extract readiness score from the startup_score response
    score_raw = all_sections.get("Startup Readiness Score", "")
    total_score, score_breakdown = parse_score(score_raw)

    report = (
        ReportBuilder(startup_input)
        .with_sections(all_sections)
        .with_score(total_score, score_breakdown)
        .build()
    )

    return report


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _call_gemini(template_name: str, startup_input: StartupInput) -> str:
    """Retrieve RAG context, build a prompt, and call Google Gemini.

    The RAG context is retrieved using a domain-specific query built from
    the template name and the startup input.  An empty context string is
    used gracefully when the knowledge base is empty or unavailable.

    Args:
        template_name: Prompt template filename.
        startup_input: Validated startup input for context injection.

    Returns:
        Raw text response from Google Gemini.

    Raises:
        GeminiAuthenticationError: When Gemini credentials are not configured.
        GeminiGenerationError:     When the API call fails after all retries.
    """
    rag_context = get_context(
        template_name=template_name,
        startup_name=startup_input.startup_name,
        industry=startup_input.industry,
        country=startup_input.country,
        startup_idea=startup_input.startup_idea,
    )

    prompt = build_prompt(
        template_name=template_name,
        startup_input=startup_input,
        rag_context=rag_context,
    )
    response = gemini_client.generate(prompt)

    print("=" * 80)
    print(response)
    print("=" * 80)

    return response


def _parse_sections(raw_text: str, expected_sections: list[str]) -> Dict[str, str]:
    """Parse a multi-section Gemini response into a {section_name: content} dict.

    The parser looks for Markdown headings (### or ##) whose text matches
    (case-insensitively, partial) one of the expected section names.

    Unmatched content at the start is discarded. Sections not found in the
    response are omitted from the returned dict so the caller can detect gaps.

    Args:
        raw_text:          Full text response from Google Gemini.
        expected_sections: Ordered list of section names to extract.

    Returns:
        Dict mapping section name → extracted content string.
    """
    sections: Dict[str, str] = {}

    # Split on any Markdown heading line (##, ###, ####)
    heading_pattern = re.compile(r"^##\s+(.+)$", re.MULTILINE)
    parts = heading_pattern.split(raw_text)

    # parts alternates: [pre_text, heading1, body1, heading2, body2, ...]
    # zip pairs heading with its following body
    heading_body_pairs = list(zip(parts[1::2], parts[2::2]))

    for heading, body in heading_body_pairs:
        matched_section = _match_section(heading.strip(), expected_sections)
        body = re.sub(r"<br\s*/?>", "\n", body, flags=re.IGNORECASE)
        if matched_section and matched_section not in sections:
            sections[matched_section] = body.strip()

    # For any expected section not found by heading match, attempt a
    # keyword search as a fallback
    for section in expected_sections:
        if section not in sections:
            fallback = _keyword_fallback(raw_text, section)
            if fallback:
                sections[section] = fallback
                logger.debug("Section '%s' recovered via keyword fallback.", section)
            else:
                logger.warning("Section '%s' not found in Gemini response.", section)

    return sections


def _match_section(heading: str, candidates: list[str]) -> str | None:
    """Find the best matching section name for a heading string.

    Matches are case-insensitive and require the candidate's core keyword
    to appear somewhere within the heading.

    Args:
        heading:    The heading string extracted from Gemini's response.
        candidates: The expected section names for this prompt.

    Returns:
        The matching section name string, or None.
    """
    heading_clean = heading.lower()

    # Remove markdown formatting
    heading_clean = heading_clean.replace("*", "")

    # Remove leading numbering like "14." or "14)"
    heading_clean = re.sub(r"^\s*\d+[\.\)]\s*", "", heading_clean)

    # Normalize punctuation
    heading_clean = re.sub(r"[-–—]", " ", heading_clean)

    # Remove everything except letters/numbers/spaces
    heading_clean = re.sub(r"[^a-z0-9 ]", " ", heading_clean)

    # Collapse repeated spaces
    heading_clean = " ".join(heading_clean.split())

    for candidate in candidates:
        # Use the first 3+ word tokens of the candidate for matching
        key_clean = candidate.lower()

        # Normalize hyphens exactly like headings
        key_clean = re.sub(r"[-‐-–—]", " ", key_clean)

        # Remove everything except letters/numbers/spaces
        key_clean = re.sub(r"[^a-z0-9 ]", " ", key_clean)

        # Collapse spaces
        key_clean = " ".join(key_clean.split())
        if key_clean == heading_clean:
            return candidate

        # Direct substring match
        if key_clean in heading_clean or heading_clean in key_clean:
            return candidate

    return None


def _keyword_fallback(raw_text: str, section_name: str) -> str:
    """Attempt to extract a section by searching the raw text for its name.

    Used when heading-based parsing misses a section. Looks for the section
    name as plain text and extracts the following paragraph.

    Args:
        raw_text:     Full Gemini response text.
        section_name: The section name to search for.

    Returns:
        Extracted text if found, or an empty string.
    """
    # Search for the section name (case-insensitive) as a line or inline
    key = re.escape(section_name.lower().split()[0])
    pattern = re.compile(
        rf"(?i){key}.*?\n((?:.+\n?)+)",
        re.MULTILINE,
    )
    match = pattern.search(raw_text)
    if match:
        return match.group(1).strip()
    return ""
