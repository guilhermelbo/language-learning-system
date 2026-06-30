"""
OpenAICompatibleVoiceService — native audio voice provider via llamacpp.

Pipeline:
  1. Encode user audio as base64 WAV
  2. POST {base_url}/chat/completions with input_audio content type
     (Gemma 4 processes audio natively — no STT server required)
  3. Parse USER_TRANSCRIPT and PRONUNCIATION_EVENTS from model response
  4. POST {tts_api_url}/ (Piper TTS) with clean response text
  5. Return OmniVoiceResult with audio, transcripts, and pronunciation events
"""
import base64
import json
import logging
import re
import subprocess
from typing import Optional

import httpx

from ..domain.interfaces import OmniVoiceService
from ..domain.entities import OmniVoiceResult, PronunciationEvent
from .omni_service import VoiceServiceUnavailableError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

TUTOR_SYSTEM_PROMPT = """You are a professional language tutor specialising in pronunciation coaching.

When the user speaks to you:
1. Respond naturally and helpfully in the target language.
2. Listen carefully to HOW the user pronounces words — not just WHAT they say.
3. If you detect any pronunciation errors (wrong vowels, consonants, stress, or intonation), explicitly address them in your spoken response: name the word, describe the error, and demonstrate the correct pronunciation.
4. After your spoken response, emit these two machine-readable blocks EXACTLY (even if there are no errors):

<!-- USER_TRANSCRIPT: [what you heard the student say] -->
<!-- PRONUNCIATION_EVENTS: [] -->

If there ARE pronunciation errors, populate the PRONUNCIATION_EVENTS array:
<!-- USER_TRANSCRIPT: [what you heard] -->
<!-- PRONUNCIATION_EVENTS: [{"word": "hello", "error_type": "vowel", "user_pronunciation": "hɛlo", "correct_pronunciation": "həˈloʊ"}] -->

Allowed error_type values: "vowel", "consonant", "stress", "intonation", "other"

Rules:
- The two blocks MUST always be the very last things in your text output, in that order.
- Keep your spoken response warm, encouraging, and brief.
- Correct at most 2 errors per turn to avoid overwhelming the student.
- If the pronunciation was correct, still emit both blocks (USER_TRANSCRIPT with what you heard, PRONUNCIATION_EVENTS with empty array).
"""

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


# ---------------------------------------------------------------------------
# Response parsing helpers
# ---------------------------------------------------------------------------

def _to_wav(audio: bytes) -> bytes:
    """Convert any audio format to 16kHz mono WAV using ffmpeg (pipe-based, no temp files)."""
    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", "pipe:0",
            "-ar", "16000",
            "-ac", "1",
            "-f", "wav",
            "pipe:1",
        ],
        input=audio,
        capture_output=True,
        timeout=15,
    )
    if result.returncode != 0:
        raise VoiceServiceUnavailableError(
            f"Audio conversion failed (ffmpeg exit {result.returncode}): "
            f"{result.stderr.decode(errors='replace')}"
        )
    return result.stdout


def _detect_audio_format(audio: bytes) -> str:
    """Detect audio format from magic bytes for llamacpp input_audio format field."""
    if audio[:4] == b"RIFF" and audio[8:12] == b"WAVE":
        return "wav"
    if audio[:4] == b"\x1a\x45\xdf\xa3":  # EBML magic → WebM/MKV
        return "webm"
    if audio[:4] == b"OggS":
        return "ogg"
    if audio[:3] == b"ID3" or (len(audio) >= 2 and audio[0] == 0xFF and audio[1] & 0xE0 == 0xE0):
        return "mp3"
    return "wav"  # default


def _extract_pronunciation_events(text: str) -> tuple[str, list[dict]]:
    """Split model output into (text_without_pe_block, pronunciation_events)."""
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


def _extract_user_transcript(text: str) -> str:
    """Extract content of <!-- USER_TRANSCRIPT: ... --> block, or empty string."""
    pattern = r"<!--\s*USER_TRANSCRIPT:\s*(.*?)\s*-->"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""


def _strip_user_transcript_block(text: str) -> str:
    """Remove the USER_TRANSCRIPT block from text."""
    pattern = r"\s*<!--\s*USER_TRANSCRIPT:\s*.*?\s*-->"
    return re.sub(pattern, "", text, flags=re.DOTALL).strip()


