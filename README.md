# Content Intelligence Engine V2 (Agentic RAG)

An automated content ingestion and agentic Retrieval-Augmented Generation (RAG) platform. It continuously monitors RSS feeds, processes articles with transformer-based NLP (BART summarization & sentiment analysis), stores relational records in SQLite, generates semantic embeddings with SentenceTransformers, indexes chunks in ChromaDB, and coordinates question answering via a LangGraph state workflow with query analysis, vector search, relevance filtering, web search fallback, and citations.

---

## Architecture Overview

```text
                    RSS / Blogs
                         │
                         ▼
                 Ingestion Scheduler
                         │
                         ▼
                  Article Processing
                         │
                  ┌──────┴──────┐
                  ▼             ▼
             PostgreSQL/      ChromaDB
               SQLite        (Embeddings)
                  │             │
                  └──────┬──────┘
                         │
                    User Query
                         │
                         ▼
                      FastAPI
                         │
                         ▼
                     LangGraph
                         │
                 ┌───────┴────────┐
                 ▼                ▼
          Query Analysis     Vector Search
                                  │
                                  ▼
                           Filter / Rerank
                                  │
                         ┌────────┴────────┐
                         │                 │
                  Local Relevant       Not enough
                         │                 │
                         │            Web Search
                         │            (DuckDuckGo)
                         │                 │
                         └────────┬────────┘
                                  ▼
                              LLM (OpenAI / Local)
                                  │
                                  ▼
                         Answer + Citations
                                  │
                                  ▼
                             Evaluation
                                  │
                       Ragas / Benchmark Metrics
```

---

## Features

1. **Robust Article Ingestion & Deduplication**:
   - SHA-256 hash generation on canonical URLs or content to prevent duplicates.
   - Preserves publication dates, source information, full content, summaries, and sentiments.
2. **Local Embeddings**:
   - SentenceTransformers (`all-MiniLM-L6-v2`) generating 384-dimensional dense vectors.
   - Text cleaning and word chunking with configurable overlap.
3. **ChromaDB Vector Store**:
   - Persistent vector storage with cosine distance metric.
   - Automatic metadata tracking (`title`, `source`, `url`, `published_at`, `article_id`).
4. **LangGraph Agentic Orchestration**:
   - Typed graph state (`RAGState`).
   - Query Analysis node rewriting search queries and stripping conversational noise.
   - Vector Search node for semantic retrieval.
   - Filter & Rerank node evaluating similarity thresholds.
   - Conditional router executing web search fallback when local context is insufficient.
   - Answer Generation node producing grounded responses with structured citations.
5. **Citations & Attribution**:
   - Strict source attribution (titles, sources, and canonical URLs) from retrieved documents.
6. **Evaluation & Benchmarking**:
   - Curated 22-question benchmark dataset (`app/evaluation/dataset.py`).
   - Comparison of **Version A (Baseline RAG)** vs. **Version B (Agentic RAG)**.
   - Measures Faithfulness, Answer Relevance, Context Relevance, and Context Recall.
   - Results exported to JSON (`evaluation_results.json`) and CSV (`evaluation_results.csv`).
7. **Full API & Interactive UI**:
   - FastAPI REST endpoints (`/ask`, `/search`, `/articles`, `/health`).
   - Streamlit interactive demo dashboard (`streamlit_app.py`) for live exploration.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health status |
| `GET` | `/articles` | List all ingested articles |
| `GET` | `/articles/{id}` | Get article by ID |
| `GET` | `/search?query=...&top_k=5` | Semantic vector search across ChromaDB |
| `POST` | `/ask` | Ask question to the Agentic RAG workflow |
| `POST` | `/contents` | Create content item and index into vector store |
| `GET` | `/contents` | Legacy endpoint to retrieve processed items |
| `POST` | `/process-content` | Run workflow engine on text |
| `POST` | `/process-rss` | Trigger immediate fetch and ingestion of RSS feed |

### Example Request to `/ask`:

```bash
curl -X POST "http://localhost:8000/ask" \
     -H "Content-Type: application/json" \
     -d '{"query": "What are the latest developments in AI chips?"}'
```

Response:

```json
{
  "answer": "According to NVIDIA unveils AI GPU, NVIDIA announced its newest Blackwell GPU architecture delivering breakthrough AI compute and energy efficiency.\n\nSources:\n1. NVIDIA unveils AI GPU - TechRadar (https://techradar.com/nvidia-gpu)",
  "sources": [
    {
      "title": "NVIDIA unveils AI GPU",
      "url": "https://techradar.com/nvidia-gpu",
      "source": "TechRadar"
    }
  ],
  "rewritten_query": "latest developments in AI chips"
}
```

---

## Running Locally

### 1. Prerequisites & Installation

```bash
# Clone the repository
git clone <repo-url>
cd content-intelligence-engine

# Create virtual environment and activate
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Variables

Create `.env` based on `.env.example`:

```bash
copy .env.example .env
```

Key environment variables:
- `RSS_FEED_URL`: RSS feed URL (default: `https://techcrunch.com/feed/`)
- `SCHEDULER_INTERVAL`: Periodic RSS poll interval in seconds (default: `300`)
- `OPENAI_API_KEY`: (Optional) OpenAI API key. If omitted, the engine uses local grounded synthesis.
- `ENABLE_TRANSFORMER_MODELS`: Set to `true` to load BART and DistilBERT transformer models locally.

### 3. Start the FastAPI Service

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive documentation will be available at: `http://localhost:8000/docs`

### 4. Start the Streamlit Dashboard (Optional)

```bash
streamlit run streamlit_app.py
```

### 5. Run the Test Suite

```bash
pytest -v
```

### 6. Run the RAG Evaluation Benchmark

```bash
python -m app.evaluation.evaluator
```

This runs the comparative benchmark between Version A and Version B and saves results in:
- `app/evaluation/evaluation_results.json`
- `app/evaluation/evaluation_results.csv`

---

## Docker Setup

### Build the Docker Image:

```bash
docker build -t content-intelligence-engine .
```

### Run the Container:

```bash
docker run -p 8000:8000 --env-file .env content-intelligence-engine
```
