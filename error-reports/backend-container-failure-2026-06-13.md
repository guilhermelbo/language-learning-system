# Backend Container Failure Report

## Timestamp
2026-06-13 18:xx UTC

## Container Status
- **Container**: `lingo-backend`
- **Status**: `Restarting (1) X seconds ago` (infinite restart loop)
- **Image**: `language-learning-system-backend:latest`
- **CMD**: `["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]`

## Error Analysis

### Root Cause
The backend container fails to start due to an `openai.OpenAIError` exception during the `AsyncOpenAI` client initialization.

### Error Trace
```
File "/app/src/infrastructure/llm_factory.py", line 16, in create_llm_service
    return OpenAICompatibleLLMService(
File "/app/src/infrastructure/llm_service.py", line 77, in __init__
    self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)
File "/usr/local/lib/python3.10/site-packages/openai/_client.py", line 700, in __init__
    raise OpenAIError(
openai.OpenAIError: Missing credentials. Please pass an `api_key`, `workload_identity`, `admin_api_key`, or set the `OPENAI_API_KEY` or `OPENAI_ADMIN_KEY` environment variable.
```

### Code Flow
1. `main.py` line 31 calls `create_llm_service(settings)`
2. `llm_factory.py` line 14-15 detects `LLM_PROVIDER=openai_compatible`
3. Tries to instantiate `OpenAICompatibleLLMService` with settings
4. `llm_service.py` line 77 calls `AsyncOpenAI(base_url=base_url, api_key=api_key)`
5. `openai.AsyncOpenAI.__init__` raises `OpenAIError` because `api_key` is invalid/empty

## Configuration Inspection

### Environment Variables (from docker-compose.yml)
```yaml
environment:
  - LLM_PROVIDER=openai_compatible
  - LLM_MODEL_NAME=Qwen3.5-35B-A3B-UD-IQ3_S.gguf
  - LLM_BASE_URL=http://localhost:8080/v1
  - LLM_TEMPERATURE=0.7
  - LLM_MAX_TOKENS=1024
  - LLM_ENABLE_THINKING=true
  - STT_API_URL=http://stt:8001
  - TTS_API_URL=http://tts:8002
```

**Missing**: `LLM_API_KEY` environment variable is NOT defined in docker-compose.

### Default Configuration (config.py)
```python
llm_api_key: str = Field(default="", alias="LLM_API_KEY")  # Empty string default
```

### Problem Summary
The `OpenAICompatibleLLMService` receives an empty string `""` for `api_key` because:
1. `LLM_API_KEY` is not set in docker-compose environment
2. The config defaults to empty string `""`
3. `openai.AsyncOpenAI` does NOT accept empty strings - it requires either:
   - A valid API key string, OR
   - `None` to skip authentication

## Affected Files
- `backend/src/infrastructure/llm_factory.py` - Line 14-22 (no validation for empty api_key)
- `backend/src/infrastructure/llm_service.py` - Line 77 (no conditional None handling)
- `backend/src/config.py` - Line 20 (default is empty string instead of None)
- `backend/requirements.txt` - Missing `python-multipart` dependency
- `docker-compose.yml` - Missing `LLM_API_KEY` environment variable

## Root Cause Summary
The `AsyncOpenAI` client library enforces strict credential requirements. When using an OpenAI-compatible API like llama.cpp (which doesn't require authentication), the `api_key` parameter must be explicitly set to `None`, not an empty string. The current implementation passes an empty string, which the OpenAI library treats as invalid credentials and raises an error.

## Impact
- Backend container cannot start
- No REST API available at port 8000
- Frontend cannot send requests (shows "Error sending text: {}")
- Complete application stack failure

---
## Resolution

### Root Cause Analysis

The `openai.AsyncOpenAI` client has strict credential requirements:
- It raises `OpenAIError` when `api_key=""` (empty string) is passed
- It raises `OpenAIError` when `api_key=None` AND no environment variable is set
- It **works** when `api_key` is any non-empty string (even fake values for unauthenticated APIs)

### Fixes Applied

1. **backend/src/infrastructure/llm_service.py** (line 77-79):
   - Changed `api_key: str = "ollama"` to `api_key: str | None = None`
   - Added logic to use a fake key when no real key is provided:
     ```python
     safe_api_key = api_key if api_key else "fake-key-for-unauthenticated-api"
     self.client = AsyncOpenAI(base_url=base_url, api_key=safe_api_key)
     ```

2. **backend/requirements.txt** (line 7):
   - Added `python-multipart` dependency required by FastAPI for form data handling

3. **backend/src/config.py** (line 20):
   - Changed `llm_api_key: str` to `str | None = Field(default=None)`
   - Added validator to convert empty strings to None

### Verification

- Backend container starts successfully
- Health endpoint returns `{ "status": "ok" }`
- Application ready for text and speech processing

---
