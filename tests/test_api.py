import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_search_endpoint(client):
    response = client.get("/search", params={"query": "technology"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_ask_endpoint(client):
    response = client.post("/ask", json={"query": "Tell me about technology developments"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert isinstance(data["sources"], list)
    assert len(data["answer"]) > 0


def test_articles_endpoints(client):
    response = client.get("/articles")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

