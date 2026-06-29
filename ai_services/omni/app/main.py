"""
Voice model server — speech-to-speech inference with pluggable backends.

Accepts raw audio input (WebM/WAV), routes it to the selected ModelBackend,
and returns:
  - audio_base64: spoken response (WAV, backend-determined sample rate)
  - transcript_user: model-inferred transcription of user speech
  - transcript_assistant: text of assistant response
  - pronunciation_events: structured list of detected pronunciation issues

The active backend is selected via VOICE_MODEL_BACKEND environment variable.
"""

import base64
import io
import json
import logging
import os
import re
import tempfile
from contextlib import asynccontextmanager
from typing import Optional

import numpy as np
import soundfile as sf
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from .backends.qwen import QwenBackend
from .backends.gemma import GemmaBackend

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Backend registry — add new entries here to support additional models.
# Each value is a zero-argument factory that returns a ModelBackend instance.
# ---------------------------------------------------------------------------
_BACKENDS = {
    "qwen2.5-omni": QwenBackend,
    "gemma4": GemmaBackend,
}

VOICE_MODEL_BACKEND = os.environ.get("VOICE_MODEL_BACKEND", "qwen2.5-omni")

if VOICE_MODEL_BACKEND not in _BACKENDS:
    raise ValueError(
        f"Unknown VOICE_MODEL_BACKEND '{VOICE_MODEL_BACKEND}'. "
        f"Supported values: {sorted(_BACKENDS.keys())}."
    )

backend = _BACKENDS[VOICE_MODEL_BACKEND]()

# ---------------------------------------------------------------------------
# System prompt — instructs the model to act as a pronunciation-aware tutor
# and emit structured pronunciation metadata in a parseable comment block.
# ---------------------------------------------------------------------------
TUTOR_SYSTEM_PROMPT = """You are a professional language tutor specialising in pronunciation coaching.

When the user speaks to you:
1. Respond naturally and helpfully in the target language.
2. Listen carefully to HOW the user pronounces words — not just WHAT they say.
3. If you detect any pronunciation errors (wrong vowels, consonants, stress, or intonation), explicitly address them in your spoken response: name the word, describe the error, and demonstrate the correct pronunciation.
4. After your spoken response, emit a machine-readable block EXACTLY like this (even if there are no errors):

<!-- PRONUNCIATION_EVENTS: [] -->

If there ARE errors, populate the array with objects in this exact format:
<!-- PRONUNCIATION_EVENTS: [{"word": "hello", "error_type": "vowel", "user_pronunciation": "hɛlo", "correct_pronunciation": "həˈloʊ"}] -->

Allowed error_type values: "vowel", "consonant", "stress", "intonation", "other"

Rules:
- The PRONUNCIATION_EVENTS block MUST always be the very last thing in your text output.
- Keep your spoken response warm, encouraging, and brief.
- Correct at most 2 errors per turn to avoid overwhelming the student.
- If the pronunciation was correct, still emit the block with an empty array.
"""

# Drill context addendum — injected when a prior turn has open corrections
DRILL_CONTEXT_PROMPT = """
Additionally, the previous turn had unresolved pronunciation corrections:
{open_corrections}

Listen specifically for whether the user has improved on these words. If they have:
- Confirm their success warmly ("Much better! Your pronunciation of '{word}' is correct now.")
- Set correction_attempted to true and correction_succeeded to true in the PRONUNCIATION_EVENTS block.
If still incorrect after a second attempt:
- Offer one final specific tip, then move on naturally.
- Set correction_attempted to true and correction_succeeded to false.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        backend.load()
    except NotImplementedError as exc:
        logger.warning("Backend load skipped (stub): %s", exc)
    except Exception as exc:
        logger.error("Backend load failed: %s", exc)
    yield


app = FastAPI(title="Voice Model Server", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Audio helpers
# ---------------------------------------------------------------------------

def _audio_bytes_to_array(raw: bytes) -> tuple[np.ndarray, int]:
    """Convert raw audio bytes (WebM/WAV/etc.) to numpy float32 array + sample rate."""
    with tempfile.NamedTemporaryFile(suffix=".audio", delete=False) as tmp:
        tmp.write(raw)
        tmp_path = tmp.name
    try:
        import librosa
        audio, sr = librosa.load(tmp_path, sr=16000, mono=True)
    finally:
        os.unlink(tmp_path)
    return audio, sr


def _array_to_wav_bytes(audio: np.ndarray, sample_rate: int) -> bytes:
    """Encode float32 numpy array to WAV bytes."""
    buf = io.BytesIO()
    sf.write(buf, audio, sample_rate, format="WAV", subtype="PCM_16")
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# Pronunciation event extraction (part of the API contract, not model-specific)
# ---------------------------------------------------------------------------

def _extract_pronunciation_events(text: str) -> tuple[str, list[dict]]:
    """
    Split model text output into (clean_text, pronunciation_events).
    The model is instructed to end its text with:
        <!-- PRONUNCIATION_EVENTS: [...] -->
    """
    pattern = r"<!--\s*PRONUNCIATION_EVENTS:\s*(\[.*?\])\s*-->"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        return text.strip(), []

    clean_text = text[: match.start()].strip()
    try:
        events = json.loads(match.group(1))
        if not isinstance(events, list):
            events = []
    except json.JSONDecodeError:
        events = []

    return clean_text, events


def _build_system_prompt(context: list | None) -> str:
    """Build the full system prompt, optionally injecting drill context."""
    system_content = TUTOR_SYSTEM_PROMPT
    if context:
        open_corrections = [
            c for c in context
            if not c.get("correction_attempted", True)
        ]
        if open_corrections:
            corrections_text = json.dumps(open_corrections, ensure_ascii=False)
            system_content += DRILL_CONTEXT_PROMPT.format(open_corrections=corrections_text)
    return system_content


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model_loaded": backend.is_loaded(),
        "backend": backend.backend_name(),
    }


@app.post("/omni/speech")
async def omni_speech(
    file: UploadFile = File(...),
    language: str = Form(default="en-US"),
    context: Optional[str] = Form(default=None),
):
    if not backend.is_loaded():
        raise HTTPException(
            status_code=503,
            detail=f"Model not loaded. Ensure weights are present and restart the service.",
        )

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file received.")

    context_list: list | None = None
    if context:
        try:
            context_list = json.loads(context)
        except json.JSONDecodeError:
            context_list = None

    try:
        audio_array, sample_rate = _audio_bytes_to_array(audio_bytes)
    except Exception as exc:
        logger.error("Audio decoding failed: %s", exc)
        raise HTTPException(status_code=400, detail=f"Audio decoding failed: {exc}")

    system_prompt = _build_system_prompt(context_list)

    try:
        audio_output, output_sample_rate, response_text = backend.infer(
            audio=audio_array,
            sample_rate=sample_rate,
            system_prompt=system_prompt,
            context=context_list or [],
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.error("Inference failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Inference error: {exc}")

    clean_text, pronunciation_events = _extract_pronunciation_events(response_text)
    response_audio = _array_to_wav_bytes(audio_output, output_sample_rate)

    # The model infers user transcript from context — approximated here
    transcript_user = "[audio input]"

    return JSONResponse({
        "audio_base64": base64.b64encode(response_audio).decode("utf-8"),
        "transcript_user": transcript_user,
        "transcript_assistant": clean_text,
        "pronunciation_events": pronunciation_events,
    })
