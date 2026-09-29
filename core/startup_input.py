"""
core/startup_input.py — Startup input data model.

Defines the validated, typed representation of the data a user submits
through the input form.  All downstream modules depend on this model —
never on raw Streamlit widget values.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class StartupInput:
    """Immutable container for startup details provided by the user.

    Attributes:
        startup_name:  Name of the startup.
        startup_idea:  Description of the product or service idea.
        industry:      Industry vertical (matches INDUSTRIES constant).
        country:       Country of operation (matches COUNTRIES constant).
        budget:        Estimated budget range (matches BUDGET_OPTIONS constant).
        startup_stage: Current stage of the startup (matches STARTUP_STAGES).
    """

    startup_name: str
    startup_idea: str
    industry: str
    country: str
    budget: str
    startup_stage: str

    def to_context_string(self) -> str:
        """Return a human-readable summary suitable for injection into prompts."""
        return (
            f"Startup Name: {self.startup_name}\n"
            f"Idea: {self.startup_idea}\n"
            f"Industry: {self.industry}\n"
            f"Country: {self.country}\n"
            f"Budget: {self.budget}\n"
            f"Stage: {self.startup_stage}"
        )
