"""
FastAPI application for Language Learning AI.

Provides endpoints for speech and text-based conversation processing
with bilingual (Portuguese/English) responses.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
import os
import base64

# Domain & Infrastructure
from .domain.entities import Conversation
from .infrastructure.stt_service import FasterWhisperSTTService
from .infrastructure.llm_service import OllamaLLMService
from .infrastructure.tts_service import PiperTTSService
from .infrastructure.repositories import InMemoryConversationRepository
from .application.use_cases import ProcessUserSpeechUseCase, ProcessUserTextUseCase

app = FastAPI(title="Language Learning AI API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
STT_MODEL_SIZE = "small"
LLM_MODEL_NAME = "mistral"
PIPER_MODEL_PATH = os.environ.get("PIPER_MODEL_PATH", "pt_BR-faber-medium.onnx")

# Global Dependencies (Singleton-ish for MVP)
try:
    stt_service = FasterWhisperSTTService(api_url="http://localhost:8001")
    llm_service = OllamaLLMService(model=LLM_MODEL_NAME)
    tts_service = PiperTTSService(api_url="http://localhost:8002")

    conversation_repo = InMemoryConversationRepository()

    use_case = ProcessUserSpeechUseCase(stt_service, llm_service, tts_service)
    text_use_case = ProcessUserTextUseCase(llm_service, tts_service)

except Exception as e:
    print(f"Error initializing services: {e}")
    pass


# API Models

class SegmentDTO(BaseModel):
    """A text segment in a specific language."""
    text: str
    lang: str


class StructuredTextResponse(BaseModel):
    """
    Response with structured bilingual segments.

    Includes both combined text (backward compatible) and
    structured segments for rich display.
    """
    user_text: str
    ai_text: str
    segments: List[SegmentDTO]
    conversation_id: str
    audio_base64: Optional[str] = None
    user_audio_base64: Optional[str] = None


class TextInput(BaseModel):
    """Input for text-based conversation."""
    text: str
    conversation_id: Optional[str] = None


@app.post("/conversation/speech", response_model=StructuredTextResponse)
async def process_speech(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = None
):
    """
    Process speech input through the AI pipeline.

    Transcribes audio, generates bilingual response, and synthesizes speech.
    """
    if not tts_service:
        raise HTTPException(status_code=500, detail="TTS Service not initialized")

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

    # Convert segments to DTOs
    segments = [
        SegmentDTO(text=seg["text"], lang=seg["lang"])
        for seg in result.get("segments", [])
    ]

    return StructuredTextResponse(
        user_text=result["user_text"],
        ai_text=result["ai_text"],
        segments=segments,
        conversation_id=result["conversation_id"],
        audio_base64=audio_b64
    )


@app.post("/conversation/text", response_model=StructuredTextResponse)
async def process_text(input_data: TextInput):
    """
    Process text input through the AI pipeline.

    Generates bilingual response and synthesizes speech for both
    user input and AI response.
    """
    if not tts_service:
        raise HTTPException(status_code=500, detail="TTS Service not initialized")

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

    # Convert segments to DTOs
    segments = [
        SegmentDTO(text=seg["text"], lang=seg["lang"])
        for seg in result.get("segments", [])
    ]

    return StructuredTextResponse(
        user_text=result["user_text"],
        ai_text=result["ai_text"],
        segments=segments,
        conversation_id=result["conversation_id"],
        audio_base64=audio_b64,
        user_audio_base64=user_audio_b64
    )


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}
