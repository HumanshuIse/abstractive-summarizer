"""Flask application for the abstractive summarization demo."""

from __future__ import annotations

import os
import time
from typing import Any

from flask import Flask, jsonify, render_template, request

from summarizer import (
    MODEL_NAME,
    SUPPORTED_LENGTHS,
    SummarizationError,
    SummarizerService,
    normalize_text,
)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100_000

# Tests opt out of startup loading. In normal use the model is initialized once
# when the application starts; the service still exposes lazy initialization
# for environments where startup downloads are undesirable.
summarizer_service = SummarizerService(
    load_on_init=os.getenv("SUMMARIZER_LOAD_ON_STARTUP", "1") != "0"
)


def _word_count(text: str) -> int:
    return len(text.split())


def _error(message: str, status: int):
    return jsonify({"success": False, "error": message}), status


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return jsonify(
        {
            "success": True,
            "status": "ready" if summarizer_service.is_ready else "not_ready",
            "model": MODEL_NAME,
            "model_error": summarizer_service.initialization_error,
        }
    )


@app.post("/api/summarize")
def summarize():
    if not request.is_json:
        return _error("Request must use the application/json content type.", 415)

    payload: Any = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error("Request body must be a valid JSON object.", 400)

    raw_text = payload.get("text")
    length = payload.get("summary_length", "medium")
    if not isinstance(raw_text, str):
        return _error("The 'text' field must be a string.", 400)
    if not isinstance(length, str) or length not in SUPPORTED_LENGTHS:
        return _error("summary_length must be one of: short, medium, long.", 400)

    text = normalize_text(raw_text)
    if not text:
        return _error("Please enter some text to summarize.", 400)

    started = time.perf_counter()
    try:
        result = summarizer_service.generate_summary(text, length)
    except SummarizationError as exc:
        return _error(str(exc), exc.status_code)
    except Exception:
        app.logger.exception("Unexpected summarization failure")
        return _error("The summary could not be generated. Please try again.", 500)

    original_words = _word_count(text)
    summary_words = _word_count(result.summary)
    compression = (
        max(0.0, (1 - summary_words / original_words) * 100)
        if original_words
        else 0.0
    )
    return jsonify(
        {
            "success": True,
            "summary": result.summary,
            "statistics": {
                "original_word_count": original_words,
                "summary_word_count": summary_words,
                "original_character_count": len(text),
                "summary_character_count": len(result.summary),
                "compression_ratio": round(compression, 1),
                "processing_time": round(time.perf_counter() - started, 2),
                "truncated_input": result.truncated_input,
            },
        }
    )


@app.errorhandler(413)
def request_too_large(_exception):
    return _error("The request is too large. Please shorten the input.", 413)


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1")
