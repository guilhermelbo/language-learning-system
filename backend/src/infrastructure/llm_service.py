"""
LLM service implementation using Ollama.

Handles communication with the Ollama API for generating responses.
"""

import ollama
import logging
from typing import AsyncGenerator
from ..domain.interfaces import LLMService
from ..domain.entities import Message

logger = logging.getLogger(__name__)


class OllamaLLMService(LLMService):
    """
    LLM service using Ollama as the backend.

    The system prompt focuses on content quality rather than strict JSON formatting.
    The response extractor handles parsing of various output formats.
    """

    def __init__(self, model: str = "mistral"):
        self.model = model
        self.client = ollama.AsyncClient()

    def _convert_history(self, history: list[Message]) -> list[dict]:
        """
        Convert conversation history to Ollama message format.

        The system prompt is designed to encourage bilingual responses
        without strict JSON formatting requirements. The extractor
        layer handles parsing of varied output formats.
        """
        system_prompt = """You are a helpful bilingual language tutor helping users learn English from Portuguese.

When responding:
- Provide your response in both Portuguese and English
- First give the Portuguese version, then the English version
- Keep responses natural and conversational
- Be encouraging and helpful

Output your response as a JSON array with segments:
[
    {"text": "Portuguese response here", "lang": "pt"},
    {"text": "English response here", "lang": "en"}
]

If the user asks a question, answer it in both languages.
If the user wants a phrase or expression, provide it in both languages.
If the user wants just a translation, provide the translation."""

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend([{"role": msg.role, "content": msg.content} for msg in history])
        return messages

    async def generate_response(self, conversation_history: list[Message]) -> str:
        """
        Generate a response from the LLM.

        Args:
            conversation_history: List of messages in the conversation

        Returns:
            Raw string response from the LLM
        """
        messages = self._convert_history(conversation_history)
        logger.debug(f"Generating response with model {self.model} for {len(messages)} messages")

        response = await self.client.chat(model=self.model, messages=messages, format="json")
        content = response['message']['content']

        logger.info(f"LLM raw response: {content[:200]}..." if len(content) > 200 else f"LLM raw response: {content}")
        logger.debug(f"LLM Response length: {len(content)}")

        return content

    async def generate_response_stream(self, conversation_history: list[Message]) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response from the LLM.

        Args:
            conversation_history: List of messages in the conversation

        Yields:
            String chunks of the response
        """
        messages = self._convert_history(conversation_history)
        async for part in await self.client.chat(model=self.model, messages=messages, stream=True):
            yield part['message']['content']
