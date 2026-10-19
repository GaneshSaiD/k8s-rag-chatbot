from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "running" in resp.json()["message"]


def test_health():
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_query_rejects_empty_question():
    resp = client.post("/api/v1/query", json={"question": "   "})
    assert resp.status_code == 400


def test_query_rejects_missing_field():
    resp = client.post("/api/v1/query", json={})
    assert resp.status_code == 422


@patch("backend.api.routes.ask")
def test_query_returns_answer_and_sources(mock_ask):
    mock_ask.return_value = {"answer": "Check the container logs.", "sources": ["https://kubernetes.io/a"]}
    resp = client.post("/api/v1/query", json={"question": "Why CrashLoopBackOff?"})
    assert resp.status_code == 200
    assert resp.json() == {"answer": "Check the container logs.", "sources": ["https://kubernetes.io/a"]}
    mock_ask.assert_called_once_with("Why CrashLoopBackOff?")


@patch("backend.api.routes.ask", side_effect=RuntimeError("pinecone down"))
def test_query_returns_500_when_rag_fails(_mock_ask):
    resp = client.post("/api/v1/query", json={"question": "anything"})
    assert resp.status_code == 500
