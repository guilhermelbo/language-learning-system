"""
Unit tests for domain response entities.
"""

import pytest
from datetime import datetime
from src.domain.response_entities import TextSegment, AssistantResponse


class TestTextSegment:
    """Tests for TextSegment entity."""

    def test_create_valid_segment(self):
        """TextSegment should be created with valid inputs."""
        segment = TextSegment(text="Hello", language="en", order=0)
        assert segment.text == "Hello"
        assert segment.language == "en"
        assert segment.order == 0

    def test_segment_is_immutable(self):
        """TextSegment should be frozen (immutable)."""
        segment = TextSegment(text="Hello", language="en", order=0)
        with pytest.raises(AttributeError):
            segment.text = "Changed"

    def test_empty_text_raises_error(self):
        """TextSegment should reject empty text."""
        with pytest.raises(ValueError, match="text cannot be empty"):
            TextSegment(text="", language="en", order=0)

    def test_whitespace_only_text_raises_error(self):
        """TextSegment should reject whitespace-only text."""
        with pytest.raises(ValueError, match="text cannot be empty"):
            TextSegment(text="   ", language="en", order=0)

    def test_negative_order_raises_error(self):
        """TextSegment should reject negative order values."""
        with pytest.raises(ValueError, match="order must be non-negative"):
            TextSegment(text="Hello", language="en", order=-1)

    def test_zero_order_is_valid(self):
        """TextSegment should accept order=0."""
        segment = TextSegment(text="Hello", language="en", order=0)
        assert segment.order == 0


class TestAssistantResponse:
    """Tests for AssistantResponse entity."""

    def test_create_valid_response(self):
        """AssistantResponse should be created with valid segments."""
        seg1 = TextSegment(text="Olá", language="pt", order=0)
        seg2 = TextSegment(text="Hello", language="en", order=1)
        response = AssistantResponse(
            segments=(seg1, seg2),
            raw_content='[{"text": "Olá", "lang": "pt"}, {"text": "Hello", "lang": "en"}]'
        )
        assert len(response.segments) == 2
        assert response.segments[0].text == "Olá"
        assert response.segments[1].text == "Hello"

    def test_response_is_immutable(self):
        """AssistantResponse should be frozen (immutable)."""
        seg = TextSegment(text="Hello", language="en", order=0)
        response = AssistantResponse(segments=(seg,), raw_content="Hello")
        with pytest.raises(AttributeError):
            response.raw_content = "Changed"

    def test_combined_text_property(self):
        """combined_text should join all segment texts."""
        seg1 = TextSegment(text="Olá", language="pt", order=0)
        seg2 = TextSegment(text="Hello", language="en", order=1)
        response = AssistantResponse(segments=(seg1, seg2), raw_content="")
        assert response.combined_text == "Olá Hello"

    def test_combined_text_single_segment(self):
        """combined_text should work with single segment."""
        seg = TextSegment(text="Hello", language="en", order=0)
        response = AssistantResponse(segments=(seg,), raw_content="")
        assert response.combined_text == "Hello"

    def test_portuguese_text_property(self):
        """portuguese_text should return only PT segments."""
        seg1 = TextSegment(text="Olá", language="pt", order=0)
        seg2 = TextSegment(text="Hello", language="en", order=1)
        seg3 = TextSegment(text="Como vai?", language="pt", order=2)
        response = AssistantResponse(segments=(seg1, seg2, seg3), raw_content="")
        assert response.portuguese_text == "Olá Como vai?"

    def test_english_text_property(self):
        """english_text should return only EN segments."""
        seg1 = TextSegment(text="Olá", language="pt", order=0)
        seg2 = TextSegment(text="Hello", language="en", order=1)
        seg3 = TextSegment(text="How are you?", language="en", order=2)
        response = AssistantResponse(segments=(seg1, seg2, seg3), raw_content="")
        assert response.english_text == "Hello How are you?"

    def test_portuguese_text_empty_when_no_pt_segments(self):
        """portuguese_text should be empty when no PT segments exist."""
        seg = TextSegment(text="Hello", language="en", order=0)
        response = AssistantResponse(segments=(seg,), raw_content="")
        assert response.portuguese_text == ""

    def test_english_text_empty_when_no_en_segments(self):
        """english_text should be empty when no EN segments exist."""
        seg = TextSegment(text="Olá", language="pt", order=0)
        response = AssistantResponse(segments=(seg,), raw_content="")
        assert response.english_text == ""

    def test_fallback_creates_single_segment_response(self):
        """fallback() should create response with single segment."""
        response = AssistantResponse.fallback("Error message", language="pt")
        assert len(response.segments) == 1
        assert response.segments[0].text == "Error message"
        assert response.segments[0].language == "pt"
        assert response.segments[0].order == 0

    def test_fallback_uses_message_as_raw_content(self):
        """fallback() should use message as raw_content."""
        response = AssistantResponse.fallback("Error message")
        assert response.raw_content == "Error message"

    def test_fallback_defaults_to_portuguese(self):
        """fallback() should default to Portuguese language."""
        response = AssistantResponse.fallback("Erro")
        assert response.segments[0].language == "pt"

    def test_created_at_is_set_automatically(self):
        """created_at should be set to current time by default."""
        seg = TextSegment(text="Hello", language="en", order=0)
        before = datetime.now()
        response = AssistantResponse(segments=(seg,), raw_content="")
        after = datetime.now()
        assert before <= response.created_at <= after
