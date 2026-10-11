import os
import shutil
import pytest
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStoreService


@pytest.fixture(scope="module")
def temp_vector_store():
    test_dir = "./tests_temp_chroma"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

    embedding_service = EmbeddingService()
    vs = VectorStoreService(
        embedding_service=embedding_service,
        persist_directory=test_dir,
        collection_name="test_retrieval_collection"
    )

    # Seed test content
    vs.index_content({
        "id": 501,
        "title": "Quantum Supremacy in Computing",
        "content": "Superconducting circuits achieved high fidelity qubit gates in quantum computers.",
        "source": "TechDaily",
        "url": "https://example.com/quantum",
    })
    vs.index_content({
        "id": 502,
        "title": "Autonomous Electric Vehicles",
        "content": "Self driving cars use lidar and radar sensors to navigate city traffic safely.",
        "source": "AutoNews",
        "url": "https://example.com/ev",
    })

    yield vs

    try:
        shutil.rmtree(test_dir, ignore_errors=True)
    except Exception:
        pass


def test_query_returns_relevant_documents(temp_vector_store):
    results = temp_vector_store.search_documents("quantum qubits computing", top_k=2)
    assert len(results) > 0
    top_doc = results[0]
    assert "Quantum" in top_doc["title"]
    assert top_doc["similarity"] > 0.0
    assert "distance" in top_doc


def test_empty_results_handled_correctly(temp_vector_store):
    # Empty query string
    empty_res = temp_vector_store.search_documents("", top_k=5)
    assert empty_res == []

    # Whitespace query
    whitespace_res = temp_vector_store.search_documents("   ", top_k=5)
    assert whitespace_res == []

