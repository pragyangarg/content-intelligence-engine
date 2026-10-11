import pytest
from app.services.agentic_rag import AgenticRAGWorkflow
from app.services.vector_store import VectorStoreService
from app.services.embedding_service import EmbeddingService


@pytest.fixture(scope="module")
def rag_workflow():
    embedding_service = EmbeddingService()
    vs = VectorStoreService(
        embedding_service=embedding_service,
        persist_directory="./tests_temp_rag_chroma",
        collection_name="test_rag_collection"
    )
    vs.index_content({
        "id": 901,
        "title": "Solid State Battery Innovation",
        "content": "Automakers tested solid-state batteries with 1000 km range on a single charge.",
        "source": "BatteryTech",
        "url": "https://example.com/solid-state",
    })

    wf = AgenticRAGWorkflow(vector_store=vs)
    yield wf

    import shutil
    try:
        shutil.rmtree("./tests_temp_rag_chroma", ignore_errors=True)
    except Exception:
        pass


def test_graph_executes_successfully(rag_workflow):
    result = rag_workflow.run("What is the range of solid-state batteries?")
    assert "query" in result
    assert "rewritten_query" in result
    assert "documents" in result
    assert "answer" in result
    assert "citations" in result
    assert len(result["answer"]) > 0
    assert len(result["citations"]) > 0
    assert "Solid State Battery Innovation" in result["citations"][0]["title"]


def test_missing_context_handled(rag_workflow):
    # Query completely unrelated to indexed content with rare tokens
    result = rag_workflow.run("xyzabc123 obscure ancient pottery techniques in 4000 BC")
    assert "answer" in result
    assert "citations" in result
    assert isinstance(result["answer"], str)
    # The system should either return fallback or informative response without crashing
    assert len(result["answer"]) > 0

