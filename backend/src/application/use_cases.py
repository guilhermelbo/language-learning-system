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
        
        # 3. LLM: Text -> Text Response (JSON now)
        self.logger.info(f"Step 2: Sending to LLM. History size: {len(conversation.messages)}")
        raw_response = await self.llm.generate_response(conversation.messages)
        self.logger.info(f"Step 2: LLM Raw Result: '{raw_response}'")
        
        try:
            import json
            import re
            # Clean Markdown code blocks if present
            cleaned_response = re.sub(r'```(?:json)?', '', raw_response).strip()
            segments = json.loads(cleaned_response)
            
            # Handle Single Object or Wrapped List
            if isinstance(segments, dict):
                # Check for common wrapping keys
                for key in ['data', 'segments', 'items', 'response']:
                    if key in segments and isinstance(segments[key], list):
                        segments = segments[key]
                        break
                else:
                    # If no list found, treat as single segment
                    segments = [segments]
            
            if not isinstance(segments, list):
                raise ValueError("Parsed JSON is not a list")

            ai_text = " ".join([seg.get("text", "") for seg in segments])
            
            # Fallback for empty response
            if not ai_text.strip():
                self.logger.warning("LLM returned empty text, using fallback.")
                fallback_msg = "Desculpe, não consegui gerar uma resposta para isso."
                ai_text = fallback_msg
                segments = [{"text": fallback_msg, "lang": "pt"}]
                
        except Exception as e:
            self.logger.error(f"Failed to parse LLM JSON response: {e}. Raw: {raw_response}")
            segments = [{"text": raw_response, "lang": "pt"}]
            ai_text = raw_response
            
            # Double check if even raw_response was empty
            if not ai_text.strip():
                 fallback_msg = "Desculpe, ocorreu um erro na geração da resposta."
                 ai_text = fallback_msg
                 segments = [{"text": fallback_msg, "lang": "pt"}]

        # 4. Update History (AI) - Store plain text for history
        ai_message = Message(content=ai_text, role="assistant")
        conversation.add_message(ai_message)
        
        # 5. TTS: Segmented Synthesis
        self.logger.info(f"Step 3: Starting Segmented TTS")
        audio_segments = []
        for seg in segments:
            text_seg = seg.get("text", "")
            lang_seg = seg.get("lang", "pt")
            if not text_seg.strip():
                continue
            
            emb_audio = await self.tts.synthesize(text_seg, lang=lang_seg)
            if emb_audio:
                audio_segments.append(emb_audio)
        
        ai_audio_bytes = self._merge_wavs(audio_segments)
        self.logger.info(f"Step 3: TTS complete. Merged Audio size: {len(ai_audio_bytes)} bytes")
        
        return {
            "user_text": user_text,
            "ai_text": ai_text,
            "ai_audio": ai_audio_bytes,
            "conversation_id": str(conversation.id)
        }

    def _merge_wavs(self, wav_bytes_list: list[bytes]) -> bytes:
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
        import struct
        
        # RIFF chunk size (Total file size - 8)
        new_riff_size = struct.pack('<I', total_size - 8)
        
        # Data subchunk size
        new_data_size = struct.pack('<I', len(data))
        
        new_header = header[:4] + new_riff_size + header[8:40] + new_data_size
        
        return new_header + data

class ProcessUserTextUseCase:
    def __init__(
        self, 
        llm_service: LLMService, 
        tts_service: TTSService
    ):
        self.llm = llm_service
        self.tts = tts_service
        self.logger = logging.getLogger(__name__)

    async def execute(self, conversation: Conversation, text: str) -> dict:
        # 1. Update History (User)
        user_message = Message(content=text, role="user")
        conversation.add_message(user_message)
        
        # 1.5. TTS: User Text -> Audio
        self.logger.info(f"Step 0 (Text): Synthesizing audio for user text")
        user_audio_bytes = await self.tts.synthesize(text, lang="pt") # Assume User is PT for now or detect?

        # 2. LLM: Text -> Text Response
        self.logger.info(f"Step 1 (Text): Sending to LLM.")
        raw_response = await self.llm.generate_response(conversation.messages)
        self.logger.info(f"Step 1 (Text): LLM Raw Result: '{raw_response}'")
        
        try:
            import json
            import re
            # Clean Markdown code blocks if present
            cleaned_response = re.sub(r'```(?:json)?', '', raw_response).strip()
            segments = json.loads(cleaned_response)
            
            # Handle Single Object or Wrapped List
            if isinstance(segments, dict):
                # Check for common wrapping keys
                for key in ['data', 'segments', 'items', 'response']:
                    if key in segments and isinstance(segments[key], list):
                        segments = segments[key]
                        break
                else:
                    # If no list found, treat as single segment
                    segments = [segments]
            
            if not isinstance(segments, list):
                raise ValueError("Parsed JSON is not a list")

            ai_text = " ".join([seg.get("text", "") for seg in segments])
            
            # Fallback for empty response
            if not ai_text.strip():
                self.logger.warning("LLM returned empty text, using fallback.")
                fallback_msg = "Desculpe, não consegui gerar uma resposta para isso."
                ai_text = fallback_msg
                segments = [{"text": fallback_msg, "lang": "pt"}]
                
        except Exception as e:
            self.logger.error(f"Failed to parse LLM JSON response: {e}. Raw: {raw_response}")
            segments = [{"text": raw_response, "lang": "pt"}]
            ai_text = raw_response
            
            # Double check if even raw_response was empty
            if not ai_text.strip():
                 fallback_msg = "Desculpe, ocorreu um erro na geração da resposta."
                 ai_text = fallback_msg
                 segments = [{"text": fallback_msg, "lang": "pt"}]
        
        # 3. Update History (AI)
        ai_message = Message(content=ai_text, role="assistant")
        conversation.add_message(ai_message)
        
        # 4. TTS: Segmented Synthesis
        self.logger.info(f"Step 2 (Text): Starting Segmented TTS")
        audio_segments = []
        for seg in segments:
            text_seg = seg.get("text", "")
            lang_seg = seg.get("lang", "pt")
            if not text_seg.strip():
                continue
            
            emb_audio = await self.tts.synthesize(text_seg, lang=lang_seg)
            if emb_audio:
                audio_segments.append(emb_audio)
        
        ai_audio_bytes = self._merge_wavs(audio_segments)
        self.logger.info(f"Step 2 (Text): TTS complete. Merged Audio size: {len(ai_audio_bytes)} bytes")
        
        return {
            "user_text": text,
            "user_audio": user_audio_bytes,
            "ai_text": ai_text,
            "ai_audio": ai_audio_bytes,
            "conversation_id": str(conversation.id)
        }

    def _merge_wavs(self, wav_bytes_list: list[bytes]) -> bytes:
        # Reuse logic or call static
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
        import struct
        new_riff_size = struct.pack('<I', total_size - 8)
        new_data_size = struct.pack('<I', len(data))
        new_header = header[:4] + new_riff_size + header[8:40] + new_data_size
        
        return new_header + data

