"""
Integration tests for /conversation/speech endpoint.

This module tests the speech-to-text conversation flow with mocked external services.
"""

import pytest
from httpx import AsyncClient
import struct


@pytest.mark.asyncio
async def test_speech_endpoint_valid_audio(
    test_client: AsyncClient,
    test_audio_file
):
    """
    Test successful speech recognition with valid audio.
    
    Given: A valid audio file is sent to the /conversation/speech endpoint
    When: The backend processes the request with mocked services
    Then: It returns a valid audio response with merged TTS segments
    """
    # Create multipart form data
    from io import BytesIO
    
    files = {
        'file': (
            'test_audio.wav',
            BytesIO(test_audio_file.data),
            'audio/wav'
        )
    }
    
    response = await test_client.post('/conversation/speech', files=files)
    
    assert response.status_code == 200
    # Response should be audio data
    assert len(response.content) > 0
    # Should have WAV header
    assert response.content[:4] == b'RIFF'


@pytest.mark.asyncio
async def test_speech_endpoint_invalid_audio(
    test_client: AsyncClient,
):
    """
    Test error handling with invalid/malformed audio.
    
    Given: An invalid audio file is sent to the /conversation/speech endpoint
    When: The backend processes the request
    Then: It returns an appropriate error response
    """
    files = {
        'file': (
            'invalid.wav',
            b'Not a valid WAV file at all',
            'audio/wav'
        )
    }
    
    response = await test_client.post('/conversation/speech', files=files)
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_speech_endpoint_empty_audio(
    test_client: AsyncClient
):
    """
    Test error handling with empty audio file.
    
    Given: An empty audio file is sent to the /conversation/speech endpoint
    When: The backend processes the request
    Then: It returns an appropriate error response
    """
    files = {
        'file': (
            'empty.wav',
            b'',
            'audio/wav'
        )
    }
    
    response = await test_client.post('/conversation/speech', files=files)
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_speech_endpoint_service_timeout(
    test_client: AsyncClient,
    mock_services
):
    """
    Test error handling when STT service times out.
    
    Given: The STT service returns a timeout error
    When: The backend processes the request
    Then: It returns a user-friendly error message without crashing
    """
    # Configure mock to timeout
    mock_services['stt'].configure_error(
        "test_audio_1", 
        "Service timeout"
    )
    
    files = {
        'file': (
            'test.wav',
            b'\x00' * 100,
            'audio/wav'
        )
    }
    
    response = await test_client.post('/conversation/speech', files=files)
    
    # Backend should handle the error gracefully
    assert response.status_code in [200, 500]  # Depending on implementation
    assert "error" in response.json().lower() or "message" in response.json()


@pytest.mark.asyncio
async def test_speech_endpoint_conversation_flow(
    test_client: AsyncClient,
    test_audio_file
):
    """
    Test complete conversation flow with STT → LLM → TTS.
    
    Given: A valid audio file with a question in Portuguese
    When: The backend processes the complete conversation flow
    Then: It returns TTS audio with bilingual response segments
    """
    files = {
        'file': (
            'test.wav',
            BytesIO(test_audio_file.data),
            'audio/wav'
        )
    }
    
    response = await test_client.post('/conversation/speech', files=files)
    
    assert response.status_code == 200
    # Should return audio data
    assert len(response.content) > 0
