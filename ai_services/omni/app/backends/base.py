"""ModelBackend — abstract base class for voice model backends."""
from abc import ABC, abstractmethod

import numpy as np


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
        Run inference on the given audio input.

        Returns:
            (audio_output, output_sample_rate, text_output)
            text_output may contain the <!-- PRONUNCIATION_EVENTS: --> block.
        """

    @abstractmethod
    def is_loaded(self) -> bool:
        """Return True if model weights are fully loaded."""

    @abstractmethod
    def backend_name(self) -> str:
        """Human-readable identifier for health check response."""
