"""
Application use cases for processing user input.

Use cases orchestrate the flow between domain entities and infrastructure services.
"""

from ..domain.interfaces import STTService, LLMService, TTSService
from ..domain.entities import Conversation, Message
from .response_extractor import extract_response
from .response_transformer import transform_to_api_response
from datetime import datetime
import os
import logging
import struct


def _merge_wavs(wav_bytes_list: list[bytes]) -> bytes:
    """
    Merge multiple WAV audio segments into a single WAV file.

    Args:
        wav_bytes_list: List of WAV file bytes

    Returns:
        Merged WAV file bytes
    """
    if not wav_bytes_list:
        return b""

    if len(wav_bytes_list) == 1:
        return wav_bytes_list[0]

    header = wav_bytes_list[0][:44]
    data = wav_bytes_list[0][44:]

    for wav in wav_bytes_list[1:]:
        if len(wav) > 44:
            data += wav[44:]

    total_size = len(header) + len(data)

    # RIFF chunk size (Total file size - 8)
    new_riff_size = struct.pack('<I', total_size - 8)

    # Data subchunk size
    new_data_size = struct.pack('<I', len(data))

    new_header = header[:4] + new_riff_size + header[8:40] + new_data_size

    return new_header + data


class ProcessUserSpeechUseCase:
    """
    Process user speech input through STT, LLM, and TTS pipeline.

    Flow: Audio -> STT -> LLM -> Extract -> Transform -> TTS -> Response
    """

    def __init__(
        self,
        stt_service: STTService,
        llm_service: LLMService,
        tts_service: TTSService
    ):
        self.stt = stt_service
        self.llm = llm_service
        self.tts = tts_service
        self.logger = logging.getLogger(__name__)

    async def execute(self, conversation: Conversation, audio_data: bytes) -> dict:
        """
        Execute the speech processing pipeline.

        Args:
            conversation: Current conversation context
            audio_data: Raw audio bytes from user

        Returns:
            Dictionary with user_text, ai_text, segments, ai_audio, conversation_id
        """
        # 0. Save Input Audio for Debugging
        input_dir = "input_audio"
        os.makedirs(input_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"input_{timestamp}.webm"
        file_path = os.path.join(input_dir, filename)

        try:
            with open(file_path, "wb") as f:
                f.write(audio_data)
            self.logger.info(f"Saved input audio to {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to save input audio: {e}")

        # 1. STT: Audio -> Text
        self.logger.info(f"Step 1: Starting STT with {len(audio_data)} bytes of audio")
        user_text = await self.stt.transcribe(audio_data)
        self.logger.info(f"Step 1: STT Result: '{user_text}'")

        # 2. Update History (User)
        user_message = Message(content=user_text, role="user")
        conversation.add_message(user_message)

        # 3. LLM: Text -> Raw Response
        self.logger.info(f"Step 2: Sending to LLM. History size: {len(conversation.messages)}")
        raw_response = await self.llm.generate_response(conversation.messages)
        self.logger.info(f"Step 2: LLM Raw Result: '{raw_response}'")

        # 4. Extract structured response from raw LLM output
        assistant_response = extract_response(raw_response)
        self.logger.info(f"Step 2b: Extracted {len(assistant_response.segments)} segments")

        # 5. Transform to API format
        transformed = transform_to_api_response(assistant_response)
        ai_text = transformed["ai_text"]
        segments = transformed["segments"]

        # 6. Update History (AI) - Store plain text for history
        ai_message = Message(content=ai_text, role="assistant")
        conversation.add_message(ai_message)

        # 7. TTS: Segmented Synthesis using domain segments
        self.logger.info(f"Step 3: Starting Segmented TTS")
        audio_segments = []
        for segment in assistant_response.segments:
            if not segment.text.strip():
                continue

            emb_audio = await self.tts.synthesize(segment.text, lang=segment.language)
            if emb_audio:
                audio_segments.append(emb_audio)

        ai_audio_bytes = _merge_wavs(audio_segments)
        self.logger.info(f"Step 3: TTS complete. Merged Audio size: {len(ai_audio_bytes)} bytes")

        return {
            "user_text": user_text,
            "ai_text": ai_text,
            "segments": segments,
            "ai_audio": ai_audio_bytes,
            "conversation_id": str(conversation.id)
        }


class ProcessUserTextUseCase:
    """
    Process user text input through LLM and TTS pipeline.

    Flow: Text -> LLM -> Extract -> Transform -> TTS -> Response
    """

    def __init__(
        self,
        llm_service: LLMService,
        tts_service: TTSService
    ):
        self.llm = llm_service
        self.tts = tts_service
        self.logger = logging.getLogger(__name__)

    async def execute(self, conversation: Conversation, text: str) -> dict:
        """
        Execute the text processing pipeline.

        Args:
            conversation: Current conversation context
            text: User's text input

        Returns:
            Dictionary with user_text, ai_text, segments, user_audio, ai_audio, conversation_id
        """
        # 1. Update History (User)
        user_message = Message(content=text, role="user")
        conversation.add_message(user_message)

        # 1.5. TTS: User Text -> Audio
        self.logger.info(f"Step 0 (Text): Synthesizing audio for user text")
        user_audio_bytes = await self.tts.synthesize(text, lang="pt")

        # 2. LLM: Text -> Raw Response
        self.logger.info(f"Step 1 (Text): Sending to LLM.")
        raw_response = await self.llm.generate_response(conversation.messages)
        self.logger.info(f"Step 1 (Text): LLM Raw Result: '{raw_response}'")

        # 3. Extract structured response from raw LLM output
        assistant_response = extract_response(raw_response)
        self.logger.info(f"Step 1b (Text): Extracted {len(assistant_response.segments)} segments")

        # 4. Transform to API format
        transformed = transform_to_api_response(assistant_response)
        ai_text = transformed["ai_text"]
        segments = transformed["segments"]

        # 5. Update History (AI)
        ai_message = Message(content=ai_text, role="assistant")
        conversation.add_message(ai_message)

        # 6. TTS: Segmented Synthesis using domain segments
        self.logger.info(f"Step 2 (Text): Starting Segmented TTS")
        audio_segments = []
        for segment in assistant_response.segments:
            if not segment.text.strip():
                continue

            emb_audio = await self.tts.synthesize(segment.text, lang=segment.language)
            if emb_audio:
                audio_segments.append(emb_audio)

        ai_audio_bytes = _merge_wavs(audio_segments)
        self.logger.info(f"Step 2 (Text): TTS complete. Merged Audio size: {len(ai_audio_bytes)} bytes")

        return {
            "user_text": text,
            "user_audio": user_audio_bytes,
            "ai_text": ai_text,
            "segments": segments,
            "ai_audio": ai_audio_bytes,
            "conversation_id": str(conversation.id)
        }
