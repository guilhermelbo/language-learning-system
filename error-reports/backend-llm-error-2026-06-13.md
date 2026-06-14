# Backend LLM Generation Error

**Date**: 2026-06-13  
**Time**: 20:10 UTC  
**Severity**: HIGH - Core functionality blocked

## Problem Summary

The backend API endpoint `/conversation/text` returns an error message instead of a valid JSON response with bilingual conversation segments.

## Error Response

```json
{
  "user_text": "Hello, how are you?",
  "ai_text": "Desculpe, ocorreu um erro na geração da resposta.",
  "conversation_id": "672df35a-1448-47be-a78a-0a9054ca70f3",
  "audio_base64": "UklGRpgSAgBXQVZFZm10IBAAAAABAAEAIlYAAESsAAACABAAZGF0YXQSAgAEAP7/AAAEAPn/AQD1////+/8AAP//AA..."
}
```

## Root Cause Analysis

### Primary Issue: Qwen Model Thinking Mode Activation

The Qwen3.5-35B-A3B-UD-IQ3_S.gguf model is activating its built-in **thinking/reasoning mode**, which returns structured reasoning content before the final answer. This violates the strict JSON array format expected by the backend.

**Qwen Thinking Mode Output Pattern:**
```
</think>

[thinking content with internal reasoning...]

</think>

{"text": "Hello", "lang": "en"}
```

The backend parser receives the `</think>` token and reasoning content, causing a `JSONDecodeError`.

### Supporting Evidence

1. **Backend logs** show connection errors when trying to reach LLM
2. **Model is loaded** at `http://localhost:8080/v1/models` - confirms LLM is accessible
3. **LLM_BASE_URL** correctly set to `http://host.docker.internal:8080/v1`
4. **Backend receives response** but cannot parse it as valid JSON

## Environment Status

| Component | Status | Details |
|---|---|---|
| Backend Container | ✅ Running | Port 8000 mapped |
| Frontend Container | ✅ Running | Port 3000 mapped |
| STT Service | ✅ Running | Port 8001 mapped |
| TTS Service | ✅ Running | Port 8002 mapped |
| LLM (llamacpp) | ✅ Running | Port 8080, model loaded |
| Network | ✅ Bridge | All containers in `language-learning-system_default` |

## Technical Details

### Backend Infrastructure Layer

**File**: `backend/src/infrastructure/llm_service.py`

The OpenAI-compatible client (used for Qwen) makes requests without disabling thinking mode:

```python
async def generate_response(self, conversation_history: list[Message]) -> str:
    response = await self.client.chat.completions.create(
        model=self.model_name,
        messages=self._format_messages(conversation_history),
        temperature=self.temperature
        # Missing: disable_thinking parameter
    )
    return response.choices[0].message.content
```

**Failure Point**: The response parsing in `application/use_cases.py`:

```python
try:
    data = json.loads(raw_response)
except json.JSONDecodeError as e:
    logger.error(f"Failed to parse LLM response: {e}")
    return ErrorResult(error="Desculpe, ocorreu um erro na geração da resposta.")
```

### Model Configuration

**Environment Variable**: `LLM_MODEL_NAME=Qwen3.5-35B-A3B-UD-IQ3_S.gguf`

The model is a quantized GGUF format model designed for llama.cpp inference server. Qwen models (especially 3.5 variants) have built-in reasoning capabilities that activate by default.

## Solution: Disable Thinking Mode via API

### Approach: Configuration Parameter (Preferred)

Since the llama.cpp container is shared infrastructure that must support thinking mode for other use cases, the application should disable thinking mode via the OpenAI-compatible API parameters.

**Implementation:** Add `disable_thinking` parameter to the chat completion request:

```python
async def generate_response(self, conversation_history: list[Message]) -> str:
    response = await self.client.chat.completions.create(
        model=self.model_name,
        messages=self._format_messages(conversation_history),
        temperature=self.temperature,
        # Disable thinking mode for JSON output
        extra_headers={"x-stripe-api-version": "2024-12-15"},  # placeholder
        thinking={"type": "disabled"}  # OpenAI-compatible thinking control
    )
    return response.choices[0].message.content
```

### Alternative: Temperature Adjustment

As a fallback, reduce temperature to minimize reasoning behavior:

```python
temperature=0.1  # Lower temperature reduces creative reasoning
```

### Alternative: Enhanced System Prompt

Modify the system prompt to explicitly forbid thinking:

