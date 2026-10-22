"""Model-backed abstractive summarization service."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
MAX_INPUT_TOKENS = 1024
MAX_INPUT_CHARACTERS = 80_000
SUPPORTED_LENGTHS = {"short", "medium", "long"}

_GENERATION_SETTINGS = {
    "short": {"min_new_tokens": 20, "max_new_tokens": 70},
    "medium": {"min_new_tokens": 35, "max_new_tokens": 120},
    "long": {"min_new_tokens": 50, "max_new_tokens": 180},
}


class SummarizationError(Exception):
    """A user-facing summarization failure."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code


@dataclass
class SummaryResult:
    summary: str
    truncated_input: bool = False


def normalize_text(text: str) -> str:
    return re.sub(r"[ \t\r\n]+", " ", text).strip()


class SummarizerService:
    def __init__(self, load_on_init: bool = True):
        self.tokenizer: Any = None
        self.model: Any = None
        self.initialization_error: str | None = None
        if load_on_init:
            self._initialize()

    @property
    def is_ready(self) -> bool:
        return self.tokenizer is not None and self.model is not None

    def _initialize(self) -> None:
        try:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

            self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
            self.model.eval()
            self.initialization_error = None
        except Exception as exc:
            self.tokenizer = None
            self.model = None
            self.initialization_error = (
                "The summarization model could not be loaded. "
                "Check your internet connection and run the setup steps in README.md. "
                f"Details: {exc}"
            )

    def _ensure_initialized(self) -> None:
        if not self.is_ready:
            self._initialize()
        if not self.is_ready:
            raise SummarizationError(self.initialization_error or "The model is unavailable.")

    def generate_summary(self, text: str, summary_length: str) -> SummaryResult:
        if summary_length not in SUPPORTED_LENGTHS:
            raise SummarizationError("Choose a short, medium, or long summary.", 400)
        if len(text) > MAX_INPUT_CHARACTERS:
            raise SummarizationError(
                f"Input is too long. Please keep it under {MAX_INPUT_CHARACTERS:,} characters.",
                413,
            )
        if len(text.split()) < 20:
            raise SummarizationError(
                "Please provide at least 20 words for a meaningful summary.", 422
            )

        self._ensure_initialized()
        import torch

        encoded = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=MAX_INPUT_TOKENS,
        )
        settings = _GENERATION_SETTINGS[summary_length]
        # Keep the lower bound valid even for models with an unusual tokenizer.
        minimum = min(settings["min_new_tokens"], settings["max_new_tokens"] - 1)
        with torch.no_grad():
            output = self.model.generate(
                **encoded,
                min_new_tokens=minimum,
                max_new_tokens=settings["max_new_tokens"],
                num_beams=4,
                early_stopping=True,
                no_repeat_ngram_size=3,
            )
        summary = self.tokenizer.decode(output[0], skip_special_tokens=True).strip()
        if not summary:
            raise SummarizationError("The model returned an empty summary. Please try again.")
        token_count = int(encoded["input_ids"].shape[-1])
        return SummaryResult(summary=summary, truncated_input=token_count >= MAX_INPUT_TOKENS)
