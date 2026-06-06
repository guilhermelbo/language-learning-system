import logging
from typing import AsyncGenerator

from openai import AsyncOpenAI

from ..domain.interfaces import LLMService
from ..domain.entities import Message

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are a helpful bilingual language tutor (Portuguese/English).
Valid JSON Output is MANDATORY.
Root element must be a JSON ARRAY.

Instructions:
- If the user asks for a phrase, generate a creative one.
- If the user asks for a translation, provide the translation.
- If the user asks for the same phrase in both languages, provide two segments.

Output Format:
[
    {"text": "Portuguese text here", "lang": "pt"},
    {"text": "English text here", "lang": "en"}
]

Do not output any markdown or conversational text outside the JSON.
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
        api_key: str = "ollama",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        enable_thinking: bool = True,
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.enable_thinking = enable_thinking
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key)

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
