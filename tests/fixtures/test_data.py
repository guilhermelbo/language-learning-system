"""
Synthetic test data generation utilities.

These utilities create realistic but fake test data for the language learning
system, avoiding any real user information.
"""

import struct
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class TestAudio:
    """Test audio file representation."""
    audio_id: str
    language: str
    duration_seconds: float
    sample_rate_hz: int
    format: str
    content_type: str
    data: bytes


@dataclass
class ConversationTurn:
    """Test conversation turn."""
    turn_id: str
    user_input: str
    user_input_type: str  # "text" or "audio"
    user_language: str
    stt_transcription: str
    llm_response: List[Dict[str, str]]
    tts_audio_path: str
    status: str


def generate_test_audio(
    language: str = "pt",
    duration_seconds: float = 3.0,
    sample_rate_hz: int = 16000,
    format: str = "wav"
) -> TestAudio:
    """
    Generate synthetic test audio data.
    
    Args:
        language: Language code (pt, en)
        duration_seconds: Duration of audio in seconds
        sample_rate_hz: Audio sample rate (Hz)
        format: Audio format (wav, mp3)
        
    Returns:
        TestAudio object with synthetic data
    """
    # Generate WAV file header
    num_channels = 1  # Mono
    bits_per_sample = 16
    byte_rate = sample_rate_hz * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = int(duration_seconds * sample_rate_hz * block_align)
    
    # WAV header
    header = (
        b'RIFF' +
        struct.pack('<I', 36 + data_size) +  # File size - 8
        b'WAVE' +
        b'fmt ' +
        struct.pack('<I', 16) +              # fmt chunk size
        struct.pack('<H', 1) +               # Audio format (1 = PCM)
        struct.pack('<H', num_channels) +    # Channels
        struct.pack('<I', sample_rate_hz) +  # Sample rate
        struct.pack('<I', byte_rate) +       # Byte rate
        struct.pack('<H', block_align) +     # Block align
        struct.pack('<H', bits_per_sample) + # Bits per sample
        b'data' +
        struct.pack('<I', data_size)         # Data chunk size
    )
    
    # Generate synthetic audio data (silence - zeros)
    audio_data = header + (b'\x00' * data_size)
    
    return TestAudio(
        audio_id=f"audio-{language}-{duration_seconds}s",
        language=language,
        duration_seconds=duration_seconds,
        sample_rate_hz=sample_rate_hz,
        format=format,
        content_type=f"audio/{format}",
        data=audio_data
    )


def generate_synthetic_conversation() -> List[ConversationTurn]:
    """
    Generate synthetic conversation data for testing.
    
    Returns:
        List of ConversationTurn objects with realistic but fake dialogue
    """
    return [
        ConversationTurn(
            turn_id="turn-001",
            user_input="Olá, como você está?",
            user_input_type="text",
            user_language="pt",
            stt_transcription="Olá, como você está?",
            llm_response=[
                {"text": "Olá! Eu estou bem, obrigado! E você?", "lang": "pt"},
                {"text": "Hello! I'm doing well, thank you! And you?", "lang": "en"},
            ],
            tts_audio_path="/tmp/mock_audio_001.wav",
            status="completed"
        ),
        ConversationTurn(
            turn_id="turn-002",
            user_input="I want to learn English",
            user_input_type="text",
            user_language="en",
            stt_transcription="I want to learn English",
            llm_response=[
                {"text": "Excelente! Posso ajudar você a aprender inglês.", "lang": "pt"},
                {"text": "Great! I can help you learn English.", "lang": "en"},
            ],
            tts_audio_path="/tmp/mock_audio_002.wav",
            status="completed"
        ),
        ConversationTurn(
            turn_id="turn-003",
            user_input="O que significa 'learning'?",
            user_input_type="text",
            user_language="pt",
            stt_transcription="O que significa learning?",
            llm_response=[
                {"text": "'Learning' significa 'aprender' em inglês.", "lang": "pt"},
                {"text": "'Learning' means 'aprender' in English.", "lang": "en"},
            ],
            tts_audio_path="/tmp/mock_audio_003.wav",
            status="completed"
        ),
    ]


def generate_error_scenario_audio(error_type: str = "malformed") -> bytes:
    """
    Generate test audio for error scenario testing.
    
    Args:
        error_type: Type of error ("malformed", "empty", "invalid_format")
        
    Returns:
        Audio data that will trigger the specified error
    """
    if error_type == "malformed":
        # Invalid WAV header
        return b'RIFF' + b'\x00\x00\x00\x00' + b'INVALID' + b'\x00' * 100
    
    elif error_type == "empty":
        # Empty audio
        return b''
    
    elif error_type == "truncated":
        # Truncated WAV file
        return b'RIFF' + b'\x00\x00\x00\x00' + b'WAVE'
    
    else:
        raise ValueError(f"Unknown error type: {error_type}")


def generate_test_text_input(
    language: str = "pt",
    max_length: int = 100
) -> str:
    """
    Generate synthetic text input for testing.
    
    Args:
        language: Language code (pt, en)
        max_length: Maximum text length
        
    Returns:
        Synthetic text input string
    """
    if language == "pt":
        return f"Esta é uma mensagem de teste em português com {max_length} caracteres."
    else:
        return f"This is a test message in English with {max_length} characters."
