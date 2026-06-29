# Research: Voice Provider Abstraction

**Feature**: 008-voice-provider-abstraction  
**Date**: 2026-06-29  
**Status**: Complete — all decisions resolved by direct inspection of the existing codebase

---

## 1. Exact Coupling Points in the Current Code

**Decision**: All coupling is cosmetic or structural within the backend — no domain logic needs to change.

**Findings from code inspection**:

| File | Line(s) | Coupling |
|------|---------|---------|
| `backend/src/config.py` | 45–48 | 4 fields prefixed `omni_*`; no `voice_provider` field |
| `backend/src/infrastructure/omni_service.py` | class name | `QwenOmniHttpService` names the model; `OmniServiceUnavailableError` names the channel |
| `backend/src/main.py` | 15, 43–48 | Imports and instantiates `QwenOmniHttpService` directly; checks `settings.omni_enabled` |
| `backend/src/main.py` | 161, 166, 195–207 | References `omni_enabled`, `omni_max_audio_seconds`, `omni_api_url` |
| `docker-compose.yml` | 37–40 | `OMNI_ENABLED`, `OMNI_API_URL` env vars |
| `.env.example` | 27–30 | Same `OMNI_*` vars |
| `ai_services/omni/app/main.py` | 31–32 | `MODEL_DIR` env var is `OMNI_MODEL_DIR`; no `VOICE_MODEL_BACKEND` |
| `ai_services/omni/app/main.py` | 92–96 | Imports `Qwen2_5OmniForConditionalGeneration`, `Qwen2_5OmniProcessor` directly in `_load_model()` |
| `ai_services/omni/app/main.py` | 269 | Endpoint is `/omni/speech` (harmless but Qwen-named) |

**What does NOT need to change**:
- `backend/src/domain/interfaces.py` — `OmniVoiceService` ABC is already generic
- `backend/src/domain/entities.py` — all entities are generic
- `backend/src/application/use_cases.py` — `ProcessOmniVoiceUseCase` accepts interface only
- All frontend files — zero changes needed
- All API endpoint paths — preserved for backward compatibility

---

## 2. LLM Factory Pattern to Mirror

**Decision**: Mirror `llm_factory.py` exactly — same structure, same error message format, same validation approach.

**Pattern from `backend/src/infrastructure/llm_factory.py`**:
```
create_llm_service(settings) → LLMService
  - reads settings.llm_provider
  - maps to concrete class
  - raises ValueError with descriptive message on unknown provider
```

New factory: `backend/src/infrastructure/voice_factory.py`
```
create_voice_service(settings) → OmniVoiceService
  - reads settings.voice_provider
  - maps "generic" → GenericVoiceHttpService
  - raises ValueError on unknown provider
```

`main.py` calls `create_voice_service(settings)` the same way it calls `create_llm_service(settings)`.

---

## 3. Config Rename Strategy

**Decision**: Full rename `OMNI_*` → `VOICE_*`. No backward-compat aliases needed (internal system, no external consumers).

| Old | New |
|-----|-----|
| `OMNI_ENABLED` | `VOICE_ENABLED` |
| `OMNI_API_URL` | `VOICE_API_URL` |
| `OMNI_TIMEOUT_SECONDS` | `VOICE_TIMEOUT_SECONDS` |
| `OMNI_MAX_AUDIO_SECONDS` | `VOICE_MAX_AUDIO_SECONDS` |
| (new) | `VOICE_PROVIDER` (default: `"generic"`) |
| `OMNI_MODEL_DIR` (server) | `VOICE_MODEL_DIR` (server, default: `/app/models`) |
| (new, server) | `VOICE_MODEL_BACKEND` (default: `"qwen2.5-omni"`) |

---

## 4. External Server Backend Extraction

**Decision**: Extract Qwen inference code from `ai_services/omni/app/main.py` into `ai_services/omni/app/backends/qwen.py`. Add a `ModelBackend` ABC. Add a stub `ai_services/omni/app/backends/gemma.py`. The HTTP layer and pronunciation event extraction stay in `main.py` (they are part of the API contract, not model-specific).

**Interface for each backend**:
```python
class ModelBackend(ABC):
    @abstractmethod
    def load(self) -> None:
        """Load model weights. Called once at startup."""

    @abstractmethod
    def infer(
        self,
        audio: np.ndarray,
        sample_rate: int,
        system_prompt: str,
        context: list,
    ) -> tuple[np.ndarray, int, str]:
        """
        Run inference.
        Returns: (audio_output_array, output_sample_rate, text_output)
        text_output may contain the <!-- PRONUNCIATION_EVENTS: --> block.
        """

    @abstractmethod
    def is_loaded(self) -> bool:
        """Return True if model weights are fully loaded."""
    
    @abstractmethod
    def backend_name(self) -> str:
        """Human-readable name for health check response."""
```

**Registry in main.py**:
```python
_BACKENDS = {
    "qwen2.5-omni": "app.backends.qwen.QwenBackend",
    "gemma4": "app.backends.gemma.GemmaBackend",
}
```

**Health endpoint change**: add `"backend"` field to response:
```json
{ "status": "ok", "model_loaded": true, "backend": "qwen2.5-omni" }
```

---

## 5. Endpoint Rename Decision

**Decision**: Keep `/omni/speech` path in the external server's HTTP API (the backend client calls this path). The endpoint name is part of the internal contract between backend and voice server — renaming it would require updating `GenericVoiceHttpService` and gain nothing. Rename deferred to a future cleanup if desired.

**Rationale**: The spec requires zero changes to public API paths. The `/omni/speech` path is internal (backend → voice server). Changing it would add risk for no user-visible benefit.

---

## 6. Test File Updates

**Decision**: Update `backend/tests/test_omni_service.py` to use new class names (`GenericVoiceHttpService`, `VoiceServiceUnavailableError`). `backend/tests/test_omni_use_case.py` needs no changes — it mocks the interface.

---

## 7. Gemma 4 Stub Scope

**Decision**: `ai_services/omni/app/backends/gemma.py` is a minimal stub that raises `NotImplementedError` in `load()` and `infer()` but implements the interface correctly. This validates the extensibility pattern without shipping incomplete inference code. The `is_loaded()` method returns `False`.