def _build_system_prompt(context: list | None) -> str:
    """Build system prompt with optional DRILL_CONTEXT_PROMPT addendum for open corrections."""
    system_content = TUTOR_SYSTEM_PROMPT
    if context:
        open_corrections = [
            c for c in context
            if "role" not in c and not c.get("correction_attempted", True)
        ]
        if open_corrections:
            corrections_text = json.dumps(open_corrections, ensure_ascii=False)
            system_content += DRILL_CONTEXT_PROMPT.format(open_corrections=corrections_text)
    return system_content


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class OpenAICompatibleVoiceService(OmniVoiceService):
    """
    Voice provider using llamacpp native audio input via chat completions.

    Gemma 4 (with mmproj loaded) processes WAV audio directly without a
    separate STT server. Text response is synthesized by Piper TTS.
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: Optional[str],
        tts_api_url: str,
        timeout: int = 30,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._tts_api_url = tts_api_url.rstrip("/")
        self._timeout = timeout

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    @staticmethod
    def _map_language(language: str) -> str:
        """Map language tag to Piper TTS lang code."""
        lang = language.lower()
        if lang.startswith("pt"):
            return "pt"
        return "en"

    async def _call_llm(
        self,
        audio: bytes,
        language: str,
        context: list | None,
    ) -> str:
        """Send audio to LLM via input_audio content type, return raw response text."""
        audio_format = _detect_audio_format(audio)
        if audio_format != "wav":
            logger.debug("Converting %s audio to WAV before LLM call", audio_format)
            audio = _to_wav(audio)
            audio_format = "wav"
        audio_b64 = base64.b64encode(audio).decode("utf-8")

        # Separate conversation history from correction dicts
        message_context = [c for c in (context or []) if "role" in c]

        system_prompt = _build_system_prompt(context)

        messages: list[dict] = [{"role": "system", "content": system_prompt}]

        # Add prior turns as text messages
        for turn in message_context:
            messages.append({"role": turn["role"], "content": turn["content"]})

        # Current user turn: multimodal with audio + text instruction
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "input_audio",
                    "input_audio": {
                        "data": audio_b64,
                        "format": audio_format,
                    },
                },
                {
                    "type": "text",
                    "text": "Please respond as the language tutor to what you hear in the audio.",
                },
            ],
        })

        payload = {
            "model": self._model or "gemma4",
            "messages": messages,
            "max_tokens": 512,
            "chat_template_kwargs": {"enable_thinking": False},
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    json=payload,
                    headers=self._headers(),
                )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.error("LLM service unreachable: %s", exc)
            raise VoiceServiceUnavailableError(str(exc)) from exc

        if not response.is_success:
            raise VoiceServiceUnavailableError(
                f"LLM error {response.status_code}: {response.text}"
            )

        data = response.json()
        content = data["choices"][0]["message"].get("content") or ""
        if not content:
            raise VoiceServiceUnavailableError(
                "LLM returned empty content — response may have been truncated by max_tokens "
                "(thinking mode generates reasoning_content before content)"
            )

        return content

    async def _synthesize(self, text: str, language: str) -> bytes:
        """Convert text to audio via Piper TTS. Returns empty bytes on failure (degraded mode)."""
        lang = self._map_language(language)
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._tts_api_url}/synthesize",
                    json={"text": text},
                    params={"lang": lang},
                )
            if response.is_success:
                return response.content
            logger.warning("TTS error %s: %s", response.status_code, response.text)
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.warning("TTS service unreachable: %s", exc)
        except Exception as exc:
            logger.warning("TTS unexpected error: %s", exc)
        return b""

    async def process_speech(
        self,
        audio: bytes,
        language: str = "en-US",
        context: list | None = None,
    ) -> OmniVoiceResult:
        # 1. Send audio to LLM
        raw_text = await self._call_llm(audio, language, context)

        # 2. Extract transcript of what the model heard
        transcript_user = _extract_user_transcript(raw_text)

        # 3. Extract pronunciation events and strip their block
        text_without_pe, raw_events = _extract_pronunciation_events(raw_text)

        # 4. Strip USER_TRANSCRIPT block from clean text
        clean_text = _strip_user_transcript_block(text_without_pe)

        # 5. Convert raw event dicts to domain entities
        pronunciation_events = [
            PronunciationEvent(
                word=ev.get("word", ""),
                error_type=ev.get("error_type", "other"),
                user_pronunciation=ev.get("user_pronunciation", ""),
                correct_pronunciation=ev.get("correct_pronunciation", ""),
                correction_attempted=ev.get("correction_attempted", False),
                correction_succeeded=ev.get("correction_succeeded", None),
            )
            for ev in raw_events
            if ev.get("word")
        ]

        # 6. Synthesize speech
        audio_bytes = await self._synthesize(clean_text, language)

        return OmniVoiceResult(
            audio_bytes=audio_bytes,
            transcript_user=transcript_user,
            transcript_assistant=clean_text,
            pronunciation_events=pronunciation_events,
        )

    async def health_check(self) -> dict:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{self._base_url}/health",
                    headers=self._headers(),
                )
            if response.is_success:
                data = response.json()
                return {"status": "ok", "model_loaded": data.get("model_loaded", True)}
        except Exception:
            pass
        return {"status": "unreachable", "model_loaded": False}
