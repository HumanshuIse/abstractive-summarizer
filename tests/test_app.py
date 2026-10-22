import os

os.environ["SUMMARIZER_LOAD_ON_STARTUP"] = "0"

from app import app, summarizer_service
from summarizer import SummaryResult


def client():
    app.config.update(TESTING=True)
    return app.test_client()


def test_homepage():
    response = client().get("/")
    assert response.status_code == 200
    assert b"SummarAI" in response.data


def test_health_endpoint():
    response = client().get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["success"] is True


def test_empty_input_is_rejected():
    response = client().post("/api/summarize", json={"text": "   ", "summary_length": "short"})
    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_invalid_length_is_rejected():
    response = client().post("/api/summarize", json={"text": "A useful article " * 20, "summary_length": "tiny"})
    assert response.status_code == 400


def test_malformed_request_is_rejected():
    response = client().post("/api/summarize", data="not json", content_type="application/json")
    assert response.status_code == 400


def test_success_response_structure(monkeypatch):
    monkeypatch.setattr(
        summarizer_service,
        "generate_summary",
        lambda text, length: SummaryResult("A concise generated summary."),
    )
    response = client().post("/api/summarize", json={"text": "A useful article " * 20, "summary_length": "medium"})
    body = response.get_json()
    assert response.status_code == 200
    assert body["success"] is True
    assert "summary" in body
    assert {"original_word_count", "summary_word_count", "compression_ratio", "processing_time"} <= body["statistics"].keys()
