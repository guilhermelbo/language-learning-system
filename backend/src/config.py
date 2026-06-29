from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pydantic import field_validator



class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM provider: "ollama" | "openai_compatible"
    llm_provider: str = Field(default="ollama", alias="LLM_PROVIDER")

    # Model name used by any provider
    llm_model_name: str = Field(default="mistral", alias="LLM_MODEL_NAME")

    # OpenAI-compatible settings (Qwen, vLLM, Ollama /v1, etc.)
    llm_base_url: str = Field(default="http://llamacpp:8080/v1", alias="LLM_BASE_URL")
    llm_api_key: str | None = Field(default=None, alias="LLM_API_KEY")
    llm_temperature: float = Field(default=0.1, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=1024, alias="LLM_MAX_TOKENS")
    llm_enable_thinking: bool = Field(default=False, alias="LLM_ENABLE_THINKING")
    @field_validator("llm_api_key", mode="before")
    @classmethod
    def empty_to_none(cls, v):
        """Convert empty strings to None for API keys."""
        if v == "":
            return None
        return v

    # Ollama-specific
    ollama_host: str = Field(default="http://localhost:11434", alias="OLLAMA_HOST")

    # Standard services
    stt_api_url: str = Field(default="http://stt:8001", alias="STT_API_URL")
    tts_api_url: str = Field(default="http://tts:8002", alias="TTS_API_URL")
    piper_model_path: str = Field(
        default="pt_BR-faber-medium.onnx", alias="PIPER_MODEL_PATH"
    )

    # Voice channel (speech-to-speech tutoring)
    voice_enabled: bool = Field(default=False, alias="VOICE_ENABLED")
    voice_provider: str = Field(default="generic", alias="VOICE_PROVIDER")
    voice_api_url: str = Field(default="http://host.docker.internal:8003", alias="VOICE_API_URL")
    voice_timeout_seconds: int = Field(default=30, alias="VOICE_TIMEOUT_SECONDS")
    voice_max_audio_seconds: int = Field(default=60, alias="VOICE_MAX_AUDIO_SECONDS")


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
