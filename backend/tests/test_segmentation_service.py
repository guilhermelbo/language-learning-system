import pytest
import sys
import os
import nltk

# Ensure NLTK data is available
nltk.download('punkt')
nltk.download('punkt_tab')

# Add the 'src' directory to the Python path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.domain.services.segmentation_service import segment_text, Segment

def test_segment_simple_bilingual():
    """Tests segmentation of a simple sentence with two languages."""
    text = "Hello, how are you? Olá, como vai você?"
    expected: list[Segment] = [
        {"text": "Hello, how are you?", "lang": "en"},
        {"text": "Olá, como vai você?", "lang": "pt"},
    ]
    result = segment_text(text)
    assert result == expected

def test_segment_multiple_switches():
    """Tests text with back-and-forth language switches."""
    text = "This is in English. Isto está em português. And back to English."
    expected: list[Segment] = [
        {"text": "This is in English.", "lang": "en"},
        {"text": "Isto está em português.", "lang": "pt"},
        {"text": "And back to English.", "lang": "en"},
    ]
    result = segment_text(text)
    assert result == expected

def test_segment_monolingual_english():
    """Tests a purely English sentence."""
    text = "This is a test sentence. It should not be split."
    expected: list[Segment] = [
        {"text": "This is a test sentence. It should not be split.", "lang": "en"}
    ]
    result = segment_text(text)
    assert result == expected

def test_segment_monolingual_portuguese():
    """Tests a purely Portuguese sentence."""
    text = "Esta é uma frase de teste. Não deve ser dividida."
    expected: list[Segment] = [
        {"text": "Esta é uma frase de teste. Não deve ser dividida.", "lang": "pt"}
    ]
    result = segment_text(text)
    assert result == expected

def test_segment_empty_string():
    """Tests behavior with an empty input string."""
    text = ""
    expected: list[Segment] = []
    result = segment_text(text)
    assert result == expected

def test_segment_whitespace_string():
    """Tests behavior with a string containing only whitespace."""
    text = "   \t\n   "
    expected: list[Segment] = []
    result = segment_text(text)
    assert result == expected

def test_segment_with_mocked_ambiguous_sentence(monkeypatch):
    """
    Tests that sentences are correctly segmented based on mock language detection,
    reflecting the actual behavior of nltk.sent_tokenize.
    """
    # Mock langdetect.detect to return a predictable sequence of languages
    # This aligns with nltk.sent_tokenize splitting the text into TWO sentences.
    mock_detections = ['en', 'pt']
    def mock_detect(text):
        return mock_detections.pop(0)
    
    monkeypatch.setattr("src.domain.services.segmentation_service.detect", mock_detect)

    text = "This is a test. ok. Esta é uma frase."
    expected: list[Segment] = [
        {"text": "This is a test.", "lang": "en"},
        {"text": "ok. Esta é uma frase.", "lang": "pt"},
    ]
    
    result = segment_text(text)
    assert result == expected

