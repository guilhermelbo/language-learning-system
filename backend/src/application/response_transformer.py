"""
Response transformer for converting domain entities to API formats.

Converts AssistantResponse domain entities to format-specific outputs
(e.g., API response dictionaries).
"""

from ..domain.response_entities import AssistantResponse


def transform_to_api_response(response: AssistantResponse) -> dict:
    """
    Transform domain AssistantResponse to API response format.

    Converts the domain entity to a dictionary suitable for API serialization,
    preserving segment information for rich frontend display.

    Args:
        response: Domain AssistantResponse entity

    Returns:
        Dictionary with:
            - ai_text: Combined text from all segments (backward compatible)
            - segments: List of segment dicts with text and lang keys
    """
    segments = [
        {"text": seg.text, "lang": seg.language}
        for seg in response.segments
    ]

    return {
        "ai_text": response.combined_text,
        "segments": segments
    }
