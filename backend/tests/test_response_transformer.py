"""
Unit tests for response transformer.
"""

import pytest
from src.application.response_transformer import transform_to_api_response
from src.domain.response_entities import TextSegment, AssistantResponse


class TestTransformToApiResponse:
    """Tests for transform_to_api_response function."""

    def test_output_structure(self):
        """Should return dict with ai_text and segments keys."""
        seg = TextSegment(text="Hello", language="en", order=0)
        response = AssistantResponse(segments=(seg,), raw_content="")

        result = transform_to_api_response(response)

        assert "ai_text" in result
        assert "segments" in result

    def test_ai_text_is_combined_text(self):
        """Should set ai_text to combined segment texts."""
        seg1 = TextSegment(text="Olá", language="pt", order=0)
        seg2 = TextSegment(text="Hello", language="en", order=1)
        response = AssistantResponse(segments=(seg1, seg2), raw_content="")

        result = transform_to_api_response(response)

        assert result["ai_text"] == "Olá Hello"

    def test_segments_preserves_all_segments(self):
        """Should include all segments in output."""
        seg1 = TextSegment(text="Olá", language="pt", order=0)
        seg2 = TextSegment(text="Hello", language="en", order=1)
        response = AssistantResponse(segments=(seg1, seg2), raw_content="")

        result = transform_to_api_response(response)

        assert len(result["segments"]) == 2

    def test_segment_dict_structure(self):
        """Should format segments as dicts with text and lang keys."""
        seg = TextSegment(text="Hello", language="en", order=0)
        response = AssistantResponse(segments=(seg,), raw_content="")

        result = transform_to_api_response(response)

        assert result["segments"][0] == {"text": "Hello", "lang": "en"}

    def test_preserves_segment_order(self):
        """Should preserve segment order in output."""
        seg1 = TextSegment(text="First", language="en", order=0)
        seg2 = TextSegment(text="Second", language="en", order=1)
        seg3 = TextSegment(text="Third", language="en", order=2)
        response = AssistantResponse(segments=(seg1, seg2, seg3), raw_content="")

        result = transform_to_api_response(response)

        assert result["segments"][0]["text"] == "First"
        assert result["segments"][1]["text"] == "Second"
        assert result["segments"][2]["text"] == "Third"

    def test_handles_single_segment(self):
        """Should handle response with single segment."""
        seg = TextSegment(text="Solo", language="pt", order=0)
        response = AssistantResponse(segments=(seg,), raw_content="")

        result = transform_to_api_response(response)

        assert result["ai_text"] == "Solo"
        assert len(result["segments"]) == 1

    def test_preserves_language_codes(self):
        """Should preserve language codes in output."""
        seg1 = TextSegment(text="Olá", language="pt", order=0)
        seg2 = TextSegment(text="Hello", language="en", order=1)
        response = AssistantResponse(segments=(seg1, seg2), raw_content="")

        result = transform_to_api_response(response)

        assert result["segments"][0]["lang"] == "pt"
        assert result["segments"][1]["lang"] == "en"

    def test_works_with_fallback_response(self):
        """Should handle fallback responses correctly."""
        response = AssistantResponse.fallback("Error message", language="pt")

        result = transform_to_api_response(response)

        assert result["ai_text"] == "Error message"
        assert result["segments"] == [{"text": "Error message", "lang": "pt"}]
