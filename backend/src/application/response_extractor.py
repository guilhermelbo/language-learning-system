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
    Extract structured response from raw LLM output.

    Handles various LLM output formats:
    - Clean JSON array
    - Markdown-wrapped JSON (```json blocks)
    - Single object instead of array
    - Wrapped objects (e.g., {"data": [...]})
    - Plain text fallback

    Args:
        raw_llm_output: Raw string output from the LLM

    Returns:
        AssistantResponse with extracted segments, or fallback on parse failure
    """
    if not raw_llm_output or not raw_llm_output.strip():
        logger.warning("Empty LLM output, returning fallback")
        return AssistantResponse.fallback(FALLBACK_MESSAGE_PT)

    try:
        # Step 1: Clean markdown code blocks
        cleaned = _remove_markdown_blocks(raw_llm_output)

        # Step 2: Parse JSON
        parsed = json.loads(cleaned)

        # Step 3: Normalize to list
        segments_data = _normalize_to_list(parsed)

        # Step 4: Create domain entities
        segments = _create_segments(segments_data)

        if not segments:
            logger.warning("No valid segments extracted, returning fallback")
            return AssistantResponse.fallback(FALLBACK_MESSAGE_PT)

        return AssistantResponse(
            segments=tuple(segments),
            raw_content=raw_llm_output
        )

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}. Raw output: {raw_llm_output[:200]}")
        # Use raw output as fallback if it has content
        if raw_llm_output.strip():
            return AssistantResponse.fallback(raw_llm_output.strip())
        return AssistantResponse.fallback(FALLBACK_MESSAGE_PT)

    except Exception as e:
        logger.error(f"Failed to parse LLM output: {e}. Raw: {raw_llm_output[:200]}")
        # Use raw output as fallback if it has content
        if raw_llm_output.strip():
            return AssistantResponse.fallback(raw_llm_output.strip())
        return AssistantResponse.fallback(FALLBACK_MESSAGE_PT)


def _remove_markdown_blocks(text: str) -> str:
    """
    Remove markdown code block markers from text.

    Handles:
    - ```json ... ```
    - ``` ... ```
    - Leading/trailing whitespace

    Args:
        text: Text potentially containing markdown code blocks

    Returns:
        Cleaned text with code block markers removed
    """
    # Remove code block markers (```json or just ```)
    cleaned = re.sub(r'```(?:json)?', '', text)
    return cleaned.strip()


def _normalize_to_list(parsed) -> list:
    """
    Normalize parsed JSON to a list of segment dictionaries.

    Args:
        parsed: Parsed JSON (could be list, dict, or other)

    Returns:
        List of segment dictionaries

    Raises:
        ValueError: If structure cannot be normalized to list
    """
    if isinstance(parsed, list):
        return parsed

    if isinstance(parsed, dict):
        # Check for common wrapping keys
        for key in ['data', 'segments', 'items', 'response']:
            if key in parsed and isinstance(parsed[key], list):
                return parsed[key]
        # Single object, wrap in list
        return [parsed]

    raise ValueError(f"Unexpected JSON structure: {type(parsed)}")


def _create_segments(segments_data: list) -> list[TextSegment]:
    """
    Create TextSegment instances from segment dictionaries.

    Args:
        segments_data: List of dictionaries with text/lang keys

    Returns:
        List of valid TextSegment instances (invalid entries are skipped)
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
