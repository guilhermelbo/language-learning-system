from fastapi import FastAPI, UploadFile, File, HTTPException
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

try:
    settings = get_settings()

    stt_service = FasterWhisperSTTService(api_url=settings.stt_api_url)
    llm_service = create_llm_service(settings)
    tts_service = PiperTTSService(api_url=settings.tts_api_url)

    conversation_repo = InMemoryConversationRepository()
    
    use_case = ProcessUserSpeechUseCase(stt_service, llm_service, tts_service)
    text_use_case = ProcessUserTextUseCase(llm_service, tts_service)
    
except Exception as e:
    print(f"Error initializing services: {e}")
    # Application might be unstable
    pass


import base64

class TextResponse(BaseModel):
    user_text: str
    ai_text: str
    conversation_id: str
    audio_base64: Optional[str] = None
    user_audio_base64: Optional[str] = None

class TextInput(BaseModel):
    text: str
    conversation_id: Optional[str] = None

@app.post("/conversation/speech", response_model=TextResponse)
async def process_speech(
    file: UploadFile = File(...), 
    conversation_id: Optional[str] = None
):
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
