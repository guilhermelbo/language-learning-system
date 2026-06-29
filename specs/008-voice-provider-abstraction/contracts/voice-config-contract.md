# Configuration Contract: Voice Channel

**Feature**: 008-voice-provider-abstraction  
**Date**: 2026-06-29

This document defines all environment variables that control the voice channel after this refactoring. It is the authoritative reference for deployment configuration.

---

## Backend Environment Variables

These are set in `docker-compose.yml` for the `backend` service (or in `.env`).

| Variable | Required | Default | Valid values | Description |
|----------|----------|---------|-------------|-------------|
| `VOICE_ENABLED` | No | `false` | `true`, `false` | Master switch. When `false`, all voice endpoints return 503. Standard pipeline unaffected. |
| `VOICE_PROVIDER` | No | `generic` | `generic` | Selects the voice provider implementation. `generic` = self-hosted voice server. |
| `VOICE_API_URL` | No | `http://host.docker.internal:8003` | Any URL | Base URL of the external voice server. Used when `VOICE_PROVIDER=generic`. |
| `VOICE_TIMEOUT_SECONDS` | No | `30` | Integer > 0 | Per-request timeout for voice server calls. |
| `VOICE_MAX_AUDIO_SECONDS` | No | `60` | Integer > 0 | Maximum accepted audio duration. Requests exceeding this return 400. |

**Startup behaviour**: If `VOICE_PROVIDER` is set to an unrecognised value and `VOICE_ENABLED=true`, the backend fails to start with an error message naming the invalid value.

---

## External Voice Server Environment Variables

These are set when running `ai_services/omni/` standalone.

| Variable | Required | Default | Valid values | Description |
|----------|----------|---------|-------------|-------------|
| `VOICE_MODEL_BACKEND` | No | `qwen2.5-omni` | `qwen2.5-omni`, `gemma4` (stub) | Selects which model backend to load. |
| `VOICE_MODEL_DIR` | No | `/app/models/Qwen2.5-Omni-7B` | Path | Directory containing model weights for the selected backend. |

**Startup behaviour**: If `VOICE_MODEL_BACKEND` is set to an unrecognised value, the server fails to start with an error message naming the invalid value. If `VOICE_MODEL_DIR` is missing, the server starts with `model_loaded: false` and all inference requests return 503.

---

## Switching Models: Step-by-Step

### Change model (both standard and alternative backends):

```bash
# In .env (backend):
VOICE_ENABLED=true
VOICE_PROVIDER=generic
VOICE_API_URL=http://host.docker.internal:8003   # or wherever the voice server runs

# In the voice server's environment:
VOICE_MODEL_BACKEND=qwen2.5-omni    # or: gemma4 (when weights available)
VOICE_MODEL_DIR=/app/models/Qwen2.5-Omni-7B
```

Zero code changes needed.

---

## Removed Variables (breaking change — internal only)

The following `OMNI_*` variables no longer exist:

| Removed | Replaced by |
|---------|-------------|
| `OMNI_ENABLED` | `VOICE_ENABLED` |
| `OMNI_API_URL` | `VOICE_API_URL` |
| `OMNI_TIMEOUT_SECONDS` | `VOICE_TIMEOUT_SECONDS` |
| `OMNI_MAX_AUDIO_SECONDS` | `VOICE_MAX_AUDIO_SECONDS` |
| `OMNI_MODEL_DIR` (server) | `VOICE_MODEL_DIR` (server) |