```python
SYSTEM_PROMPT = """
You are a helpful bilingual language tutor (Portuguese/English).
Valid JSON Output is MANDATORY. DO NOT THINK, DO NOT REASON, DO NOT OUTPUT ANY ANALYSIS.
Only output a JSON array. No markdown, no thinking blocks, no explanations.
"""
```

## Solution Options

### Option 1: API Parameter Control (Recommended)

Add OpenAI-compatible `thinking` parameter to disable reasoning mode:

```python
# In OpenAICompatibleLLMService.generate_response()
response = await self.client.chat.completions.create(
    model=self.model_name,
    messages=self._format_messages(conversation_history),
    temperature=self.temperature,
    thinking={"type": "disabled"}  # or {"enabled": false}
)
```

**Pros:** Clean separation of concerns, model-agnostic configuration  
**Cons:** May not work with all llama.cpp versions

### Option 2: Temperature Reduction

Set low temperature to minimize thinking:

```python
temperature = 0.1  # Reduce from default (likely 0.7-0.8)
```

**Pros:** Works universally, no API changes  
**Cons:** May reduce response quality, not a true "disable"

### Option 3: Response Post-Processing

Strip thinking blocks from response before JSON parsing:

```python
import re

def strip_thinking(response: str) -> str:
    # Remove </thinking>... </thinking> or <think>...</think> blocks
    response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
    response = re.sub(r'</think>.*?</think>', '', response, flags=re.DOTALL)
    return response
```

**Pros:** Works regardless of model behavior  
**Cons:** Fragile, adds processing overhead

## Implementation Plan

### Phase 1: Diagnose Thinking Mode

1. **Test raw API output:**
   ```bash
   curl -X POST http://localhost:8080/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{
       "model": "Qwen3.5-35B-A3B-UD-IQ3_S.gguf",
       "messages": [{"role": "user", "content": "Say hello"}],
       "temperature": 0.7
     }' | jq -r '.choices[0].message.content'
   ```

2. **Verify thinking blocks present:**
   - Look for `</think>`, `<thinking>`, or reasoning content
   - Check if JSON appears after reasoning

3. **Test with temperature=0.1:**
   ```bash
   curl -X POST ... "temperature": 0.1
   ```

### Phase 2: Implement Solution

1. **Add configuration parameter:**
   ```python
   # In backend/src/infrastructure/llm_service.py
   class OpenAICompatibleLLMService:
       def __init__(self, model: str = "Qwen3.5-35B-A3B-UD-IQ3_S.gguf", 
                    host: str = None, temperature: float = 0.1):
           # Add temperature parameter with lower default
   ```

2. **Pass parameters to API call:**
   ```python
   response = await self.client.chat.completions.create(
       model=self.model_name,
       messages=messages,
       temperature=self.temperature
   )
   ```

3. **Add post-processing as fallback:**
   ```python
   def parse_llm_response(raw_response: str) -> dict | ErrorResult:
       # Strip thinking blocks first
       cleaned = strip_thinking_blocks(raw_response)
       return json.loads(cleaned)
   ```

## Testing Required

1. **Verify JSON output without thinking:**
   ```bash
   curl -X POST http://localhost:8080/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"messages":[{"role":"user","content":"Say hello"}], "temperature": 0.1}'
   ```

2. **Test parsing in Python:**
   ```python
   import json
   json.loads(response)  # Should not raise JSONDecodeError
   ```

3. **Full flow test:**
   ```bash
   curl -X POST http://localhost:8000/conversation/text \
     -H "Content-Type: application/json" \
     -d '{"text": "Hello, how are you?"}'
   ```

4. **Verify JSON structure:**
   ```python
   response = json.loads(raw)
   assert isinstance(response, list)
   assert all("text" in item and "lang" in item for item in response)
   ```

## Related Files

- `backend/src/infrastructure/llm_service.py` - LLM client implementation
- `backend/src/application/use_cases.py` - Response parsing logic
- `backend/src/main.py` - API endpoint definition
- `docker-compose.yml` - Service configuration (no changes needed)
- `backend/src/config.py` - Configuration management

## Notes

- **Infrastructure constraint**: llama.cpp container is shared infrastructure; cannot modify its configuration
- **Model agnostic**: Solution must work with any OpenAI-compatible LLM provider
- **User-friendly error**: "Desculpe, ocorreu um erro na geração da resposta" should be hidden once JSON parsing works
- **Audio still generated**: Empty WAV file created even on LLM failure (graceful degradation)
- **No persistence**: Conversation IDs generated but conversations not persisted (in-memory only)

## Next Steps

1. Test raw API output with current temperature setting
2. Implement temperature reduction as immediate fix
3. Add thinking mode detection as diagnostic
4. Document configuration parameters in `.env` template
