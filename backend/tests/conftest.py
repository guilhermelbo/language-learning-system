"""
Pytest fixtures and configuration for backend tests.

This module provides shared fixtures for mocking external services (STT, LLM, TTS)
and setting up test environment.
"""

import pytest
import httpx
from httpx import AsyncClient, Response
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'tests', 'fixtures'))

from mock_services import MockSTTService, MockLLMService, MockTTSService
from test_data import generate_test_audio, generate_synthetic_conversation


@pytest.fixture
def mock_stt_service():
    """Fixture providing mock STT service for testing."""
    return MockSTTService()


@pytest.fixture
def mock_llm_service():
    """Fixture providing mock LLM service for testing."""
    return MockLLMService()


@pytest.fixture
def mock_tts_service():
    """Fixture providing mock TTS service for testing."""
    return MockTTSService()


@pytest.fixture
def mock_services(mock_stt_service, mock_llm_service, mock_tts_service):
    """Fixture providing all mock services for testing."""
    return {
        'stt': mock_stt_service,
        'llm': mock_llm_service,
        'tts': mock_tts_service,
    }


@pytest.fixture
def test_audio_file():
    """Fixture providing synthetic test audio data."""
    return generate_test_audio(language='pt')


@pytest.fixture
def test_conversation():
    """Fixture providing synthetic conversation data for testing."""
    return generate_synthetic_conversation()


@pytest.fixture
async def test_client(mock_services):
    """
    Async HTTP client fixture with mocked external services.
    
    This fixture creates an async HTTP client that automatically routes
    requests to mock services instead of real external APIs.
    """
    # Note: In a real implementation, you would need to configure the client
    # to intercept requests and route them to the mock services.
    # This is a placeholder for demonstration.
    pass
