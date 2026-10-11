import textwrap
from typing import Any

import requests
import streamlit as st


st.set_page_config(
    page_title="Content Intelligence Engine",
    page_icon="CI",
    layout="wide",
)


API_DEFAULT = "http://127.0.0.1:8000"


def call_api(method: str, endpoint: str, **kwargs: Any) -> requests.Response:
    base_url = st.session_state.get("api_base_url", API_DEFAULT).rstrip("/")
    url = f"{base_url}{endpoint}"
    response = requests.request(method, url, timeout=20, **kwargs)
    response.raise_for_status()
    return response


def fetch_contents() -> list[dict[str, Any]]:
    response = call_api("GET", "/contents")
    data = response.json()
    return data if isinstance(data, list) else []


def fetch_health() -> tuple[bool, str]:
    try:
        response = call_api("GET", "/health")
        payload = response.json()
        return True, str(payload.get("status", "ok"))
    except Exception as exc:
        return False, str(exc)


def render_content_card(item: dict[str, Any]) -> None:
    title = item.get("title", "Untitled")
    source = item.get("source", "Unknown source")
    sentiment = item.get("sentiment") or "UNKNOWN"
    summary = item.get("summary") or "No summary available yet."

    with st.container(border=True):
        st.markdown(f"### {title}")
        st.caption(f"Source: {source}")
        st.write(f"Sentiment: **{sentiment}**")
        st.write(summary)


def refresh_contents() -> list[dict[str, Any]]:
    try:
        contents = fetch_contents()
        st.session_state["contents"] = contents
        return contents
    except Exception as exc:
        st.error(f"Could not load processed content: {exc}")
        return st.session_state.get("contents", [])


