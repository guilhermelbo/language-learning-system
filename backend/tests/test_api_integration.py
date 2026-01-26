import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
import os

# Add src to path to allow absolute imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the app and the dependency providers
from src.main import app, get_llm_service, get_tts_service

# --- Mock Services ---

def mock_llm_service_override():
    """Creates a mock LLM service that returns a predictable bilingual string."""
    mock = AsyncMock()
    mock.generate_response.return_value = "This is a test. Isto é um teste."
    return mock

def mock_tts_service_override():
    """Creates a mock TTS service that simulates file creation."""
    async def mock_synthesize_to_file(text, lang, output_path):
        return output_path
    
    mock = AsyncMock()
    mock.synthesize_to_file.side_effect = mock_synthesize_to_file
    mock.synthesize.return_value = b"dummy_user_audio_bytes"
    return mock

# --- Override Dependencies ---
app.dependency_overrides[get_llm_service] = mock_llm_service_override
app.dependency_overrides[get_tts_service] = mock_tts_service_override

# --- Test Client ---
client = TestClient(app)

# --- Test Case ---

def test_conversation_text_endpoint_integration():
    """
    Tests the /conversation/text endpoint with mocked dependencies.
    It checks if the request is processed correctly and if the response
    has the expected structure with segmented audio URLs.
    """
    # Arrange
    input_data = {"text": "Test with a bilingual sentence"}

    # Act
    response = client.post("/conversation/text", json=input_data)

    # Assert
    assert response.status_code == 200
    
    data = response.json()
    
    # Check for presence and type of key fields
    assert "segments" in data
    assert isinstance(data["segments"], list)
    assert "audio_urls" in data
    assert isinstance(data["audio_urls"], list)
    assert "ai_text" in data
    
    # Check the content of the fields
    assert data["ai_text"] == "This is a test. Isto é um teste."
    
    segments = data["segments"]
    urls = data["audio_urls"]
    
    assert len(segments) == 2
    assert len(urls) == 2
    
    # Check segment content
    assert segments[0]["text"] == "This is a test."
    assert segments[0]["lang"] == "en"
    assert segments[1]["text"] == "Isto é um teste."
    assert segments[1]["lang"] == "pt"
    
    # Check that the URLs look correct
    assert urls[0].startswith("/audio/")
    assert urls[0].endswith(".wav")
    assert urls[1].startswith("/audio/")
    assert urls[1].endswith(".wav")
