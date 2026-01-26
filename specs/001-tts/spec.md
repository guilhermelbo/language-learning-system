# Feature: Text-to-Speech (TTS)

## Status
- **Status**: Implementation Stable
- **Priority**: High

## Introduction
The TTS module is responsible for converting the AI's text responses into natural-sounding speech using Piper.

## User Stories
- As a user, I want to hear the tutor speak naturally so I can practice listening.
- As a developer, I want low latency (<200ms) so the conversation feels real-time.

## Functional Requirements
1. **Latency**: <200ms for first byte of audio.
2. **Voices**: Support for English (`en_US-lessac-medium.onnx`) and Portuguese (`pt_BR-faber-medium.onnx`) voices.
3. **Format**: Returns `audio/wav`.
4. **Input Sanitization**: Must handle newlines by replacing them with spaces to prevent Piper parsing errors.

## Technical Implementation
### Service
- **Type**: Microservice (FastAPI)
- **Path**: `ai_services/tts/app.py`
- **Engine**: Piper TTS (running via subprocess)

### API Contract
- **Endpoint**: `POST /synthesize`
- **Request Body**:
  ```json
  {
    "text": "Hello world"
  }
  ```
- **Query Params**: `lang` ("pt" or "en", default: "pt")
- **Response**: Binary `audio/wav` stream.

### Infrastructure Wrapper
- **Class**: `PiperTTSService` (`backend/src/infrastructure/tts_service.py`)
- **Client**: `httpx.AsyncClient`
