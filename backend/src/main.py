from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

# Domain & Infrastructure
from .config import get_settings
from .domain.entities import Conversation
from .infrastructure.stt_service import FasterWhisperSTTService
from .infrastructure.llm_factory import create_llm_service
from .infrastructure.tts_service import PiperTTSService
from .infrastructure.repositories import InMemoryConversationRepository, InMemoryOmniSessionRepository
from .infrastructure.omni_service import VoiceServiceUnavailableError
from .infrastructure.voice_factory import create_voice_service
from .application.use_cases import ProcessUserSpeechUseCase, ProcessUserTextUseCase, ProcessOmniVoiceUseCase

app = FastAPI(title="Language Learning AI API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings = get_settings()

stt_service = FasterWhisperSTTService(api_url=settings.stt_api_url)
llm_service = create_llm_service(settings)
tts_service = PiperTTSService(api_url=settings.tts_api_url)

conversation_repo = InMemoryConversationRepository()
omni_session_repo = InMemoryOmniSessionRepository()

use_case = ProcessUserSpeechUseCase(stt_service, llm_service, tts_service)
text_use_case = ProcessUserTextUseCase(llm_service, tts_service)

# Voice channel (only instantiated when enabled)
omni_use_case: ProcessOmniVoiceUseCase | None = None
if settings.voice_enabled:
    _voice_service = create_voice_service(settings)
    omni_use_case = ProcessOmniVoiceUseCase(_voice_service, omni_session_repo)


import base64
import json


class TextResponse(BaseModel):
    user_text: str
    ai_text: str
    conversation_id: str
    audio_base64: Optional[str] = None
    user_audio_base64: Optional[str] = None


class OmniTextResponse(BaseModel):
    conversation_id: str
    user_text: str
    ai_text: str
    audio_base64: Optional[str] = None
    pronunciation_events: list = []


class TextInput(BaseModel):
    text: str
    conversation_id: Optional[str] = None

@app.post("/conversation/speech", response_model=TextResponse)
async def process_speech(
    file: UploadFile = File(...), 
    conversation_id: Optional[str] = None
):
    # Load or Create Conversation
    if conversation_id:
        conversation = await conversation_repo.get_by_id(UUID(conversation_id))
        if not conversation:
             raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation()
        await conversation_repo.save(conversation)
    
    # Read Audio
    audio_bytes = await file.read()
    
    # Execute Use Case
    result = await use_case.execute(conversation, audio_bytes)
    
    # Save State
    await conversation_repo.save(conversation)
    
    # Encode Audio to Base64
    audio_b64 = None
    if result.get("ai_audio"):
        audio_b64 = base64.b64encode(result["ai_audio"]).decode("utf-8")
    
    return {
        "user_text": result["user_text"],
        "ai_text": result["ai_text"],
        "conversation_id": result["conversation_id"],
        "audio_base64": audio_b64
    }

@app.post("/conversation/text", response_model=TextResponse)
async def process_text(
    input_data: TextInput
):
    # Load or Create Conversation
    if input_data.conversation_id:
        conversation = await conversation_repo.get_by_id(UUID(input_data.conversation_id))
        if not conversation:
             raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = Conversation()
        await conversation_repo.save(conversation)
    
    # Execute Use Case
    result = await text_use_case.execute(conversation, input_data.text)
    
    # Save State
    await conversation_repo.save(conversation)
    
    # Encode Audio to Base64
    audio_b64 = None
    if result.get("ai_audio"):
        audio_b64 = base64.b64encode(result["ai_audio"]).decode("utf-8")

    user_audio_b64 = None
    if result.get("user_audio"):
        user_audio_b64 = base64.b64encode(result["user_audio"]).decode("utf-8")
    
    return {
        "user_text": result["user_text"],
        "ai_text": result["ai_text"],
        "conversation_id": result["conversation_id"],
        "audio_base64": audio_b64,
        "user_audio_base64": user_audio_b64
    }

@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Omni Voice Channel endpoints
# ---------------------------------------------------------------------------

@app.post("/conversation/omni/speech", response_model=OmniTextResponse)
async def process_omni_speech(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(default=None),
    language: str = Form(default="en-US"),
):
    if not settings.voice_enabled or omni_use_case is None:
        raise HTTPException(status_code=503, detail="omni_unavailable")

    # Validate audio size via duration proxy (byte length heuristic: 16kHz mono 16-bit ≈ 32000 B/s)
    audio_bytes = await file.read()
    max_bytes = settings.voice_max_audio_seconds * 32000 * 2  # generous upper bound
    if len(audio_bytes) > max_bytes:
        raise HTTPException(status_code=400, detail="audio_too_long")

    # Resolve existing session
    session = None
    if conversation_id and conversation_id.startswith("omni-"):
        raw_id = conversation_id[len("omni-"):]
        try:
            session = await omni_session_repo.get_by_id(UUID(raw_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid conversation_id format")
        if session is None:
            raise HTTPException(status_code=404, detail="Conversation not found")

    try:
        result = await omni_use_case.execute(
            audio_data=audio_bytes,
            session=session,
            language=language,
        )
    except VoiceServiceUnavailableError as exc:
        import logging as _logging
        _logging.getLogger(__name__).error("VoiceServiceUnavailableError: %s", exc)
        raise HTTPException(status_code=503, detail="omni_unavailable")

    return result


@app.get("/conversation/omni/status")
async def omni_status():
    if not settings.voice_enabled:
        return {"omni_enabled": False, "model_loaded": False, "omni_api_url": None}

    # Probe health of the voice service
    _health_svc = create_voice_service(settings)
    health_data = await _health_svc.health_check()
    return {
        "omni_enabled": True,
        "model_loaded": health_data.get("model_loaded", False),
        "omni_api_url": settings.voice_api_url,
    }
