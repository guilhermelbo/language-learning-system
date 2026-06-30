from __future__ import annotations
from typing import AsyncGenerator
from ..domain.interfaces import STTService, LLMService, TTSService, OmniVoiceService
from ..domain.entities import Conversation, Message, OmniVoiceSession, OmniAudioTurn, PronunciationEvent
from datetime import datetime
import base64
import json
import os
import re
import logging


def strip_thinking_blocks(response: str) -> str:
    """Remove <think>...</think> reasoning blocks and markdown wrappers from model output."""
    response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
    response = re.sub(r'</?think>', '', response)
    response = re.sub(r'```(?:json)?\s*', '', response, flags=re.DOTALL)
    response = re.sub(r'```\s*', '', response, flags=re.DOTALL)
    return response.strip()

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
            cleaned_response = strip_thinking_blocks(raw_response)
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
            cleaned_response = strip_thinking_blocks(raw_response)
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


# ---------------------------------------------------------------------------
# Omni Voice Channel Use Case
# ---------------------------------------------------------------------------

class ProcessOmniVoiceUseCase:
    def __init__(
        self,
        omni_service: OmniVoiceService,
        session_repo,
    ) -> None:
        self.omni = omni_service
        self.session_repo = session_repo
        self.logger = logging.getLogger(__name__)

    async def execute(
        self,
        audio_data: bytes,
        session: OmniVoiceSession | None,
        language: str = "en-US",
    ) -> dict:
        # Build context from prior turns for multi-turn continuity
        context: list[dict] = []
        open_corrections: list[dict] = []

        if session:
            for turn in session.turns:
                context.append({"role": "user", "content": turn.transcript_user})
                context.append({"role": "assistant", "content": turn.transcript_assistant})
            # Collect open pronunciation corrections for drill context
            if session.turns:
                last_turn = session.turns[-1]
                open_corrections = [
                    {
                        "word": ev.word,
                        "error_type": ev.error_type,
                        "correct_pronunciation": ev.correct_pronunciation,
                        "correction_attempted": ev.correction_attempted,
                        "role": "correction",
                        "content": f"Please correct pronunciation of '{ev.word}'",
                    }
                    for ev in last_turn.pronunciation_events
                    if not ev.correction_attempted
                ]
                context.extend(open_corrections)
        else:
            session = OmniVoiceSession()

        # Call the omni model service
        result = await self.omni.process_speech(
            audio=audio_data,
            language=language,
            context=context if context else None,
        )

        # Update drill state — mark open corrections as attempted
        for event in result.pronunciation_events:
            if event.word in session.drill_state:
                session.drill_state[event.word] += 1
                event.correction_attempted = True
                # If the same error reappears after a drill attempt, it didn't succeed
                event.correction_succeeded = False
            else:
                # Check if this is a NEW error or a RESOLVED one from prior turn
                was_open = any(c["word"] == event.word for c in open_corrections)
                if was_open:
                    event.correction_attempted = True
                    event.correction_succeeded = False
                    session.drill_state[event.word] = session.drill_state.get(event.word, 0) + 1

        # Mark resolved corrections (words that were open but don't appear in new events)
        resolved_words = {ev.word for ev in result.pronunciation_events}
        if session.turns:
            for prior_event in session.turns[-1].pronunciation_events:
                if not prior_event.correction_attempted and prior_event.word not in resolved_words:
                    prior_event.correction_attempted = True
                    prior_event.correction_succeeded = True

        # Save turn to session
        turn = OmniAudioTurn(
            session_id=session.id,
            assistant_audio_bytes=result.audio_bytes,
            transcript_user=result.transcript_user,
            transcript_assistant=result.transcript_assistant,
            pronunciation_events=result.pronunciation_events,
        )
        session.add_turn(turn)
        await self.session_repo.save(session)

        audio_b64 = base64.b64encode(result.audio_bytes).decode("utf-8") if result.audio_bytes else None

        return {
            "conversation_id": session.omni_id,
            "user_text": result.transcript_user,
            "ai_text": result.transcript_assistant,
            "audio_base64": audio_b64,
            "pronunciation_events": [
                {
                    "word": ev.word,
                    "error_type": ev.error_type,
                    "user_pronunciation": ev.user_pronunciation,
                    "correct_pronunciation": ev.correct_pronunciation,
                    "correction_attempted": ev.correction_attempted,
                    "correction_succeeded": ev.correction_succeeded,
                }
                for ev in result.pronunciation_events
            ],
        }


