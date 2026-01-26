"""
Unit tests for response extractor.
"""

import pytest
from src.application.response_extractor import (
    extract_response,
    _remove_markdown_blocks,
    _normalize_to_list,
    _create_segments,
    FALLBACK_MESSAGE_PT,
)
from src.domain.response_entities import TextSegment


class TestExtractResponse:
    """Tests for extract_response function."""

    def test_valid_json_array(self):
        """Should extract segments from valid JSON array."""
        raw = '[{"text": "Olá", "lang": "pt"}, {"text": "Hello", "lang": "en"}]'
        response = extract_response(raw)

        assert len(response.segments) == 2
        assert response.segments[0].text == "Olá"
        assert response.segments[0].language == "pt"
        assert response.segments[1].text == "Hello"
        assert response.segments[1].language == "en"

    def test_markdown_wrapped_json(self):
        """Should extract segments from markdown-wrapped JSON."""
        raw = '```json\n[{"text": "Olá", "lang": "pt"}]\n```'
        response = extract_response(raw)

        assert len(response.segments) == 1
        assert response.segments[0].text == "Olá"

    def test_markdown_without_json_hint(self):
        """Should extract segments from markdown blocks without json hint."""
        raw = '```\n[{"text": "Olá", "lang": "pt"}]\n```'
        response = extract_response(raw)

        assert len(response.segments) == 1
        assert response.segments[0].text == "Olá"

    def test_single_object_normalization(self):
        """Should wrap single object in array."""
        raw = '{"text": "Olá", "lang": "pt"}'
        response = extract_response(raw)

        assert len(response.segments) == 1
        assert response.segments[0].text == "Olá"

    def test_wrapped_object_with_data_key(self):
        """Should extract from wrapped object with 'data' key."""
        raw = '{"data": [{"text": "Olá", "lang": "pt"}]}'
        response = extract_response(raw)

        assert len(response.segments) == 1
        assert response.segments[0].text == "Olá"

    def test_wrapped_object_with_segments_key(self):
        """Should extract from wrapped object with 'segments' key."""
        raw = '{"segments": [{"text": "Olá", "lang": "pt"}]}'
        response = extract_response(raw)

        assert len(response.segments) == 1
        assert response.segments[0].text == "Olá"

    def test_wrapped_object_with_items_key(self):
        """Should extract from wrapped object with 'items' key."""
        raw = '{"items": [{"text": "Olá", "lang": "pt"}]}'
        response = extract_response(raw)

        assert len(response.segments) == 1
        assert response.segments[0].text == "Olá"

    def test_wrapped_object_with_response_key(self):
        """Should extract from wrapped object with 'response' key."""
        raw = '{"response": [{"text": "Olá", "lang": "pt"}]}'
        response = extract_response(raw)

        assert len(response.segments) == 1
        assert response.segments[0].text == "Olá"

    def test_empty_input_returns_fallback(self):
        """Should return fallback for empty input."""
        response = extract_response("")

        assert len(response.segments) == 1
        assert response.segments[0].text == FALLBACK_MESSAGE_PT
        assert response.segments[0].language == "pt"

    def test_none_input_returns_fallback(self):
        """Should return fallback for None input."""
        response = extract_response(None)

        assert len(response.segments) == 1
        assert response.segments[0].text == FALLBACK_MESSAGE_PT

    def test_whitespace_only_returns_fallback(self):
        """Should return fallback for whitespace-only input."""
        response = extract_response("   \n\t  ")

        assert len(response.segments) == 1
        assert response.segments[0].text == FALLBACK_MESSAGE_PT

    def test_malformed_json_returns_fallback(self):
        """Should return fallback with raw content for malformed JSON."""
        raw = "This is not JSON at all"
        response = extract_response(raw)

        assert len(response.segments) == 1
        assert response.segments[0].text == raw

    def test_partial_json_returns_fallback(self):
        """Should return fallback for partial/broken JSON."""
        raw = '[{"text": "Olá"'  # Missing closing brackets
        response = extract_response(raw)

        assert len(response.segments) == 1
        # Should use raw content as fallback
        assert response.segments[0].text == raw

    def test_preserves_raw_content(self):
        """Should preserve raw content in response."""
        raw = '[{"text": "Olá", "lang": "pt"}]'
        response = extract_response(raw)

        assert response.raw_content == raw

    def test_skips_empty_text_segments(self):
        """Should skip segments with empty text."""
        raw = '[{"text": "", "lang": "pt"}, {"text": "Hello", "lang": "en"}]'
        response = extract_response(raw)

        assert len(response.segments) == 1
        assert response.segments[0].text == "Hello"

    def test_defaults_language_to_pt(self):
        """Should default language to 'pt' if not specified."""
        raw = '[{"text": "Olá"}]'
        response = extract_response(raw)

        assert response.segments[0].language == "pt"

    def test_segment_order_preserved(self):
        """Should preserve segment order."""
        raw = '[{"text": "First", "lang": "en"}, {"text": "Second", "lang": "en"}, {"text": "Third", "lang": "en"}]'
        response = extract_response(raw)

        assert response.segments[0].order == 0
        assert response.segments[1].order == 1
        assert response.segments[2].order == 2


