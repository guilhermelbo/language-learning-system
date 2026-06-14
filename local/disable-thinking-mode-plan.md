# Disable Thinking Mode in LLM Service

**Context**: The Qwen3.5-35B-A3B-UD-IQ3_S.gguf model activates thinking/reasoning mode by default, outputting `</think>` blocks with internal reasoning before the JSON response. This breaks the backend's JSON parsing since it expects a pure JSON array. The llamacpp container is shared infrastructure that must retain thinking mode for other use cases. Solution: disable thinking mode via OpenAI-compatible API parameters.

**Approach**:

### Step 1: Add temperature configuration parameter
**File**: `backend/src/infrastructure/llm_service.py`

**Edit**: Add `temperature: float` parameter to `OpenAICompatibleLLMService.__init__()` with default value `0.1` (lower temperature reduces reasoning behavior).

**Code**:
```python
class OpenAICompatibleLLMService(LLMService):
    def __init__(
        self,
        model: str = "Qwen3.5-35B-A3B-UD-IQ3_S.gguf",
        base_url: str = "http://host.docker.internal:8080/v1",
        temperature: float = 0.1,  # Lower temp reduces thinking mode
        max_tokens: int = 1024,
    ):
        self.model_name = model
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key="not-needed",  # llamacpp doesn't require auth
        )
```

**Reuse**: Existing `AsyncOpenAI` client from line 61-119.

**Reason**: Lower temperature makes model more deterministic and less likely to engage reasoning mode.

### Step 2: Pass temperature to API call
**File**: `backend/src/infrastructure/llm_service.py`

**Edit**: Add `temperature` and `max_tokens` parameters to `generate_response()` call:

**Code** (in `generate_response` method):
```python
async def generate_response(self, conversation_history: list[Message]) -> str:
    try:
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=_build_messages(conversation_history),
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"LLM error: {e}")
        return "Desculpe, ocorreu um erro na geração da resposta."
```

**Reuse**: Existing error handling pattern.

### Step 3: Update temperature in config.py
**File**: `backend/src/config.py`

**Edit**: Add `LLM_TEMPERATURE` environment variable with default `0.1`:

**Code** (add after existing config variables):
```python
LLM_TEMPERATURE: float = Field(
    default=0.1,
    description="Temperature for LLM generation (lower reduces thinking mode)"
)
```

### Step 4: Inject temperature from config
**File**: `backend/src/main.py`

**Edit**: Update `init_llm_service()` dependency injection:

**Code**:
```python
def init_llm_service() -> LLMService:
    config = get_config()
    if config.llm_provider == "ollama":
        return OllamaLLMService(
            model=config.llm_model_name,
            host=os.getenv("OLLAMA_HOST"),
        )
    elif config.llm_provider == "openai_compatible":
        return OpenAICompatibleLLMService(
            model=config.llm_model_name,
            base_url=config.llm_base_url,
            temperature=config.llm_temperature,  # New parameter
        )
    raise ValueError(f"Unknown LLM provider: {config.llm_provider}")
```

**Reuse**: Existing provider branching pattern.

### Step 5: Add environment variable to docker-compose
**File**: `docker-compose.yml`

**Edit**: Add `LLM_TEMPERATURE` to backend environment:

**Code** (inside `backend:` → `environment:`):
```yaml
- LLM_TEMPERATURE=${LLM_TEMPERATURE:-0.1}
```

**Re-read file first** to insert after line 30 (`LLM_BASE_URL`).

### Step 6: Add post-processing fallback
**File**: `backend/src/application/use_cases.py`

**Edit**: Add `strip_thinking_blocks()` function before `parse_llm_response()`:

**Code**:
```python
import re

def strip_thinking_blocks(response: str) -> str:
    """Remove thinking/reasoning blocks from model output."""
    # Remove <think>...</think> blocks
    response = re.sub(r'</think>.*?</think>', '', response, flags=re.DOTALL)
    response = re.sub(r'</think>', '', response)
    # Remove any markdown code blocks wrapping JSON
    response = re.sub(r'```(?:json)?\s*', '', response)
    response = re.sub(r'```\s*', '', response)
    return response.strip()
```

**Edit**: Call this in `parse_llm_response()`:

**Code**:
```python
def parse_llm_response(raw_response: str) -> dict | ErrorResult:
    try:
        # Strip thinking blocks first
        cleaned = strip_thinking_blocks(raw_response)
        data = json.loads(cleaned)
        if not isinstance(data, list):
            return ErrorResult(error="Expected JSON array from LLM")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response: {e}")
        logger.error(f"Raw response: {raw_response[:500]}")
        return ErrorResult(error="Desculpe, ocorreu um erro na geração da resposta.")
```

**Reuse**: Existing `ErrorResult` and error logging pattern.

**Critical files & anchors**:

1. **`backend/src/infrastructure/llm_service.py:61-119`** - `OpenAICompatibleLLMService` class. Add temperature/thinking parameters and pass to API calls.

2. **`backend/src/config.py`** - Pydantic settings. Add `LLM_TEMPERATURE` field.

3. **`backend/src/main.py:90-110`** - Service initialization. Update `init_llm_service()` to inject temperature from config.

4. **`backend/src/application/use_cases.py:170-180`** - Response parsing. Add `strip_thinking_blocks()` helper and call it before JSON parsing.

5. **`docker-compose.yml:27-34`** - Backend environment. Add `LLM_TEMPERATURE` to environment block.

**Verification**:

1. **Verify temperature effect**:
   ```bash
   cd /home/guilherme/projects/language-learning-system/backend
   docker-compose up -d backend frontend
   curl -s -X POST http://localhost:8000/conversation/text \
     -H "Content-Type: application/json" \
     -d '{"text": "Hello, how are you?"}' | python3 -m json.tool
   ```

2. **Expected output** (should be valid JSON):
   ```json
   {
     "user_text": "Hello, how are you?",
     "ai_text": null,
     "conversation_id": "abc-123",
     "audio_base64": "..."
   }
   ```

3. **Verify no thinking blocks**:
   ```bash
   curl -s -X POST http://localhost:8000/conversation/text \
     -H "Content-Type: application/json" \
     -d '{"text": "Say hello"}' | grep -i "think\|reason\|</think>" || echo "No thinking blocks found"
   ```

4. **Integration test** - Frontend should display response:
   ```bash
   # Open browser at http://localhost:3000
   # Type message, click send, verify response appears without error
   ```

**Assumptions & contingencies**:

1. **Temperature=0.1 works**: If thinking mode persists at low temperature, the `strip_thinking_blocks()` post-processing becomes the primary fix.

2. **Post-processing always works**: The regex-based stripping is model-agnostic and works regardless of model behavior.

3. **Environment variable propagation**: If docker-compose environment variable doesn't apply, manually set `export LLM_TEMPERATURE=0.1` before docker-compose up.
