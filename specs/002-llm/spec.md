# Feature: LLM Service

## Status
- **Status**: Implementation Stable
- **Priority**: Critical

## Introduction
The LLM Service acts as the brain, generating contextual and pedagogical responses using Ollama.

## User Stories
- As a student, I want corrections on my grammar.
- As a student, I want the tutor to remember my previous mistakes.

## Functional Requirements
1. **Context**: Must accept conversation history.
2. **Pedagogy**: System prompt enforces specific JSON output for multi-part (bilingual) responses.
3. **Multilingual**: Support EN and PT.
4. **Output Format**: Strict JSON Array.

## Technical Implementation
### Service
- **Type**: In-process Library / External Service Connector
- **Path**: `backend/src/infrastructure/llm_service.py`
- **Engine**: Ollama (local inference)
- **Model**: Default `mistral`

### Schema
**System Prompt Restriction**:
Output must be a JSON array of objects:
```json
[
    {"text": "Ola, tudo bem?", "lang": "pt"},
    {"text": "Hello, how are you?", "lang": "en"}
]
```

### Class Structure
- **Class**: `OllamaLLMService`
- **Methods**:
    - `generate_response(history)`: Returns complete JSON string.
    - `generate_response_stream(history)`: Yields chunks (note: Ollama streaming JSON might need special handling).
