"""
core/report_builder.py — Assembles a structured Report from generated sections.

The ReportBuilder accepts a StartupInput and AI-generated section content,
then produces an immutable Report dataclass ready for rendering and export.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Optional

from core.startup_input import StartupInput
from config.constants import REPORT_SECTIONS

logger = logging.getLogger(__name__)


@dataclass
class Report:
    """Structured container for a fully generated startup blueprint.

    Attributes:
        startup_input:   The original user input that produced this report.
        sections:        Ordered mapping of section name → generated content.
        readiness_score: Overall startup readiness score out of 100, or None.
        score_breakdown: Per-dimension score values (dimension → score).
    """

    startup_input: StartupInput
    sections: Dict[str, str] = field(default_factory=dict)
    readiness_score: Optional[int] = None
    score_breakdown: Dict[str, int] = field(default_factory=dict)

    def get_section(self, name: str) -> str:
        """Return content for a named section, or an empty string if absent.

        Args:
            name: Section name as defined in :data:`config.constants.REPORT_SECTIONS`.

        Returns:
            Section content string, or empty string when not present.
        """
        return self.sections.get(name, "")

    def is_complete(self) -> bool:
        """Return True when all expected report sections have been populated.

        Returns:
            Boolean indicating whether every section in REPORT_SECTIONS is present.
        """
        return all(section in self.sections for section in REPORT_SECTIONS)


class ReportBuilder:
    """Fluent builder for :class:`Report` instances.

    Usage::

        report = (
            ReportBuilder(startup_input)
            .with_sections(sections_dict)
            .with_score(total, breakdown)
            .build()
        )
    """

    def __init__(self, startup_input: StartupInput) -> None:
        self._startup_input = startup_input
        self._sections: Dict[str, str] = {}
        self._readiness_score: Optional[int] = None
        self._score_breakdown: Dict[str, int] = {}

    def with_sections(self, sections: Dict[str, str]) -> "ReportBuilder":
        """Inject AI-generated section content.

        Args:
            sections: Mapping of section name → generated text.

        Returns:
            Self, for method chaining.
        """
        self._sections.update(sections)
        return self

    def with_score(self, score: int, breakdown: Dict[str, int]) -> "ReportBuilder":
        """Inject readiness score and per-dimension breakdown.

        Args:
            score:     Overall score (0–100).
            breakdown: Mapping of dimension name → score value.

        Returns:
            Self, for method chaining.
        """
        self._readiness_score = score
        self._score_breakdown = breakdown
        return self

    def build(self) -> Report:
        """Assemble and return the final :class:`Report`.

        Returns:
            A fully populated Report instance.
        """
        logger.debug(
            "Building report for '%s' — %d section(s), score=%s.",
            self._startup_input.startup_name,
            len(self._sections),
            self._readiness_score,
        )
        return Report(
            startup_input=self._startup_input,
            sections=self._sections,
            readiness_score=self._readiness_score,
            score_breakdown=self._score_breakdown,
        )
