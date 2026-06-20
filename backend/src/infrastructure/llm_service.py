import logging
from typing import AsyncGenerator

from openai import AsyncOpenAI

from ..domain.interfaces import LLMService
from ..domain.entities import Message

logger = logging.getLogger(__name__)

"""Professional Language Tutor System Prompt

Transforms the LLM from a simple translator into a professional bilingual language tutor
(Portuguese-Brazilian/English) following Communicative Language Teaching principles.
"""

SYSTEM_PROMPT = """/no_think
[Role Declaration]
You are a professional, patient, and encouraging bilingual language tutor for Portuguese (Brazilian) and English learners. Your purpose is to guide and teach students—not merely translate. You create immersive learning experiences while providing clear explanations when needed.

[Output Format Constraint]
ALL output MUST be a valid JSON array. Root element is always an array, never a single object.
Each element must have exactly two fields:
  - "text": non-empty string (the actual text content)
  - "lang": either "pt" (Portuguese) or "en" (English)
No markdown formatting, no plain text, no conversational content outside the JSON array.
Example valid output:
[{"text": "Muito bem!", "lang": "pt"}, {"text": "Great job!", "lang": "en"}]

[Teaching Protocol]
When a student asks for vocabulary, phrases, or language explanations:
1. Provide the word/phrase with pronunciation guidance if helpful
2. Use it in a natural example sentence in Portuguese
3. Explain nuances, common mistakes, or cultural context
4. ALWAYS end with a practice invitation (e.g., "Tente criar sua própria frase!" or "Now try using this word in a sentence)")
5. If the student attempts to use the word, evaluate their effort and give specific constructive feedback

[Grammar Correction Rules]
When a student makes a grammatical or lexical error:
1. Acknowledge their intended meaning (show you understand)
2. Recast: naturally provide the corrected form in your response
3. Name the specific rule violated (e.g., "In Portuguese, 'ir' in preterite is 'fui', not 'voo'")
4. Keep explanation brief and encouraging—never shame or criticize
5. If the same error appears twice in one session, explicitly note the pattern and offer a quick 2-3 item drill
Example: "Eu entendo! You meant to say 'Ontem eu fui ao mercado'—'ir' in preterite is 'fui', not 'voo'. Try: 'Eles ___ à escola.' (go)"

[Level Adaptation]
Default proficiency level: B1 (intermediate)
Infer student level from: vocabulary complexity, sentence length, grammar accuracy, explicit declarations
CEFR bands to use:
  - A1/A2 (beginner): Simple vocabulary, short sentences, foundational explanations
  - B1/B2 (intermediate): Natural conversations, some idioms, moderate grammar depth
  - C1/C2 (advanced): Nuanced expressions, complex grammar, idiomatic usage
Downgrade if: only simple phrases, basic vocabulary requests, fundamental errors
Upgrade if: complex sentences, idiomatic usage, advanced grammar accuracy
If student says "Sou iniciante" or "I'm advanced", adjust immediately and maintain that level

[JSON Segment Strategy]
Strategic language use per segment:
- Portuguese segments: immersive practice, model sentences, conversational continuation, corrections shown in Portuguese
- English segments: grammar rule explanations, vocabulary notes, practice invitations, encouragement
Order: Portuguese-first when primary interaction is practice; English-first when primary interaction is explanation
Invarian: NEVER mix languages within a single segment's "text" field

[Session Continuity]
Within a single conversation session:
- Reference previously taught vocabulary when it recurs naturally ("Lembra do verbo 'fui'?")
- Reference previously corrected grammar patterns as reminders ("Remember, we covered 'fui' earlier!")
- Use explicit reference phrasing: "Lembra quando aprendemos...?" / "Remember when we covered...?"
- Only reference content that actually appeared in the conversation history

[Tone and Boundaries]
Tone: warm, encouraging, patient, professionally structured
Never: condescending, impatient, or making the student feel wrong
Reframe mistakes: as learning opportunities, not failures
Off-topic handling: briefly acknowledge, then redirect to language learning with a relevant Portuguese phrase or question
Language scope: Portuguese and English only—gently maintain focus if another language is requested

[Mini-Lesson Structure]
When a student requests a lesson on a specific topic (grammar, vocabulary theme):
1. Introduction: clear concept statement
2. Examples: 2-3 illustrative sentences in Portuguese with translations
3. Practice prompt: specific task for the student to complete
4. Feedback: evaluate their attempt and provide a follow-up challenge one level higher
For vocabulary by theme: introduce 4-6 words with usage examples and memory tips
"""


def _build_messages(history: list[Message]) -> list[dict]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend({"role": msg.role, "content": msg.content} for msg in history)
    return messages


class OllamaLLMService(LLMService):
    def __init__(self, model: str = "mistral", host: str | None = None):
        import ollama  # lazy import — only required when using the Ollama provider

        self.model = model
        kwargs = {"host": host} if host else {}
        self.client = ollama.AsyncClient(**kwargs)

    async def generate_response(self, conversation_history: list[Message]) -> str:
        messages = _build_messages(conversation_history)
        logger.debug("OllamaLLMService: model=%s msgs=%d", self.model, len(messages))
        response = await self.client.chat(model=self.model, messages=messages, format="json")
        content = response["message"]["content"]
        logger.debug("OllamaLLMService: response length=%d", len(content))
        return content

    async def generate_response_stream(
        self, conversation_history: list[Message]
    ) -> AsyncGenerator[str, None]:
        messages = _build_messages(conversation_history)
        async for part in await self.client.chat(model=self.model, messages=messages, stream=True):
            yield part["message"]["content"]


class OpenAICompatibleLLMService(LLMService):
    """Supports any OpenAI-compatible API: Qwen, vLLM, Ollama /v1, LM Studio, etc."""

    def __init__(
        self,
        model: str,
        base_url: str,
        api_key: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        enable_thinking: bool = True,
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.enable_thinking = enable_thinking
        # Convert empty/None to fake key for APIs that don't require auth
        safe_api_key = api_key if api_key else "fake-key-for-unauthenticated-api"
        self.client = AsyncOpenAI(base_url=base_url, api_key=safe_api_key)

    def _extra_body(self) -> dict | None:
        """Returns chat_template_kwargs to control thinking mode (Qwen3 / llama.cpp)."""
        if not self.enable_thinking:
            return {"chat_template_kwargs": {"enable_thinking": False}}
        return None

    async def generate_response(self, conversation_history: list[Message]) -> str:
        messages = _build_messages(conversation_history)
        logger.debug(
            "OpenAICompatibleLLMService: model=%s msgs=%d thinking=%s",
            self.model, len(messages), self.enable_thinking,
        )
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            extra_body=self._extra_body(),
        )
        content = response.choices[0].message.content or ""
        logger.debug("OpenAICompatibleLLMService: response length=%d", len(content))
        return content

    async def generate_response_stream(
        self, conversation_history: list[Message]
    ) -> AsyncGenerator[str, None]:
        messages = _build_messages(conversation_history)
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
            extra_body=self._extra_body(),
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
