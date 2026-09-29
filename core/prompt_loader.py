"""
core/prompt_loader.py — Prompt template loading and assembly.

Responsibilities:
    - Load prompt templates from the prompts/ directory
    - Inject startup context and (optionally) RAG context
    - Return a fully assembled prompt string ready for Google Gemini
    - Handle missing template files with a clear error

Templates use two placeholders:
    {startup_context}  — always injected from StartupInput.to_context_string()
    {rag_context}      — injected when RAG is available; replaced with an
                         empty-context notice when RAG is disabled
"""

import logging

from core.startup_input import StartupInput
from utils.file_utils import read_prompt_template

logger = logging.getLogger(__name__)

_NO_RAG_NOTICE = (
    "[KNOWLEDGE BASE CONTEXT]\n"
    "No knowledge base context available for this query.\n"
    "[END CONTEXT]"
)


def build_prompt(
    template_name: str,
    startup_input: StartupInput,
    rag_context: str = "",
) -> str:
    """Load a prompt template and inject the provided context values.

    Args:
        template_name: Filename of the template, e.g. ``"business_blueprint.md"``.
        startup_input: The validated startup input from the user.
        rag_context:   Retrieved knowledge base context. Pass an empty string
                       when RAG is disabled (Phase 2); the template placeholder
                       will be replaced with a neutral notice.

    Returns:
        A fully assembled prompt string ready to send to Google Gemini.

    Raises:
        FileNotFoundError: When the template file does not exist.
    """
    template = read_prompt_template(template_name)

    context = rag_context.strip() if rag_context.strip() else _NO_RAG_NOTICE

    prompt = template.replace("{startup_context}", startup_input.to_context_string())

    # Only substitute {rag_context} if the placeholder exists in this template
    if "{rag_context}" in prompt:
        prompt = prompt.replace("{rag_context}", context)

    logger.debug(
        "Built prompt from '%s' — %d characters (RAG: %s)",
        template_name,
        len(prompt),
        "yes" if rag_context.strip() else "no",
    )
    return prompt
