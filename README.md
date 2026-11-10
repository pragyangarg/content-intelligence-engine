# Content Intelligence Engine V2 (Agentic RAG)

An automated content ingestion and agentic Retrieval-Augmented Generation (RAG) platform. It continuously monitors RSS feeds, processes articles with transformer-based NLP (BART summarization & sentiment analysis), stores relational records in SQLite, generates semantic embeddings with SentenceTransformers, indexes chunks in ChromaDB, and coordinates question answering via a LangGraph state workflow with query analysis, vector search, relevance filtering, web search fallback, and citations.

---

## Architecture Overview

### 1. Dual-Layer Routing & MCP Microservice Architecture

The platform features a hybrid microservice architecture integrating a high-speed **Jev AI Triage Agent** and the **Model Context Protocol (MCP)**:

```text
                           Incoming Request / Prompt
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │      triage-agent/router.py   │
                       │   (OpenRouter Decisions API)  │
                       │     Model: typesafe/jev-1.14  │
                       └───────────────┬───────────────┘
                                       │
                  ┌────────────────────┴────────────────────┐
                  │                                         │
       Choice: requires_jev                      Choice: requires_llm
   (Confidence >= 0.75 cutoff)               (or low-confidence fallback)
                  │                                         │
                  ▼                                         ▼
   ┌─────────────────────────────┐        ┌───────────────────────────────────┐
   │ Jev Strict Categorization   │        │ MCP Client (mcp.client.stdio)     │
   │  - Zero prompt fluff        │        │ Spawns stdio process across dirs  │
   │  - Strict choice evaluation │        └─────────────────┬─────────────────┘
   │  - Returns category         │                          │
   └─────────────────────────────┘                          │ stdio transport
                                                            ▼
                                          ┌───────────────────────────────────┐
                                          │ mcp_server.py (FastMCP Bridge)    │
                                          │ ContentIntelligenceBackend        │
                                          └─────────────────┬─────────────────┘
                                                            │
                                        ┌───────────────────┼───────────────────┐
                                        ▼                   ▼                   ▼
                               trigger_backend_llm   fetch_db_errors   trigger_n8n_rss
                               (Core RAG Pipeline)    (PostgreSQL)        (Webhooks)
```

- **Dual-Layer Routing ("System One" vs. "System Two")**:
  - **System One (Fast Decision Layer)**: Uses `typesafe/jev-1.14` through OpenRouter's Decisions API (`https://openrouter.ai/api/alpha/decisions`). It acts as a lightweight, low-latency router evaluating structured choices.
  - **Path `requires_jev`**: When the query only requires strict classification without explanation (e.g., ticket categorization into predefined labels) and confidence score $\ge 0.75$, Jev resolves it directly with minimal token and latency overhead.
  - **Path `requires_llm`**: When the user requests synthesis, explanation, troubleshooting, or complex generative tasks (or if Jev confidence falls below $0.75$), the agent escalates execution to the heavy LLM / RAG backend.
- **Secure Cross-Directory MCP Protocol**:
  - The client (`triage-agent/router.py`) and backend bridge (`mcp_server.py`) communicate over the standard **Model Context Protocol (MCP)** using `StdioServerParameters` and `stdio_client`.
  - Process isolation: The client spawns the backend server as a subprocess communicating securely over standard input/output (`stdio`), eliminating HTTP exposure and port management for internal tool invocations.

---

### 2. Core Agentic RAG Pipeline

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
6. **Jev AI Triage & MCP Microservice Bridge**:
   - High-speed dual-layer routing via OpenRouter Decisions API (`typesafe/jev-1.14`).
   - Fast categorization path (`requires_jev`) bypassing LLMs for predefined classification criteria.
   - MCP bridge (`mcp_server.py`) exposing core engine capabilities over secure `stdio` process pipes.
7. **Evaluation & Benchmarking**:
   - Curated 22-question benchmark dataset (`app/evaluation/dataset.py`).
   - Comparison of **Version A (Baseline RAG)** vs. **Version B (Agentic RAG)**.
   - Measures Faithfulness, Answer Relevance, Context Relevance, and Context Recall.
   - Results exported to JSON (`evaluation_results.json`) and CSV (`evaluation_results.csv`).
