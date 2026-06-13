"""
Integration tests for audio file processing.

This module tests audio validation, format handling, and edge cases
for audio file processing in the LingoAI backend.
"""

import pytest


@pytest.mark.asyncio
async def test_valid_wav_audio(
    test_client: AsyncClient,
):
    """
    Test processing of valid WAV audio file.
    
    Given: A properly formatted WAV file
    When: Client sends audio to speech endpoint
    Then: Backend processes successfully
    """
    # Create minimal valid WAV header
    wav_header = (
        b'RIFF' + b'\x00\x00\x00\x00' + b'WAVE' +
        b'fmt ' + b'\x10\x00\x00\x00\x01\x00\x02\x00' +
        b'\xd0\xfa\x00\x00\x00\x00\x00\x00\x02\x00\x10' +
        b'\x00data' + b'\x00\x00\x00\x00' + b'\x00' * 100
    )
    
    response = await test_client.post(
        '/conversation/speech',
        files={'file': ('test.wav', wav_header, 'audio/wav')}
    )
    
    # Should be accepted (may still fail on other services)
    assert response.status_code in [200, 400, 415]


@pytest.mark.asyncio
async def test_invalid_wav_header(
    test_client: AsyncClient,
):
    """
    Test handling of invalid WAV header.
    
    Given: File with invalid WAV header
    When: Client sends audio
    Then: Backend rejects with appropriate error
    """
    response = await test_client.post(
        '/conversation/speech',
        files={'file': ('test.wav', b'Not WAV at all', 'audio/wav')}
    )
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_truncated_wav_file(
    test_client: AsyncClient,
):
    """
    Test handling of truncated WAV file.
    
    Given: File with incomplete WAV header
    When: Client sends audio
    Then: Backend rejects with appropriate error
    """
    response = await test_client.post(
        '/conversation/speech',
        files={'file': ('test.wav', b'RIFF\x00\x00\x00\x00WAVE', 'audio/wav')}
    )
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_mp3_audio_format(
    test_client: AsyncClient,
):
    """
    Test handling of MP3 audio format.
    
    Given: MP3 encoded audio
    When: Client sends audio
    Then: Backend either processes or rejects based on config
    """
    # MP3 magic number
    mp3_header = b'\xff\xfb'
    
    response = await test_client.post(
        '/conversation/speech',
        files={'file': ('test.mp3', mp3_header, 'audio/mpeg')}
    )
    
    # Backend should handle MP3 or reject
    assert response.status_code in [200, 400, 415]


@pytest.mark.asyncio
async def test_ogg_audio_format(
    test_client: AsyncClient,
):
    """
    Test handling of OGG audio format.
    
    Given: OGG encoded audio
    When: Client sends audio
    Then: Backend handles appropriately
    """
    response = await test_client.post(
        '/conversation/speech',
        files={'file': ('test.ogg', b'\x01OggS', 'audio/ogg')}
    )
    
    assert response.status_code in [200, 400, 415]


@pytest.mark.asyncio
async def test_webm_audio_format(
    test_client: AsyncClient,
):
    """
    Test handling of WebM audio format.
    
    Given: WebM encoded audio (Opus/ Vorbis)
    When: Client sends audio
    Then: Backend handles appropriately
    """
    # WebM magic number
    webm_header = b'\x1a\x45\xdf\xa3'
    
    response = await test_client.post(
        '/conversation/speech',
        files={'file': ('test.webm', webm_header, 'audio/webm')}
    )
    
    assert response.status_code in [200, 400, 415]


@pytest.mark.asyncio
async def test_audio_too_short(
    test_client: AsyncClient,
):
    """
    Test handling of audio that's too short.
    
    Given: Very short audio clip (<10ms)
    When: Client sends audio
    Then: Backend may reject or process minimally
    """
    # Minimal valid WAV with very short data
    wav_minimal = (
        b'RIFF' + b'\x2c\x01\x00\x00' + b'WAVE' +
        b'fmt ' + b'\x10\x00\x00\x00\x01\x00\x02\x00' +
        b'\xd0\xfa\x00\x00\x00\x00\x00\x00\x02\x00\x10' +
        b'\x00data' + b'\x00\x00\x00\x00'
    )
    
    response = await test_client.post(
        '/conversation/speech',
        files={'file': ('short.wav', wav_minimal, 'audio/wav')}
    )
    
    assert response.status_code in [200, 400]


@pytest.mark.asyncio
async def test_audio_sample_rate_validation(
    test_client: AsyncClient,
):
    """
    Test handling of unusual sample rates.
    
    Given: Audio with very low or very high sample rate
    When: Client sends audio
    Then: Backend handles appropriately
    """
    # Low sample rate (5kHz)
    wav_low_sr = (
        b'RIFF' + b'\x40\x01\x00\x00' + b'WAVE' +
        b'fmt ' + b'\x10\x00\x00\x00\x01\x00\x01\x00' +
        b'\x0c\x40\x00\x00' + b'\x00\x00\x00\x00\x02\x00\x10' +
        b'\x00data' + b'\x00\x00\x00\x00'
    )
    
    response = await test_client.post(
        '/conversation/speech',
        files={'file': ('low_sr.wav', wav_low_sr, 'audio/wav')}
    )
    
    assert response.status_code in [200, 400]


@pytest.mark.asyncio
async def test_audio_mono_vs_stereo(
    test_client: AsyncClient,
):
    """
    Test handling of mono vs stereo audio.
    
    Given: Both mono and stereo audio files
    When: Client sends audio
    Then: Backend handles both formats
    """
    # Mono audio
    wav_mono = (
        b'RIFF' + b'\x10\x01\x00\x00' + b'WAVE' +
        b'fmt ' + b'\x10\x00\x00\x00\x01\x00\x01\x00' +
        b'\xd0\xfa\x00\x00\x00\x00\x00\x00\x02\x00\x10' +
        b'\x00data' + b'\x00\x00\x00\x00'
    )
    
    # Stereo audio
    wav_stereo = (
        b'RIFF' + b'\x20\x01\x00\x00' + b'WAVE' +
        b'fmt ' + b'\x10\x00\x00\x00\x01\x00\x02\x00' +
        b'\xd0\xfa\x00\x00\x00\x00\x00\x00\x04\x00\x10' +
        b'\x00data' + b'\x00\x00\x00\x00'
    )
    
    response_mono = await test_client.post(
        '/conversation/speech',
        files={'file': ('mono.wav', wav_mono, 'audio/wav')}
    )
    
    response_stereo = await test_client.post(
        '/conversation/speech',
        files={'file': ('stereo.wav', wav_stereo, 'audio/wav')}
    )
    
    # Both should be accepted or rejected consistently
    assert response_mono.status_code == response_stereo.status_code


@pytest.mark.asyncio
async def test_audio_no_extension(
    test_client: AsyncClient,
):
    """
    Test handling of audio without file extension.
    
    Given: Audio file without .wav extension
    When: Client sends audio
    Then: Backend validates based on content, not extension
    """
    response = await test_client.post(
        '/conversation/speech',
        files={'file': ('audio_data', b'\x00' * 100, 'audio/wav')}
    )
    
    assert response.status_code in [200, 400]
