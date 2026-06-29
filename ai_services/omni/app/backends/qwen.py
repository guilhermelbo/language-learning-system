"""QwenBackend — Qwen2.5-Omni-7B model backend."""
import json
import logging
import os

import numpy as np
import torch

from .base import ModelBackend

logger = logging.getLogger(__name__)

SAMPLE_RATE = 24000  # Qwen2.5-Omni audio output sample rate


class QwenBackend(ModelBackend):
    def __init__(self) -> None:
        self._model_dir = os.environ.get("VOICE_MODEL_DIR", "/app/models/Qwen2.5-Omni-7B")
        self._model = None
        self._processor = None
        self._loaded = False

    def load(self) -> None:
        if not os.path.isdir(self._model_dir):
            logger.warning(
                "Model directory not found at %s — voice service will return errors until weights are installed.",
                self._model_dir,
            )
            return
        try:
            from transformers import Qwen2_5OmniForConditionalGeneration, Qwen2_5OmniProcessor

            logger.info("Loading Qwen2.5-Omni-7B from %s ...", self._model_dir)
            self._processor = Qwen2_5OmniProcessor.from_pretrained(self._model_dir)
            self._model = Qwen2_5OmniForConditionalGeneration.from_pretrained(
                self._model_dir,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto",
            )
            self._loaded = True
            logger.info("Qwen2.5-Omni-7B loaded successfully.")
        except Exception as exc:
            logger.error("Failed to load Qwen2.5-Omni-7B: %s", exc)

    def infer(
        self,
        audio: np.ndarray,
        sample_rate: int,
        system_prompt: str,
        context: list,
    ) -> tuple[np.ndarray, int, str]:
        """
        Run Qwen2.5-Omni inference.

        Returns:
            (audio_output_array, output_sample_rate, text_output)
            text_output may contain the <!-- PRONUNCIATION_EVENTS: --> block.
        """
        if not self._loaded or self._model is None or self._processor is None:
            raise RuntimeError("Model not loaded")

        messages = [
            {"role": "system", "content": system_prompt},
        ]

        if context:
            for turn in context:
                if turn.get("role") and turn.get("content"):
                    messages.append({"role": turn["role"], "content": turn["content"]})

        messages.append({
            "role": "user",
            "content": [
                {"type": "audio", "audio": audio, "sampling_rate": sample_rate},
            ],
        })

        text_input = self._processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=False,
        )

        inputs = self._processor(
            text=text_input,
            audio=audio,
            sampling_rate=sample_rate,
            return_tensors="pt",
        ).to(self._model.device)

        with torch.no_grad():
            output_ids, audio_output = self._model.generate(
                **inputs,
                max_new_tokens=512,
                return_audio=True,
            )

        generated_ids = output_ids[:, inputs["input_ids"].shape[1]:]
        response_text = self._processor.batch_decode(
            generated_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True,
        )[0]

        if audio_output is not None and audio_output.numel() > 0:
            audio_np = audio_output[0].cpu().float().numpy()
        else:
            audio_np = np.zeros(SAMPLE_RATE, dtype=np.float32)

        return audio_np, SAMPLE_RATE, response_text

    def is_loaded(self) -> bool:
        return self._loaded

    def backend_name(self) -> str:
        return "qwen2.5-omni"