# ---------------------------------------------------------------------------
# Streaming Omni Voice Use Case
# ---------------------------------------------------------------------------

class ProcessOmniVoiceStreamUseCase:
    """Streaming variant of ProcessOmniVoiceUseCase.

    Calls process_speech_stream on the omni service and forwards all SSE
    events to the caller, saving the session after the 'done' event.
    """

    def __init__(
        self,
        omni_service: OmniVoiceService,
        session_repo,
    ) -> None:
        self.omni = omni_service
        self.session_repo = session_repo
        self.logger = logging.getLogger(__name__)

    async def execute_stream(
        self,
        audio_data: bytes,
        session: OmniVoiceSession | None,
        language: str = "en-US",
    ) -> AsyncGenerator[dict, None]:
        # Build context (same logic as ProcessOmniVoiceUseCase)
        context: list[dict] = []
        open_corrections: list[dict] = []

        if session:
            for turn in session.turns:
                context.append({"role": "user", "content": turn.transcript_user})
                context.append({"role": "assistant", "content": turn.transcript_assistant})
            if session.turns:
                last_turn = session.turns[-1]
                open_corrections = [
                    {
                        "word": ev.word,
                        "error_type": ev.error_type,
                        "correct_pronunciation": ev.correct_pronunciation,
                        "correction_attempted": ev.correction_attempted,
                        "role": "correction",
                        "content": f"Please correct pronunciation of '{ev.word}'",
                    }
                    for ev in last_turn.pronunciation_events
                    if not ev.correction_attempted
                ]
                context.extend(open_corrections)
        else:
            session = OmniVoiceSession()

        # Accumulators for turn data
        user_text: str = ""
        ai_text_parts: list[str] = []
        pe_dicts: list[dict] = []

        async for event in self.omni.process_speech_stream(
            audio=audio_data,
            language=language,
            context=context if context else None,
        ):
            event_type = event.get("event", "")

            if event_type == "transcript":
                data = json.loads(event["data"])
                user_text = data.get("user_text", "")

            elif event_type == "text_delta":
                data = json.loads(event["data"])
                ai_text_parts.append(data.get("delta", ""))

            elif event_type == "pronunciation_events":
                data = json.loads(event["data"])
                pe_dicts = data if isinstance(data, list) else []

            elif event_type == "done":
                ai_text = "".join(ai_text_parts)

                pronunciation_events = [
                    PronunciationEvent(
                        word=d.get("word", ""),
                        error_type=d.get("error_type", "other"),
                        user_pronunciation=d.get("user_pronunciation", ""),
                        correct_pronunciation=d.get("correct_pronunciation", ""),
                        correction_attempted=d.get("correction_attempted", False),
                        correction_succeeded=d.get("correction_succeeded"),
                    )
                    for d in pe_dicts
                    if d.get("word")
                ]

                turn = OmniAudioTurn(
                    session_id=session.id,
                    assistant_audio_bytes=b"",  # individual audio in sentence_audio events
                    transcript_user=user_text,
                    transcript_assistant=ai_text,
                    pronunciation_events=pronunciation_events,
                )
                session.add_turn(turn)
                await self.session_repo.save(session)

                # Override conversation_id with the real session ID
                yield {
                    "event": "done",
                    "data": json.dumps({"conversation_id": session.omni_id}),
                }
                continue

            yield event