8. **Full API & Interactive UI**:
   - FastAPI REST endpoints (`/ask`, `/search`, `/articles`, `/health`).
   - Streamlit interactive demo dashboard (`streamlit_app.py`) for live exploration.

---

## Monorepo Component Layout

```text
content-intelligence-engine/
├── app/                        # Core Content Intelligence Engine Backend
│   ├── api/                    # FastAPI routes (/ask, /search, /articles, /contents)
│   ├── evaluation/             # RAG evaluation dataset and benchmark runner
│   ├── models/                 # SQLAlchemy ORM models (Content table, migrations)
│   ├── schemas/                # Pydantic request/response schemas
│   ├── services/               # Core domain services
│   │   ├── agentic_rag.py      # LangGraph state workflow orchestration
│   │   ├── embedding_service.py# SentenceTransformers embedding generation
│   │   ├── llm_service.py      # LLM answer synthesis with citations
│   │   ├── rss_monitor.py      # RSS feed parsing & multi-feed ingestion
│   │   ├── scheduler.py        # Background scheduler
│   │   ├── sentiment.py        # DistilBERT sentiment scoring
│   │   ├── summarizer.py       # BART abstractive summarizer
│   │   ├── vector_store.py     # ChromaDB vector retrieval service
│   │   └── web_search.py       # DuckDuckGo fallback service
│   └── main.py                 # FastAPI application root & lifespan setup
├── triage-agent/               # Jev AI Triage Microservice Client
│   ├── router.py               # Triage agent: Jev Decisions API + MCP stdio client
│   ├── pyproject.toml          # uv / Python project configuration
│   └── .env                    # Triage agent environment config (OPENROUTER_API_KEY)
├── mcp_server.py               # FastMCP Server bridge exposing backend tools over stdio
├── streamlit_app.py            # Streamlit interactive UI dashboard
├── requirements.txt            # Core engine Python dependencies
├── pyproject.toml              # Top-level uv project definition
└── Dockerfile                  # Container packaging for deployment
```

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

#### Core Engine Configuration (`.env`)
Create `.env` in the root folder based on `.env.example`:

```bash
copy .env.example .env
```

Key environment variables:
- `RSS_FEED_URL`: RSS feed URL (default: `https://techcrunch.com/feed/`)
- `SCHEDULER_INTERVAL`: Periodic RSS poll interval in seconds (default: `300`)
- `OPENAI_API_KEY`: (Optional) OpenAI API key. If omitted, the engine uses local grounded synthesis.
- `ENABLE_TRANSFORMER_MODELS`: Set to `true` to load BART and DistilBERT transformer models locally.

#### Triage Agent Configuration (`triage-agent/.env`)
Create or edit `triage-agent/.env`:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

---

### 3. Running the Jev Triage Agent (MCP Client)

The triage agent routes incoming prompts using the OpenRouter Decisions API (`typesafe/jev-1.14`) and connects to `mcp_server.py` over stdio when execution requires the core backend LLM.

#### Using `uv` (inside `triage-agent/`):
```bash
cd triage-agent
uv run router.py
```

#### Using Python directly:
```bash
cd triage-agent
python router.py
```

Sample interactive output:
```text
--- New Request: 'What is the severity of this database connection error, and how do I fix it?' ---
[Router] Selected Path: requires_llm (Confidence: 0.95)
[Agent] Spinning up MCP Server connection...
[Agent] Connected. Triggering 'trigger_backend_llm' tool...
[Real Backend] LLM response would be generated here...

--- New Request: 'Sort this ticket: 'The login page is returning a 500 error'.' ---
[Router] Selected Path: requires_jev (Confidence: 0.98)
[Agent] Asking Jev for strict categorization...
[Jev Execution] Categorized as: Bug
```

---

### 4. Running the Standalone MCP Server Bridge (Optional Direct Test)

To test the MCP server independently over stdio:

```bash
python mcp_server.py
```

---

### 5. Start the FastAPI Service

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive documentation will be available at: `http://localhost:8000/docs`

### 6. Start the Streamlit Dashboard (Optional)

```bash
streamlit run streamlit_app.py
```

### 7. Run the Test Suite

```bash
pytest -v
```

### 8. Run the RAG Evaluation Benchmark

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
