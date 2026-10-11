import json
import os
from typing import List, Dict, Any

EVALUATION_DATASET: List[Dict[str, Any]] = [
    {
        "id": 1,
        "question": "What architecture powers the latest NVIDIA AI GPU?",
        "ground_truth": "The latest NVIDIA AI GPU is powered by the Blackwell architecture delivering high AI compute and energy efficiency.",
        "relevant_documents": [
            "NVIDIA announced its newest Blackwell GPU architecture delivering breakthrough AI compute and energy efficiency for generative models."
        ]
    },
    {
        "id": 2,
        "question": "What is the key advantage of fault-tolerant topological qubits in quantum computing?",
        "ground_truth": "Fault-tolerant topological qubits provide stability and operate at higher temperatures for scalable quantum computing.",
        "relevant_documents": [
            "Physicists developed a fault-tolerant topological qubit system operating at higher temperatures."
        ]
    },
    {
        "id": 3,
        "question": "How did renewable energy installations perform this year?",
        "ground_truth": "Solar and wind installations achieved record capacity globally this year, reducing coal dependence.",
        "relevant_documents": [
            "Solar and wind installations achieved record capacity globally this year, reducing coal dependence."
        ]
    },
    {
        "id": 4,
        "question": "How is artificial intelligence transforming enterprise workflows?",
        "ground_truth": "AI helps organizations automate repetitive tasks, improve decision-making, and uncover insights without manual review.",
        "relevant_documents": [
            "Artificial intelligence is helping organizations automate repetitive tasks, improve decisions, and uncover insights from large volumes of content."
        ]
    },
    {
        "id": 5,
        "question": "What model does the content summarizer service utilize?",
        "ground_truth": "The content summarizer service uses the facebook/bart-large-cnn transformer model.",
        "relevant_documents": [
            "The summarizer service runs facebook/bart-large-cnn for abstractive text summarization."
        ]
    },
    {
        "id": 6,
        "question": "What model does the sentiment analysis service employ?",
        "ground_truth": "The sentiment analysis service uses distilbert-base-uncased-finetuned-sst-2-english.",
        "relevant_documents": [
            "Sentiment classification uses distilbert-base-uncased-finetuned-sst-2-english to score positive and negative sentiment."
        ]
    },
    {
        "id": 7,
        "question": "What vector database powers the semantic search retrieval?",
        "ground_truth": "ChromaDB is used as the persistent vector database for semantic retrieval.",
        "relevant_documents": [
            "ChromaDB stores document embeddings with cosine similarity for fast vector retrieval."
        ]
    },
    {
        "id": 8,
        "question": "Which embedding model is used for local vector generation?",
        "ground_truth": "The system utilizes the all-MiniLM-L6-v2 model from SentenceTransformers.",
        "relevant_documents": [
            "The embedding service uses all-MiniLM-L6-v2 from SentenceTransformers to generate 384-dimensional embeddings."
        ]
    },
    {
        "id": 9,
        "question": "How does the system prevent duplicate articles from being ingested?",
        "ground_truth": "The system generates a SHA-256 hash from the article URL or content and checks if it already exists in the database.",
        "relevant_documents": [
            "Duplicate prevention computes a SHA-256 content hash and skips inserting articles that already exist."
        ]
    },
    {
        "id": 10,
        "question": "What framework coordinates the RAG workflow graph?",
        "ground_truth": "LangGraph is used to orchestrate the agentic RAG workflow graph.",
        "relevant_documents": [
            "LangGraph compiles a StateGraph connecting query analysis, vector search, filtering, and answer generation."
        ]
    },
    {
        "id": 11,
        "question": "When does the system trigger web search fallback?",
        "ground_truth": "Web search fallback is triggered only when the local vector store does not return enough relevant documents above the threshold.",
        "relevant_documents": [
            "When local vector search yields no documents above the similarity threshold, the workflow triggers DuckDuckGo web search."
        ]
    },
    {
        "id": 12,
        "question": "What information is included in generated citations?",
        "ground_truth": "Generated citations include the article title, source, and URL.",
        "relevant_documents": [
            "Every generated response lists citations with article title, source publication, and canonical URL."
        ]
    },
    {
        "id": 13,
        "question": "What database stores the relational application data?",
        "ground_truth": "SQLite or PostgreSQL stores standard relational application data and metadata.",
        "relevant_documents": [
            "Relational article records and metadata are persisted in SQLite via SQLAlchemy ORM."
        ]
    },
    {
        "id": 14,
        "question": "How does query analysis improve search precision?",
        "ground_truth": "Query analysis strips conversational filler phrases and isolates core search keywords.",
        "relevant_documents": [
            "Query analysis removes conversational filler words like 'please tell me' to produce concise keyword queries."
        ]
    },
    {
        "id": 15,
        "question": "What scheduler interval is configured by default for RSS ingestion?",
        "ground_truth": "The default scheduler interval for background RSS polling is 300 seconds.",
        "relevant_documents": [
            "The background scheduler polls the RSS feed periodically with a default interval of 300 seconds."
        ]
    },
    {
        "id": 16,
        "question": "How are long documents handled before generating embeddings?",
        "ground_truth": "Long documents are cleaned and split into word chunks with overlapping windows.",
        "relevant_documents": [
            "Long texts are broken into chunks of 300 words with 50 words of overlap before generating embeddings."
        ]
    },
    {
        "id": 17,
        "question": "What distance metric is configured for the ChromaDB collection?",
        "ground_truth": "Cosine distance is used in ChromaDB to calculate similarity.",
        "relevant_documents": [
            "The ChromaDB collection is initialized with HNSW cosine distance space."
        ]
    },
    {
        "id": 18,
        "question": "What is the primary RSS feed ingested by default?",
        "ground_truth": "The default RSS feed configured is TechCrunch.",
        "relevant_documents": [
            "The default RSS feed URL in the configuration points to TechCrunch."
        ]
    },
    {
        "id": 19,
        "question": "What endpoint processes raw user queries through the agentic RAG workflow?",
        "ground_truth": "The POST /ask endpoint processes user queries through the LangGraph workflow.",
        "relevant_documents": [
            "The POST /ask endpoint receives a query and invokes the LangGraph agentic RAG workflow."
        ]
    },
    {
        "id": 20,
        "question": "How does the filter and rerank node decide which documents to keep?",
        "ground_truth": "It removes documents below the similarity threshold and keeps the top most relevant results.",
        "relevant_documents": [
            "The filter node removes documents with similarity below 0.25 and retains the top 3 highest-scoring documents."
        ]
    },
    {
        "id": 21,
        "question": "What does the /health endpoint return?",
        "ground_truth": "The /health endpoint returns a JSON object with status ok.",
        "relevant_documents": [
            "GET /health returns a status dictionary indicating the service is healthy."
        ]
    },
    {
        "id": 22,
        "question": "What does the GET /search endpoint do?",
        "ground_truth": "The GET /search endpoint performs semantic vector retrieval for a given query string.",
        "relevant_documents": [
            "GET /search accepts query and limit parameters and returns matching chunks with similarity scores."
        ]
    }
]


def get_evaluation_dataset() -> List[Dict[str, Any]]:
    dataset_path = os.path.join(os.path.dirname(__file__), "eval_dataset.json")
    if os.path.exists(dataset_path):
        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return EVALUATION_DATASET


def save_evaluation_dataset(path: str = None) -> str:
    target_path = path or os.path.join(os.path.dirname(__file__), "eval_dataset.json")
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(EVALUATION_DATASET, f, indent=2)
    return target_path


if __name__ == "__main__":
    p = save_evaluation_dataset()
    print(f"Saved {len(EVALUATION_DATASET)} evaluation items to {p}")

