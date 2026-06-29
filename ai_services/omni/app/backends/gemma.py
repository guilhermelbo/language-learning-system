"""GemmaBackend — stub for Gemma 4 model backend.

This is a placeholder that validates the ModelBackend extensibility pattern.
It raises NotImplementedError for all inference operations until Gemma 4
weights and integration code are implemented.
"""
import numpy as np

from .base import ModelBackend


class GemmaBackend(ModelBackend):
    def load(self) -> None:
        raise NotImplementedError("Gemma 4 backend not yet implemented")

    def infer(
        self,
        audio: np.ndarray,
        sample_rate: int,
        system_prompt: str,
        context: list,
    ) -> tuple[np.ndarray, int, str]:
        raise NotImplementedError("Gemma 4 backend not yet implemented")

    def is_loaded(self) -> bool:
        return False

    def backend_name(self) -> str:
        return "gemma4"
