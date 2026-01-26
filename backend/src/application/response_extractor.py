"""
Content extractor for LLM responses.

Extracts structured content from raw LLM output,
handling various output formats and edge cases.
"""

import json
import re
import logging
from typing import Optional

from ..domain.response_entities import TextSegment, AssistantResponse

logger = logging.getLogger(__name__)

FALLBACK_MESSAGE_PT = "Desculpe, não consegui gerar uma resposta para isso."
FALLBACK_MESSAGE_EN = "Sorry, I couldn't generate a response for that."


def extract_response(raw_llm_output: str) -> AssistantResponse:
    """
    Extracts a structured `AssistantResponse` from a raw LLM output string.

    This function is designed to be robust against various LLM output formats,
    including clean JSON, markdown-wrapped JSON, and plain text. It attempts
    to parse the structured data and falls back to a simple response if parsing
    fails.

    Args:
        raw_llm_output: The raw string output from the language model.

    Returns:
        An `AssistantResponse` instance containing structured `TextSegment` objects
        if parsing is successful, or a fallback response if it fails.
    """
    if not raw_llm_output or not raw_llm_output.strip():
        logger.warning("Empty LLM output, returning fallback")
        return AssistantResponse.fallback(FALLBACK_MESSAGE_PT)

    try:
        cleaned = _remove_markdown_blocks(raw_llm_output)
        parsed = json.loads(cleaned)
        segments_data = _normalize_to_list(parsed)
        segments = _create_segments(segments_data)

        if not segments:
            logger.warning("No valid segments extracted, returning fallback")
            return AssistantResponse.fallback(FALLBACK_MESSAGE_PT)

        return AssistantResponse(
            segments=tuple(segments),
            raw_content=raw_llm_output
        )
    except (json.JSONDecodeError, ValueError, Exception) as e:
        logger.error(f"Failed to parse LLM output due to {type(e).__name__}: {e}. Raw: {raw_llm_output[:200]}")
        # Use raw output as fallback if it has content, otherwise use a default message.
        fallback_text = raw_llm_output.strip() or FALLBACK_MESSAGE_PT
        return AssistantResponse.fallback(fallback_text)


def _remove_markdown_blocks(text: str) -> str:
    """
    Removes markdown code block fences (```) from a string.

    This handles blocks with or without a language specifier (e.g., ```json).

    Args:
        text: The text potentially containing markdown code blocks.

    Returns:
        The cleaned text with code block markers removed and whitespace stripped.
    """
    # Remove code block markers (```json or just ```)
    cleaned = re.sub(r'```(?:json)?', '', text)
    return cleaned.strip()


def _normalize_to_list(parsed: object) -> list:
    """
    Normalizes a parsed JSON object into a list of segment dictionaries.

    This function handles cases where the LLM returns a single JSON object,
    a list of objects, or an object wrapped in a dictionary key
    (e.g., `{"data": [...]}`).

    Args:
        parsed: The parsed JSON object from `json.loads()`.

    Returns:
        A list of segment dictionaries.

    Raises:
        ValueError: If the parsed structure cannot be normalized to a list.
    """
    if isinstance(parsed, list):
        return parsed

    if isinstance(parsed, dict):
        # Check for common wrapping keys
        for key in ['data', 'segments', 'items', 'response']:
            if key in parsed and isinstance(parsed[key], list):
                return parsed[key]
        # A single object was returned, wrap it in a list
        return [parsed]

    raise ValueError(f"Unexpected JSON structure: cannot normalize type '{type(parsed).__name__}' to a list.")


def _create_segments(segments_data: list) -> list[TextSegment]:
    """
    Converts a list of dictionaries into a list of `TextSegment` instances.

    Invalid dictionaries or dictionaries with empty text are skipped.

    Args:
        segments_data: A list of dictionaries, each expected to contain
                       'text' and 'lang' keys.

    Returns:
        A list of valid `TextSegment` instances.
    """
    segments = []
    for i, seg in enumerate(segments_data):
        if not isinstance(seg, dict):
            logger.warning(f"Skipping non-dict segment at index {i}: {seg}")
            continue

        text = seg.get("text", "").strip()
        lang = seg.get("lang", "pt")

        if not text:
            logger.debug(f"Skipping empty text segment at index {i}")
            continue

        try:
            segments.append(TextSegment(text=text, language=lang, order=i))
        except ValueError as e:
            logger.warning(f"Invalid segment at index {i}: {e}")
            continue

    return segments
