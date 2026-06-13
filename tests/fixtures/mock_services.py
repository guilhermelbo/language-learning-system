"""
Mock services for testing external AI services (STT, LLM, TTS).

These mocks allow tests to run without actual external API calls,
providing predictable responses and enabling error scenario testing.
"""

import struct
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class MockSTTResponse:
    """Mock response from STT service."""
    transcription: str
    confidence: float = 0.95
    duration: float = 0.0


@dataclass
class MockLLMResponse:
    """Mock response from LLM service."""
    segments: List[Dict[str, str]]
    processing_time: float = 0.5


@dataclass
class MockTTSResponse:
    """Mock response from TTS service."""
    audio_data: bytes
    duration: float = 1.0
    format: str = "wav"


class MockSTTService:
    """
    Mock STT (Speech-to-Text) service for testing.
    
    Returns pre-defined transcriptions without actual audio processing.
    Supports configurable responses and error simulation.
    """
    
    def __init__(self):
        self.transcriptions: Dict[str, str] = {
            "test_audio_1": "Olá, como você está?",
            "test_audio_2": "I want to learn English",
            "default": "Test transcription",
        }
        self.delays: Dict[str, float] = {}
        self.errors: Dict[str, str] = {}
    
    async def transcribe(self, audio_data: bytes) -> str:
        """
        Simulate STT transcription.
        
        Args:
            audio_data: Mock audio data (bytes)
            
        Returns:
            Transcription string
            
        Raises:
            RuntimeError: If error is configured for this audio
        """
        # Check for configured error
        audio_key = audio_data[:20].hex()
        if audio_key in self.errors:
            raise RuntimeError(self.errors[audio_key])
        
        # Return mock transcription
        if audio_key in self.transcriptions:
            return self.transcriptions[audio_key]
        return self.transcriptions["default"]
    
    def configure_delay(self, audio_key: str, delay_ms: int):
        """Configure delay for specific audio."""
        self.delays[audio_key] = delay_ms / 1000.0
    
    def configure_error(self, audio_key: str, error_message: str):
        """Configure error for specific audio."""
        self.errors[audio_key] = error_message


class MockLLMService:
    """
    Mock LLM (Large Language Model) service for testing.
    
    Returns pre-defined bilingual conversation segments.
    Supports error simulation and response delays.
    """
    
    def __init__(self):
        self.responses: Dict[str, List[Dict[str, str]]] = {
            "greeting": [
                {"text": "Olá! Como posso ajudar?", "lang": "pt"},
                {"text": "Hello! How can I help you?", "lang": "en"},
            ],
            "introduction": [
                {"text": "Me chamo LingoAI. Sou um tutor de idiomas.", "lang": "pt"},
                {"text": "My name is LingoAI. I am a language tutor.", "lang": "en"},
            ],
            "default": [
                {"text": "Entendido! Posso ajudar com o que?", "lang": "pt"},
                {"text": "Understood! How can I help?", "lang": "en"},
            ],
        }
        self.delays: Dict[str, float] = {}
        self.errors: Dict[str, str] = {}
        self.invalid_responses: bool = False
    
    async def generate_response(self, prompt: str) -> List[Dict[str, str]]:
        """
        Simulate LLM response generation.
        
        Args:
            prompt: User input prompt
            
        Returns:
            List of bilingual segments
            
        Raises:
            RuntimeError: If error is configured
            ValueError: If invalid JSON response is configured
        """
        # Check for configured error
        if self.invalid_responses:
            raise ValueError("Invalid JSON response from LLM")
        
        if prompt in self.errors:
            raise RuntimeError(self.errors[prompt])
        
        # Return mock response
        if prompt in self.responses:
            return self.responses[prompt]
        return self.responses["default"]
    
    def configure_delay(self, prompt_key: str, delay_ms: int):
        """Configure delay for specific prompt."""
        self.delays[prompt_key] = delay_ms / 1000.0
    
    def configure_error(self, prompt_key: str, error_message: str):
        """Configure error for specific prompt."""
        self.errors[prompt_key] = error_message
    
    def enable_invalid_responses(self):
        """Enable invalid response simulation."""
        self.invalid_responses = True


class MockTTSService:
    """
    Mock TTS (Text-to-Speech) service for testing.
    
    Returns synthetic audio data without actual synthesis.
    Supports error simulation and audio format configuration.
    """
    
    def __init__(self, format: str = "wav"):
        self.format = format
        self.responses: Dict[str, bytes] = {}
        self.errors: Dict[str, str] = {}
        self.delays: Dict[str, float] = {}
    
    async def synthesize(self, text: str, language: str = "pt") -> bytes:
        """
        Simulate TTS audio synthesis.
        
        Args:
            text: Text to convert to speech
            language: Language code (default: "pt")
            
        Returns:
            Audio data in WAV format
            
        Raises:
            RuntimeError: If error is configured for this text
        """
        # Check for configured error
        text_key = text[:20]
        if text_key in self.errors:
            raise RuntimeError(self.errors[text_key])
        
        # Return synthetic audio data (placeholder)
        if text_key in self.responses:
            return self.responses[text_key]
        
        # Generate synthetic WAV header and zeros
        audio_data = self._generate_mock_audio(text, language)
        return audio_data
    
    def _generate_mock_audio(self, text: str, language: str) -> bytes:
        """Generate mock audio data for testing."""
        # Simple mock: WAV header + zeros
        header = b'RIFF' + b'\x00\x00\x00\x00' + b'WAVE'
        header += b'fmt ' + struct.pack('<I', 16) + struct.pack('<H', 1)
        header += struct.pack('<HH', 1, 16)
        header += struct.pack('<I', 16000)
        header += struct.pack('<I', 64000)
        header += struct.pack('<H', 2) + struct.pack('<H', 16)
        header += b'data' + struct.pack('<I', len(text) * 2)
        
        return header + (b'\x00' * len(text) * 2)
    
    def configure_delay(self, text_key: str, delay_ms: int):
        """Configure delay for specific text."""
        self.delays[text_key] = delay_ms / 1000.0
    
    def configure_error(self, text_key: str, error_message: str):
        """Configure error for specific text."""
        self.errors[text_key] = error_message
    
    def set_audio_format(self, format: str):
        """Set audio format (wav, mp3, etc.)."""
        self.format = format
