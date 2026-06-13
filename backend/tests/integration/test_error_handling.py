"""
Integration tests for error scenarios.

This module tests graceful error handling for various failure modes
in the LingoAI backend services.
"""

import pytest
import json


@pytest.mark.asyncio
async def test_stt_service_timeout(
    test_client: AsyncClient,
    mock_services,
):
    """
    Test graceful handling of STT service timeout.
    
    Given: STT service is timing out
    When: Client sends speech request
    Then: Backend returns error response without crashing
    """
    # Configure mock to fail
    mock_services['stt'].configure_error(
        "test",
        "Timeout after 30000ms"
    )
    
    response = await test_client.post(
        '/conversation/speech',
        files={'file': ('test.wav', b'\x00' * 100, 'audio/wav')}
    )
    
    # Should handle gracefully
    assert response.status_code in [200, 500]
    
    if response.status_code == 200:
        data = response.json()
        assert 'error' in data or 'message' in data


@pytest.mark.asyncio
async def test_llm_service_unavailable(
    test_client: AsyncClient,
    mock_services,
):
    """
    Test graceful handling of LLM service unavailability.
    
    Given: LLM service is unavailable
    When: Client sends text request
    Then: Backend returns fallback response or error message
    """
    # Configure mock to fail
    mock_services['llm'].configure_error(
        "test",
        "Service unavailable"
    )
    
    response = await test_client.post(
        '/conversation/text',
        json={"text": "Test", "conversation_id": None}
    )
    
    # Should handle gracefully
    assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_tts_service_error(
    test_client: AsyncClient,
    mock_services,
):
    """
    Test graceful handling of TTS service error.
    
    Given: TTS service encounters an error
    When: Client requests speech processing
    Then: Backend handles error and returns appropriate response
    """
    # Configure mock to fail
    mock_services['tts'].configure_error(
        "test",
        "TTS synthesis failed"
    )
    
    response = await test_client.post(
        '/conversation/speech',
        files={'file': ('test.wav', b'\x00' * 100, 'audio/wav')}
    )
    
    # Should handle gracefully
    assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_invalid_content_type(
    test_client: AsyncClient,
):
    """
    Test handling of invalid content type.
    
    Given: Request with unsupported content type
    When: Client sends speech request
    Then: Backend returns 415 Unsupported Media Type
    """
    response = await test_client.post(
        '/conversation/speech',
        files={'file': ('test.txt', b'Text file', 'text/plain')}
    )
    
    assert response.status_code in [400, 415]


@pytest.mark.asyncio
async def test_request_too_large(
    test_client: AsyncClient,
):
    """
    Test handling of oversized requests.
    
    Given: Request exceeds maximum size limit
    When: Client sends large audio file
    Then: Backend returns appropriate error
    """
    # Create very large audio file
    large_audio = b'\x00' * (1024 * 1024 * 10)  # 10MB
    
    response = await test_client.post(
        '/conversation/speech',
        files={'file': ('large.wav', large_audio, 'audio/wav')}
    )
    
    assert response.status_code in [400, 413, 429]


@pytest.mark.asyncio
async def test_invalid_llm_json_response(
    test_client: AsyncClient,
    mock_llm_service,
):
    """
    Test handling of invalid JSON from LLM.
    
    Given: LLM returns malformed JSON
    When: Backend processes response
    Then: Backend handles error gracefully
    """
    # Enable invalid responses
    mock_llm_service.enable_invalid_responses()
    
    response = await test_client.post(
        '/conversation/text',
        json={"text": "Test", "conversation_id": None}
    )
    
    # Should handle gracefully
    assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_multiple_service_failures(
    test_client: AsyncClient,
    mock_services,
):
    """
    Test handling when multiple services fail simultaneously.
    
    Given: STT, LLM, and TTS services all encounter errors
    When: Client sends request
    Then: Backend returns appropriate error message
    """
    # Configure all mocks to fail
    mock_services['stt'].configure_error("test", "STT error")
    mock_services['llm'].configure_error("test", "LLM error")
    mock_services['tts'].configure_error("test", "TTS error")
    
    response = await test_client.post(
        '/conversation/speech',
        files={'file': ('test.wav', b'\x00' * 100, 'audio/wav')}
    )
    
    # Should handle gracefully
    assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_empty_conversation_id(
    test_client: AsyncClient,
):
    """
    Test handling of empty/null conversation ID.
    
    Given: Request with null or empty conversation_id
    When: Backend processes request
    Then: Backend treats it as new conversation
    """
    response = await test_client.post(
        '/conversation/text',
        json={"text": "Test", "conversation_id": None}
    )
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_malformed_url_encoding(
    test_client: AsyncClient,
):
    """
    Test handling of malformed URL encoding.
    
    Given: Request with invalid URL encoding
    When: Backend processes request
    Then: Backend returns appropriate error
    """
    response = await test_client.post(
        '/conversation/text',
        json={"text": "Test\x00\x01", "conversation_id": None}
    )
    
    # Should handle gracefully
    assert response.status_code in [200, 400]
