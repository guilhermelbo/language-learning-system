from ..domain.interfaces import STTService, LLMService, TTSService
from ..domain.entities import Conversation, Message
from datetime import datetime
import os
import logging

class ProcessUserSpeechUseCase:
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
        
        # 2. Update History
        user_message = Message(content=user_text, role="user")
        conversation.add_message(user_message)
        
        # 3. LLM: Text -> Text Response
        self.logger.info(f"Step 2: Sending to LLM. History size: {len(conversation.messages)}")
        ai_text = await self.llm.generate_response(conversation.messages)
        self.logger.info(f"Step 2: LLM Result: '{ai_text}'")
        
        # 4. Update History
        ai_message = Message(content=ai_text, role="assistant")
        conversation.add_message(ai_message)
        
        # 5. TTS: Text Response -> Audio
        # We might want to save to file or return bytes. For now, bytes.
        self.logger.info(f"Step 3: Starting TTS for text: '{ai_text[:50]}...'")
        ai_audio_bytes = await self.tts.synthesize(ai_text)
        self.logger.info(f"Step 3: TTS complete. Audio size: {len(ai_audio_bytes)} bytes")
        
        return {
            "user_text": user_text,
            "ai_text": ai_text,
            "ai_audio": ai_audio_bytes,
            "conversation_id": str(conversation.id)
        }