class TestRemoveMarkdownBlocks:
    """Tests for _remove_markdown_blocks helper."""

    def test_removes_json_code_block(self):
        """Should remove ```json markers."""
        text = '```json\n{"key": "value"}\n```'
        result = _remove_markdown_blocks(text)
        assert result == '{"key": "value"}'

    def test_removes_plain_code_block(self):
        """Should remove plain ``` markers."""
        text = '```\n{"key": "value"}\n```'
        result = _remove_markdown_blocks(text)
        assert result == '{"key": "value"}'

    def test_handles_no_code_block(self):
        """Should handle text without code blocks."""
        text = '{"key": "value"}'
        result = _remove_markdown_blocks(text)
        assert result == '{"key": "value"}'

    def test_strips_whitespace(self):
        """Should strip leading/trailing whitespace."""
        text = '  \n{"key": "value"}\n  '
        result = _remove_markdown_blocks(text)
        assert result == '{"key": "value"}'


class TestNormalizeToList:
    """Tests for _normalize_to_list helper."""

    def test_list_returns_as_is(self):
        """Should return list unchanged."""
        data = [{"text": "Hello"}]
        result = _normalize_to_list(data)
        assert result == data

    def test_dict_with_data_key(self):
        """Should extract list from 'data' key."""
        data = {"data": [{"text": "Hello"}]}
        result = _normalize_to_list(data)
        assert result == [{"text": "Hello"}]

    def test_dict_wraps_as_single_item(self):
        """Should wrap single dict in list."""
        data = {"text": "Hello", "lang": "en"}
        result = _normalize_to_list(data)
        assert result == [data]

    def test_raises_for_unexpected_type(self):
        """Should raise ValueError for unexpected types."""
        with pytest.raises(ValueError):
            _normalize_to_list("not a list or dict")


class TestCreateSegments:
    """Tests for _create_segments helper."""

    def test_creates_segments_from_dicts(self):
        """Should create TextSegment instances from dicts."""
        data = [{"text": "Hello", "lang": "en"}]
        segments = _create_segments(data)

        assert len(segments) == 1
        assert isinstance(segments[0], TextSegment)
        assert segments[0].text == "Hello"

    def test_skips_non_dict_entries(self):
        """Should skip non-dict entries."""
        data = [{"text": "Hello", "lang": "en"}, "not a dict", 123]
        segments = _create_segments(data)

        assert len(segments) == 1

    def test_skips_empty_text(self):
        """Should skip entries with empty text."""
        data = [{"text": "", "lang": "en"}, {"text": "Hello", "lang": "en"}]
        segments = _create_segments(data)

        assert len(segments) == 1
        assert segments[0].text == "Hello"

    def test_assigns_order_sequentially(self):
        """Should assign order based on position in list."""
        data = [{"text": "A", "lang": "en"}, {"text": "B", "lang": "en"}]
        segments = _create_segments(data)

        assert segments[0].order == 0
        assert segments[1].order == 1
