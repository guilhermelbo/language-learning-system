"""
Application use cases for processing user input.

Use cases orchestrate the flow between domain entities and infrastructure services.
"""
import uuid
from ..domain.interfaces import STTService, LLMService, TTSService
from ..domain.entities import Conversation, Message
from datetime import datetime
import os
import logging

class ProcessUserSpeechUseCase:
    """
    Process user speech input through STT, LLM, and TTS pipeline.

    Flow: Audio -> STT -> LLM -> Segment -> TTS -> Response with Audio URLs
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

        # 4. Segment the raw LLM output into language-specific parts
        from ..domain.services.segmentation_service import segment_text
        from ..domain.response_entities import TextSegment, AssistantResponse
        from .response_transformer import transform_to_api_response

        segmented_results = segment_text(raw_response)
        self.logger.info(f"Step 2b: Segmented into {len(segmented_results)} parts")

        # 5. Convert segments to domain entities
        text_segments = tuple(
            TextSegment(text=seg["text"], language=seg["lang"], order=i)
            for i, seg in enumerate(segmented_results)
        )
        if not text_segments: # Fallback if segmentation returns nothing
            text_segments = (TextSegment(text=raw_response, language="pt", order=0),)
            
        assistant_response = AssistantResponse(segments=text_segments, raw_content=raw_response)

        # 6. Transform to API format
        transformed = transform_to_api_response(assistant_response)
        ai_text = transformed["ai_text"]
        segments = transformed["segments"]

        # 7. Update History (AI) - Store plain text for history
        ai_message = Message(content=ai_text, role="assistant")
        conversation.add_message(ai_message)

        # 8. TTS: Synthesize segments to files
        self.logger.info(f"Step 3: Starting Segmented TTS to files")
        audio_urls = []
        output_dir = "static/audio"
        os.makedirs(output_dir, exist_ok=True)

        for segment in assistant_response.segments:
            if not segment.text.strip():
                continue
            
            filename = f"{uuid.uuid4()}.wav"
            output_path = os.path.join(output_dir, filename)
            
            await self.tts.synthesize_to_file(segment.text, lang=segment.language, output_path=output_path)
            
            # Create a URL for the client
            audio_urls.append(f"/audio/{filename}")

        self.logger.info(f"Step 3: TTS complete. Generated {len(audio_urls)} audio files.")

        return {
            "user_text": user_text,
            "ai_text": ai_text,
            "segments": segments,
            "audio_urls": audio_urls,
            "conversation_id": str(conversation.id)
        }


class ProcessUserTextUseCase:
    """
    Process user text input through LLM and TTS pipeline.

    Flow: Text -> LLM -> Segment -> TTS -> Response with Audio URLs
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
        """
        # 1. Update History (User)
        user_message = Message(content=text, role="user")
        conversation.add_message(user_message)

        # 1.5. TTS: User Text -> Audio (optional, kept as bytes for simplicity)
        self.logger.info(f"Step 0 (Text): Synthesizing audio for user text")
        user_audio_bytes = await self.tts.synthesize(text, lang="pt")

        # 2. LLM: Text -> Raw Response
        self.logger.info(f"Step 1 (Text): Sending to LLM.")
        raw_response = await self.llm.generate_response(conversation.messages)
        self.logger.info(f"Step 1 (Text): LLM Raw Result: '{raw_response}'")

        # 3. Segment the raw LLM output into language-specific parts
        from ..domain.services.segmentation_service import segment_text
        from ..domain.response_entities import TextSegment, AssistantResponse
        from .response_transformer import transform_to_api_response

        segmented_results = segment_text(raw_response)
        self.logger.info(f"Step 1b (Text): Segmented into {len(segmented_results)} parts")

        # 4. Convert segments to domain entities
        text_segments = tuple(
            TextSegment(text=seg["text"], language=seg["lang"], order=i)
            for i, seg in enumerate(segmented_results)
        )
        if not text_segments: # Fallback if segmentation returns nothing
            text_segments = (TextSegment(text=raw_response, language="pt", order=0),)

        assistant_response = AssistantResponse(segments=text_segments, raw_content=raw_response)

        # 5. Transform to API format
        transformed = transform_to_api_response(assistant_response)
        ai_text = transformed["ai_text"]
        segments = transformed["segments"]

        # 6. Update History (AI)
        ai_message = Message(content=ai_text, role="assistant")
        conversation.add_message(ai_message)

        # 7. TTS: Synthesize segments to files
        self.logger.info(f"Step 2 (Text): Starting Segmented TTS to files")
        audio_urls = []
        output_dir = "static/audio"
        os.makedirs(output_dir, exist_ok=True)
        
        for segment in assistant_response.segments:
            if not segment.text.strip():
                continue

            filename = f"{uuid.uuid4()}.wav"
            output_path = os.path.join(output_dir, filename)

            await self.tts.synthesize_to_file(segment.text, lang=segment.language, output_path=output_path)
            
            # Create a URL for the client
            audio_urls.append(f"/audio/{filename}")

        self.logger.info(f"Step 2 (Text): TTS complete. Generated {len(audio_urls)} audio files.")

        return {
            "user_text": text,
            "user_audio": user_audio_bytes,
            "ai_text": ai_text,
            "segments": segments,
            "audio_urls": audio_urls,
            "conversation_id": str(conversation.id)
        }
