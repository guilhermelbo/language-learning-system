# Repository Guidelines

## ⛔ External Infrastructure — DO NOT MODIFY

The following Docker containers are **shared infrastructure** running outside this project. They must **never** be stopped, removed, recreated, or have their configuration changed by any agent action:

| Container | Purpose | Port |
|-----------|---------|------|
| `llamacpp` | Local LLM server (Qwen3.5) | 8080 |
| `hindsight` | Agent memory backend | 8888 |
| `searxng` | Web search engine | 8081 |

**This means you must never run:**
- `docker stop llamacpp` / `hindsight` / `searxng`
- `docker rm llamacpp` / `hindsight` / `searxng`
- `docker run ... --name llamacpp` / `hindsight` / `searxng`
- `docker restart` / `docker kill` on any of the above

If a task seems to require modifying these containers, **stop and ask the user** instead of proceeding autonomously.

---

## Project Overview

**LingoAI** is an AI-powered language learning tutor focused on teaching English to Portuguese speakers. The system enables real-time voice and text conversations using locally-hosted AI models for privacy and low latency.

**Core Flow**: User Voice → STT (Speech-to-Text) → LLM (Mistral via Ollama) → TTS (Piper) → Audio Playback

## Architecture & Data Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Frontend   │────▶│  Backend     │────▶│  AI Services    │
│  (Next.js)  │     │  (FastAPI)   │     │  (Docker)       │
└─────────────┘     └──────────────┘     └─────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │   STT       │    │    LLM      │    │   TTS       │
   │ Port 8001   │    │  Port 11434 │    │  Port 8002  │
   └─────────────┘    └─────────────┘    └─────────────┘
```

### Backend Architecture (Clean Architecture + DDD)

- **`domain/`**: Core entities (`Student`, `Message`, `Conversation`) and service interfaces (`STTService`, `LLMService`, `TTSService`)
- **`application/`**: Use cases (`ProcessUserSpeechUseCase`, `ProcessUserTextUseCase`) orchestrating business logic
- **`infrastructure/`**: Concrete implementations (OllamaLLMService, OpenAICompatibleLLMService, FasterWhisperSTTService, PiperTTSService)
- **`main.py`**: FastAPI entry point with REST endpoints

### Data Flow

1. **Speech Input**: `POST /conversation/speech` receives audio blob
2. **STT Transcription**: `FasterWhisperSTTService.transcribe()` converts audio to text
3. **LLM Processing**: `OllamaLLMService.generate_response()` generates JSON response with bilingual segments
4. **TTS Synthesis**: `PiperTTSService.synthesize()` converts each text segment to audio
5. **Audio Merge**: WAVE segments merged and returned to frontend

## Key Directories

| Path | Purpose |
|------|---------|
| `backend/src/` | Python backend with Clean Architecture |
| `backend/src/domain/` | Core entities and service interfaces |
| `backend/src/application/` | Business logic use cases |
| `backend/src/infrastructure/` | External service integrations |
| `backend/src/main.py` | FastAPI application entry point |
| `ai_services/stt/` | Faster-Whisper STT microservice (Docker) |
| `ai_services/tts/` | Piper TTS microservice (Docker) |
| `frontend/app/` | Next.js 14 App Router pages |
| `frontend/components/` | React components (ChatInterface, VoiceButton) |
| `specs/` | Architecture decision records and specifications |

## Development Commands

### Run Entire Project (Docker Compose)

The simplest way to run the entire project is with Docker Compose:

```bash
# Build and start all services
docker-compose up --build

# Pull Ollama model (first run only - in a new terminal)
docker exec -it ollama ollama pull mistral
```

The project will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000

### Backend (Python)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac or .\venv\Scripts\activate (Windows)
pip install -r requirements.txt

# Run development server
uvicorn src.main:app --reload
```

**API Endpoints**:
- `POST /conversation/speech` - Process voice input (multipart form-data with `file` blob)
- `POST /conversation/text` - Process text input (JSON body)
- `GET /health` - Health check

### Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev  # http://localhost:3000
```

### AI Services (Docker)

For development without the full stack, individual services can be started:

```bash
# Start all AI services
docker-compose up -d stt tts ollama

# Pull Ollama model (first run only)
docker exec ollama ollama pull mistral
```

**Service URLs**:
- STT: `http://localhost:8001/transcribe`
- TTS: `http://localhost:8002/synthesize`
- Ollama: `http://localhost:11434`

## Code Conventions & Patterns

### Python Backend

**Type Hints**: Required for all function signatures. Use union types with `|` (PEP 604).

```python
from typing import Optional
from dataclasses import dataclass, field

@dataclass
class Message:
    content: str
    role: str  # 'user' or 'assistant'
```

**Error Handling**: Log with `logging` module, return empty strings/blobs on service failures (graceful degradation).

```python
logger = logging.getLogger(__name__)
try:
    result = await self.stt.transcribe(audio_data)
except Exception as e:
    logger.error(f"STT Error: {e}")
    return ""
```

**Async I/O**: All external service calls use `async/await` with `httpx.AsyncClient`.

```python
async with httpx.AsyncClient() as client:
    response = await client.post(url, ...)
```

**JSON Response Format**: LLM outputs must be strict JSON array:
```json
[
  {"text": "Portuguese segment", "lang": "pt"},
  {"text": "English segment", "lang": "en"}
]
```

