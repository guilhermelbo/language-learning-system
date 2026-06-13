"""
Audio utilities for test generation and validation.

This module provides utilities for working with test audio files,
including format validation and conversion.
"""

import struct
import wave
from typing import Tuple, Optional


def validate_wav_header(audio_data: bytes) -> Tuple[bool, str]:
    """
    Validate WAV file header.
    
    Args:
        audio_data: Raw audio bytes
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(audio_data) < 44:
        return False, "File too short to be a valid WAV file"
    
    # Check RIFF header
    if audio_data[:4] != b'RIFF':
        return False, "Invalid RIFF header"
    
    # Check WAVE header
    if audio_data[8:12] != b'WAVE':
        return False, "Invalid WAVE header"
    
    # Check fmt chunk
    if audio_data[12:16] != b'fmt ':
        return False, "Missing fmt chunk"
    
    return True, ""


def validate_audio_format(audio_data: bytes, expected_format: str) -> bool:
    """
    Validate audio format matches expected format.
    
    Args:
        audio_data: Raw audio bytes
        expected_format: Expected format (wav, mp3, etc.)
        
    Returns:
        True if format matches, False otherwise
    """
    if expected_format == "wav":
        is_valid, _ = validate_wav_header(audio_data)
        return is_valid
    
    # Add more format validations as needed
    return False


def calculate_audio_duration(audio_data: bytes, sample_rate: int = 16000) -> float:
    """
    Calculate audio duration in seconds.
    
    Args:
        audio_data: Raw audio bytes
        sample_rate: Audio sample rate in Hz
        
    Returns:
        Duration in seconds
    """
    # Simple calculation: bytes / (channels * bits_per_sample / 8)
    # Assuming mono, 16-bit PCM
    bytes_per_sample = 2  # 16-bit
    num_channels = 1  # Mono
    
    num_samples = len(audio_data) / (num_channels * bytes_per_sample)
    duration = num_samples / sample_rate
    
    return duration


def generate_silence(duration_seconds: float, sample_rate: int = 16000) -> bytes:
    """
    Generate silence audio data.
    
    Args:
        duration_seconds: Duration in seconds
        sample_rate: Sample rate in Hz
        
    Returns:
        Silence audio data (zeros)
    """
    num_samples = int(duration_seconds * sample_rate)
    return b'\x00' * num_samples * 2  # 16-bit


def generate_tone(freq: int, duration_seconds: float, sample_rate: int = 16000) -> bytes:
    """
    Generate a pure tone audio signal.
    
    Args:
        freq: Frequency in Hz
        duration_seconds: Duration in seconds
        sample_rate: Sample rate in Hz
        
    Returns:
        Tone audio data
    """
    import math
    
    num_samples = int(duration_seconds * sample_rate)
    tone_data = bytearray(num_samples * 2)
    
    for i in range(num_samples):
        # Generate sine wave (16-bit PCM)
        value = int(32767 * math.sin(2 * math.pi * freq * i / sample_rate))
        # Pack as little-endian 16-bit
        tone_data[i * 2:i * 2 + 2] = struct.pack('<h', value)
    
    return bytes(tone_data)


def merge_audio_segments(segments: list) -> bytes:
    """
    Merge multiple audio segments into one.
    
    Args:
        segments: List of audio byte data
        
    Returns:
        Merged audio data
    """
    if not segments:
        return b''
    
    return b''.join(segments)


def trim_audio(audio_data: bytes, start_ms: int = 0, end_ms: int = -1) -> bytes:
    """
    Trim audio data to specific time range.
    
    Args:
        audio_data: Raw audio bytes
        start_ms: Start offset in milliseconds
        end_ms: End offset in milliseconds (-1 for end of audio)
        
    Returns:
        Trimmed audio data
    """
    sample_rate = 16000  # Assuming 16kHz
    bytes_per_sample = 2  # 16-bit
    
    start_byte = start_ms * sample_rate * bytes_per_sample // 1000
    
    if end_ms == -1:
        return audio_data[start_byte:]
    
    end_byte = end_ms * sample_rate * bytes_per_sample // 1000
    return audio_data[start_byte:end_byte]
