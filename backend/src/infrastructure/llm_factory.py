from ..config import Settings
from ..domain.interfaces import LLMService
from .llm_service import OllamaLLMService, OpenAICompatibleLLMService


def create_llm_service(settings: Settings) -> LLMService:
    """Instantiate the correct LLM backend from settings.

    LLM_PROVIDER=ollama           → OllamaLLMService (native Ollama client)
    LLM_PROVIDER=openai_compatible → OpenAICompatibleLLMService (any /v1 endpoint)
    """
    provider = settings.llm_provider.lower()

    if provider == "openai_compatible":
        return OpenAICompatibleLLMService(
            model=settings.llm_model_name,
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            enable_thinking=settings.llm_enable_thinking,
        )

    if provider == "ollama":
        return OllamaLLMService(
            model=settings.llm_model_name,
            host=settings.ollama_host if settings.ollama_host != "http://localhost:11434" else None,
        )

    raise ValueError(
        f"Unknown LLM_PROVIDER '{settings.llm_provider}'. "
        "Supported values: 'ollama', 'openai_compatible'."
    )
