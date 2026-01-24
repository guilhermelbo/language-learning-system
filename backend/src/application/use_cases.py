from ..domain.interfaces import STTService, LLMService, TTSService
from ..domain.entities import Conversation, Message
from datetime import datetime
import os

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

    async def execute(self, conversation: Conversation, audio_data: bytes) -> dict:
        # 1. STT: Audio -> Text
        user_text = await self.stt.transcribe(audio_data)
        
        # 2. Update History
        user_message = Message(content=user_text, role="user")
        conversation.add_message(user_message)
        
        # 3. LLM: Text -> Text Response
        ai_text = await self.llm.generate_response(conversation.messages)
        
        # 4. Update History
        ai_message = Message(content=ai_text, role="assistant")
        conversation.add_message(ai_message)
        
        # 5. TTS: Text Response -> Audio
        # We might want to save to file or return bytes. For now, bytes.
        ai_audio_bytes = await self.tts.synthesize(ai_text)
        
        return {
            "user_text": user_text,
            "ai_text": ai_text,
            "ai_audio": ai_audio_bytes,
            "conversation_id": str(conversation.id)
        }