st.markdown(
    """
    <style>
    .hero {
        padding: 1.4rem 1.6rem;
        border-radius: 20px;
        background: linear-gradient(135deg, #1e293b, #0f172a);
        color: #ffffff;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.25);
        margin-bottom: 1.5rem;
    }
    .hero h1 {
        margin: 0;
        font-size: 2.3rem;
        font-weight: 700;
        color: #ffffff !important;
    }
    .hero p {
        margin: 0.5rem 0 0;
        color: #cbd5e1 !important;
        font-size: 1rem;
    }
    .metric-card {
        padding: 1.2rem;
        border-radius: 16px;
        background: #1e293b;
        border: 1px solid #334155;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        color: #f8fafc;
        text-align: center;
    }
    .metric-card h3 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
        color: #38bdf8 !important;
    }
    .metric-card p {
        margin: 0.25rem 0 0;
        color: #94a3b8 !important;
        font-size: 0.95rem;
        font-weight: 500;
    }
    div[data-baseweb="tab-list"] {
        gap: 8px;
        margin-bottom: 1rem;
    }
    button[data-baseweb="tab"] {
        font-weight: 600 !important;
        font-size: 1rem !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>Content Intelligence Engine</h1>
        <p>Showcase automated article processing, summarization, sentiment analysis, and RSS ingestion from one simple demo screen.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


with st.sidebar:
    st.header("Demo Controls")
    st.session_state["api_base_url"] = st.text_input("FastAPI URL", value=API_DEFAULT)

    backend_ok, backend_status = fetch_health()
    if backend_ok:
        st.success(f"Backend connected: {backend_status}")
    else:
        st.error("Backend unavailable")
        st.caption(backend_status)

    if st.button("Refresh Dashboard", use_container_width=True):
        refresh_contents()

    st.caption("Run backend first: `venv\\Scripts\\python.exe -m uvicorn app.main:app`")


if "contents" not in st.session_state:
    st.session_state["contents"] = refresh_contents()

contents = st.session_state.get("contents", [])
positive_count = sum(1 for item in contents if str(item.get("sentiment", "")).upper() == "POSITIVE")
negative_count = sum(1 for item in contents if str(item.get("sentiment", "")).upper() == "NEGATIVE")

metric_col1, metric_col2, metric_col3 = st.columns(3)
with metric_col1:
    st.markdown(
        f'<div class="metric-card"><h3>{len(contents)}</h3><p>Processed Articles</p></div>',
        unsafe_allow_html=True,
    )
with metric_col2:
    st.markdown(
        f'<div class="metric-card"><h3>{positive_count}</h3><p>Positive Results</p></div>',
        unsafe_allow_html=True,
    )
with metric_col3:
    st.markdown(
        f'<div class="metric-card"><h3>{negative_count}</h3><p>Negative Results</p></div>',
        unsafe_allow_html=True,
    )


tab_manual, tab_rss, tab_rag, tab_gallery = st.tabs(["Manual Demo", "RSS Demo", "Agentic RAG & Search", "Processed Content"])

with tab_manual:
    st.subheader("Process a single article")
    with st.form("manual_process_form"):
        title = st.text_input("Article title", value="AI transforms enterprise workflows")
        source = st.text_input("Source", value="Teacher Demo")
        text = st.text_area(
            "Article text",
            height=220,
            value=textwrap.dedent(
                """
                Artificial intelligence is helping organizations automate repetitive tasks,
                improve decisions, and uncover insights from large volumes of content.
                Teams can monitor incoming articles, summarize them quickly, and measure
                overall sentiment without manually reading every document.
                """
            ).strip(),
        )
        submitted = st.form_submit_button("Process Content", use_container_width=True)

    if submitted:
        try:
            response = call_api(
                "POST",
                "/process-content",
                params={"title": title, "source": source, "text": text},
            )
            result = response.json()
            st.success("Article processed successfully.")
            st.json(result)
            contents = refresh_contents()
        except Exception as exc:
            st.error(f"Processing failed: {exc}")

with tab_rss:
    st.subheader("Process live RSS feed content")

    feed_presets = {
        "TechCrunch": "https://techcrunch.com/feed/",
        "The Verge": "https://www.theverge.com/rss/index.xml",
        "Wired": "https://www.wired.com/feed/rss",
        "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
        "BBC Technology": "https://feeds.bbci.co.uk/news/technology/rss.xml",
        "MIT Technology Review": "https://www.technologyreview.com/feed/",
        "Engadget": "https://www.engadget.com/rss.xml",
        "Hacker News": "https://news.ycombinator.com/rss",
        "Custom URL": ""
    }

    selected_preset = st.selectbox("Choose a Popular Tech Feed Preset", list(feed_presets.keys()))
    default_url = feed_presets[selected_preset] if selected_preset != "Custom URL" else "https://techcrunch.com/feed/"

    with st.form("rss_process_form"):
        rss_url = st.text_input("RSS feed URL", value=default_url)
        limit = st.slider("Articles to ingest from this feed", min_value=1, max_value=25, value=10)
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            rss_submitted = st.form_submit_button("Fetch and Process Feed", use_container_width=True)
        with col_btn2:
            batch_submitted = st.form_submit_button("Batch Ingest All 8 Feeds", use_container_width=True)

    if rss_submitted:
        with st.spinner(f"Ingesting {limit} articles from {rss_url}..."):
            try:
                response = call_api("POST", "/process-rss", params={"rss_url": rss_url, "limit": limit})
                result = response.json()
                st.success(f"Fetched and processed {len(result)} feed items.")
                st.json(result)
                contents = refresh_contents()
            except Exception as exc:
                st.error(f"RSS processing failed: {exc}")

    if batch_submitted:
        with st.spinner("Ingesting top articles across all 8 technology feeds..."):
            try:
                response = call_api("POST", "/process-all-feeds", params={"limit_per_feed": 5})
                result = response.json()
                st.success(f"Batch ingestion complete! Processed {len(result)} articles into SQLite & ChromaDB.")
                contents = refresh_contents()
            except Exception as exc:
                st.error(f"Batch ingestion failed: {exc}")

with tab_rag:
    st.subheader("Ask the Agentic RAG Engine")
    query_col, ask_btn_col = st.columns([4, 1])
    user_query = st.text_input("Enter your question", value="What are recent developments in artificial intelligence?")
    
    col_ask, col_search = st.columns(2)
    with col_ask:
        if st.button("Ask Agent (LangGraph RAG)", use_container_width=True):
            if user_query:
                with st.spinner("Analyzing query, searching knowledge base, and generating answer..."):
                    try:
                        res = call_api("POST", "/ask", json={"query": user_query}).json()
                        st.markdown("### Answer")
                        st.info(res.get("answer", ""))
                        if res.get("rewritten_query"):
                            st.caption(f"Query analyzed as: `{res.get('rewritten_query')}`")
                        sources = res.get("sources", [])
                        if sources:
                            st.markdown("#### Citations")
                            for s in sources:
                                st.markdown(f"- **{s.get('title')}** ({s.get('source')}) [Link]({s.get('url')})")
                    except Exception as exc:
                        st.error(f"Error querying agent: {exc}")
    with col_search:
        if st.button("Semantic Vector Search", use_container_width=True):
            if user_query:
                with st.spinner("Searching ChromaDB vectors..."):
                    try:
                        res = call_api("GET", "/search", params={"query": user_query, "top_k": 3}).json()
                        st.markdown("### Retrieved Documents")
                        for d in res:
                            with st.expander(f"{d.get('title')} (Similarity: {d.get('similarity', 0):.2f})"):
                                st.caption(f"Source: {d.get('source')} | URL: {d.get('url')}")
                                st.write(d.get("content"))
                    except Exception as exc:
                        st.error(f"Error searching: {exc}")

with tab_gallery:
    st.subheader("Processed content gallery")
    if not contents:
        st.info("No processed content found yet. Use the tabs above to create a demo.")
    else:
        for item in reversed(contents):
            render_content_card(item)
