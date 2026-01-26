"""
FastAPI application for Language Learning AI.

Provides endpoints for speech and text-based conversation processing
with bilingual (Portuguese/English) responses.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID, uuid4
import os
import base64
from functools import lru_cache

# Domain & Infrastructure
from .domain.entities import Conversation
from .domain.interfaces import STTService, LLMService, TTSService, ConversationRepository
from .infrastructure.stt_service import FasterWhisperSTTService
from .infrastructure.llm_service import OllamaLLMService
from .infrastructure.tts_service import PiperTTSService
from .infrastructure.repositories import InMemoryConversationRepository
from .application.use_cases import ProcessUserSpeechUseCase, ProcessUserTextUseCase

# --- App Setup ---
app = FastAPI(title="Language Learning AI API")

# Serve static audio files
os.makedirs("static/audio", exist_ok=True)
app.mount("/audio", StaticFiles(directory="static/audio"), name="audio")

# --- Dependency Injection Providers ---

@lru_cache(maxsize=1)
def get_stt_service() -> STTService:
    return FasterWhisperSTTService(api_url="http://localhost:8001")

@lru_cache(maxsize=1)
def get_llm_service() -> LLMService:
    return OllamaLLMService(model=os.environ.get("LLM_MODEL_NAME", "mistral"))

@lru_cache(maxsize=1)
def get_tts_service() -> TTSService:
    return PiperTTSService(api_url="http://localhost:8002")

@lru_cache(maxsize=1)
def get_conversation_repo() -> ConversationRepository:
    return InMemoryConversationRepository()

def get_speech_use_case(
    stt: STTService = Depends(get_stt_service),
    llm: LLMService = Depends(get_llm_service),
    tts: TTSService = Depends(get_tts_service),
) -> ProcessUserSpeechUseCase:
    return ProcessUserSpeechUseCase(stt, llm, tts)

def get_text_use_case(
    llm: LLMService = Depends(get_llm_service),
    tts: TTSService = Depends(get_tts_service),
) -> ProcessUserTextUseCase:
    return ProcessUserTextUseCase(llm, tts)

# --- API Models ---

class SegmentDTO(BaseModel):
    text: str
    lang: str

class StructuredTextResponse(BaseModel):
    user_text: str
    ai_text: str
    segments: List[SegmentDTO]
    conversation_id: str
    audio_urls: Optional[List[str]] = None
    user_audio_base64: Optional[str] = None

class TextInput(BaseModel):
    text: str
    conversation_id: Optional[str] = None

# --- Endpoints ---

@app.post("/conversation/speech", response_model=StructuredTextResponse)
async def process_speech(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = None,
    repo: ConversationRepository = Depends(get_conversation_repo),
    use_case: ProcessUserSpeechUseCase = Depends(get_speech_use_case)
):
    if conversation_id:
        conversation = await repo.get_by_id(UUID(conversation_id))
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation()

    audio_bytes = await file.read()
    result = await use_case.execute(conversation, audio_bytes)
    await repo.save(conversation)

    segments = [SegmentDTO(text=seg["text"], lang=seg["lang"]) for seg in result.get("segments", [])]

    return StructuredTextResponse(
        user_text=result["user_text"],
        ai_text=result["ai_text"],
        segments=segments,
        conversation_id=result["conversation_id"],
        audio_urls=result.get("audio_urls", [])
    )

@app.post("/conversation/text", response_model=StructuredTextResponse)
async def process_text(
    input_data: TextInput,
    repo: ConversationRepository = Depends(get_conversation_repo),
    use_case: ProcessUserTextUseCase = Depends(get_text_use_case)
):
    if input_data.conversation_id:
        conversation = await repo.get_by_id(UUID(input_data.conversation_id))
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation()

    result = await use_case.execute(conversation, input_data.text)
    await repo.save(conversation)

    user_audio_b64 = None
    if result.get("user_audio"):
        user_audio_b64 = base64.b64encode(result["user_audio"]).decode("utf-8")

    segments = [SegmentDTO(text=seg["text"], lang=seg["lang"]) for seg in result.get("segments", [])]

    return StructuredTextResponse(
        user_text=result["user_text"],
        ai_text=result["ai_text"],
        segments=segments,
        conversation_id=result["conversation_id"],
        audio_urls=result.get("audio_urls", []),
        user_audio_base64=user_audio_b64
    )

@app.get("/health")
def health():
    return {"status": "ok"}