### Frontend (TypeScript)

**React Components**: Use `"use client"` directive for client components. Functional components with TypeScript interfaces.

```typescript
"use client";
import React from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  id: string;
}
```

**Audio Recording**: Use `MediaRecorder` API with WebM format (Opus codec preferred).

```typescript
const mimeTypes = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4'];
let selectedMimeType = mimeTypes.find(navigator.mediaDevices.getUserMedia)
  .find(type => MediaRecorder.isTypeSupported(type));
```

**State Management**: Local `useState` for messages and processing state. Conversation ID persisted for context.

```typescript
const [messages, setMessages] = useState<Message[]>([]);
const [isProcessing, setIsProcessing] = useState(false);
const [conversationId, setConversationId] = useState<string | null>(null);
```

### API Communication

**Backend → AI Services**: HTTP POST with `httpx.AsyncClient`.

**Frontend → Backend**:
- Speech: `FormData` with `multipart/form-data` (key: `file`, optional `conversation_id`)
- Text: JSON body `{"text": "...", "conversation_id": "..."}`

## Important Files

| File | Purpose |
|------|---------|
| `backend/src/main.py` | FastAPI routes and service initialization |
| `backend/src/config.py` | Environment configuration (pydantic-settings) |
| `backend/src/infrastructure/llm_service.py` | Ollama/OpenAI-compatible LLM implementations |
| `backend/src/infrastructure/stt_service.py` | Faster-Whisper transcription client |
| `backend/src/infrastructure/tts_service.py` | Piper TTS synthesis client |
| `backend/src/application/use_cases.py` | Core conversation flow logic |
| `docker-compose.yml` | Service orchestration (Ollama, STT, TTS) |
| `frontend/app/page.tsx` | Main chat interface and audio handling |
| `specs/000-global-context/spec.md` | System architecture specification |

## Runtime & Tooling Preferences

### Required Runtimes
- **Backend**: Python 3.10+
- **Frontend**: Node.js 18+ (Next.js 14 requires Node 18.17+)
- **AI Services**: Docker with Python 3.10 slim

### Package Managers
- **Python**: `pip` (virtualenv recommended)
- **Frontend**: `npm` or `bun` (project uses `npm`)

### AI Models (Local Only)
- **LLM**: Ollama with `mistral` model (7B recommended)
- **STT**: Faster-Whisper `small` model (CPU-compatible)
- **TTS**: Piper `pt_BR-faber-medium.onnx` (Portuguese) and `en_US-lessac-medium.onnx` (English)

### Development Tools
- **Backend Lint/Type Check**: Standard Python linting (mypy/ruff optional)
- **Frontend**: ESLint + Next.js ESLint plugin
- **Testing**: `pytest` for backend, Next.js built-in tests for frontend

## Testing & QA

### Backend Testing

```bash
cd backend
pytest tests/ -v
```

**Key Test Files**:
- `tests/test_llm_config.py` - LLM configuration validation
- `tests/reproduce_llm_issue.py` - Issue reproduction scripts

### Frontend Testing

```bash
cd frontend
npm run lint  # ESLint check
```

### Manual QA Checklist

- [ ] STT transcribes audio correctly (Portuguese/English)
- [ ] LLM generates valid JSON response with `text` and `lang` fields
- [ ] TTS produces audible WAV output for both languages
- [ ] Audio segments merge without clipping or gaps
- [ ] Frontend plays TTS audio correctly
- [ ] Error handling shows user-friendly messages

## Architecture Notes

### Service Interfaces (Domain Layer)

All external services implement interfaces defined in `domain/interfaces.py`:

```python
class STTService(ABC):
    async def transcribe(self, audio_data: bytes) -> str

class LLMService(ABC):
    async def generate_response(self, conversation_history: list[Message]) -> str
    async def generate_response_stream(self, conversation_history: list[Message]) -> AsyncGenerator[str, None]

class TTSService(ABC):
    async def synthesize(self, text: str, lang: str = "pt") -> bytes
    async def synthesize_to_file(self, text: str, output_path: str) -> str
```

### Configuration

Environment variables (from `.env` or OS):

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | `ollama` or `openai_compatible` |
| `LLM_MODEL_NAME` | `mistral` | Model name for LLM |
| `LLM_BASE_URL` | `http://localhost:11434/v1` | OpenAI-compatible endpoint |
| `STT_API_URL` | `http://localhost:8001` | STT service URL |
| `TTS_API_URL` | `http://localhost:8002` | TTS service URL |
| `PIPER_MODEL_PATH` | `pt_BR-faber-medium.onnx` | Default TTS model |

### Known Limitations

1. **No Database**: Conversations not persisted (in-memory only)
2. **No VAD**: Turn detection via manual mic button press
3. **Sequential Processing**: STT → LLM → TTS (not parallel)
4. **No Error Recovery**: Service failures return empty responses

### Future Roadmap

- [ ] Database integration (SQLite/PostgreSQL)
- [ ] Voice Activity Detection (VAD) for natural turn-taking
- [ ] Spaced repetition vocabulary system
- [ ] Grammar error detection and feedback
- [ ] Multiple student profiles and long-term memory
- [x] Full Dockerization of entire stack
