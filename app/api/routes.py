from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models.database import SessionLocal
from app.models.content import Content, compute_content_hash
from app.schemas.content_schema import (
    ContentCreate,
    ContentResponse,
    AskRequest,
    AskResponse,
    SourceItem,
    SearchDocumentResponse,
)
from app.services.content_formatter import normalize_content_fields
from app.services.vector_store import search_documents
from app.services.agentic_rag import ask_engine
from typing import List, Optional
from datetime import datetime

router = APIRouter()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _format_content_item(item: Content) -> ContentResponse:
    summary, sentiment = normalize_content_fields(item.summary, item.sentiment)
    return ContentResponse(
        id=item.id,
        title=item.title,
        source=item.source,
        content=item.content,
        summary=summary,
        sentiment=sentiment,
        url=item.url,
        published_at=item.published_at,
        created_at=item.created_at,
        content_hash=item.content_hash,
    )


# --- Relational Articles Endpoints ---
@router.post("/contents", response_model=ContentResponse)
def create_content(content: ContentCreate, db: Session = Depends(get_db)):
    content_hash = compute_content_hash(url=content.url, content=content.content, title=content.title)
    existing = db.query(Content).filter(
        (Content.content_hash == content_hash) | (Content.title == content.title)
    ).first()
    if existing:
        return _format_content_item(existing)

    db_content = Content(
        title=content.title,
        source=content.source,
        content=content.content,
        url=content.url,
        published_at=content.published_at,
        created_at=datetime.utcnow(),
        content_hash=content_hash,
    )
    db.add(db_content)
    db.commit()
    db.refresh(db_content)
    try:
        from app.services.vector_store import get_vector_store
        get_vector_store().index_content(db_content)
    except Exception:
        pass
    return _format_content_item(db_content)


@router.get("/contents", response_model=List[ContentResponse])
def get_contents(db: Session = Depends(get_db)):
    items = db.query(Content).all()
    return [_format_content_item(item) for item in items]


@router.get("/articles", response_model=List[ContentResponse])
def get_articles(db: Session = Depends(get_db)):
    items = db.query(Content).all()
    return [_format_content_item(item) for item in items]


@router.get("/articles/{article_id}", response_model=ContentResponse)
def get_article(article_id: int, db: Session = Depends(get_db)):
    item = db.query(Content).filter(Content.id == article_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Article not found")
    return _format_content_item(item)


# --- Semantic Search Endpoint ---
@router.get("/search", response_model=List[SearchDocumentResponse])
def search_endpoint(
    query: Optional[str] = Query(None, description="Query string for semantic search"),
    q: Optional[str] = Query(None, description="Short alias for query"),
    top_k: int = Query(5, ge=1, le=20, description="Maximum results to return"),
):
    search_text = query or q or ""
    if not search_text.strip():
        return []
    results = search_documents(query=search_text, top_k=top_k)
    return [
        SearchDocumentResponse(
            id=str(r.get("id")),
            article_id=r.get("article_id") if isinstance(r.get("article_id"), int) and r.get("article_id") > 0 else None,
            title=r.get("title", ""),
            source=r.get("source", ""),
            url=r.get("url"),
            published_at=r.get("published_at"),
            content=r.get("content", ""),
            similarity=float(r.get("similarity", 0.0)),
            distance=float(r.get("distance", 1.0)),
        )
        for r in results
    ]


# --- Agentic RAG Endpoint ---
@router.post("/ask", response_model=AskResponse)
def ask_endpoint(payload: AskRequest):
    if not payload.query or not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    result = ask_engine(payload.query)

    sources = [
        SourceItem(
            title=c.get("title", "Untitled"),
            url=c.get("url"),
            source=c.get("source")
        )
        for c in result.get("citations", [])
    ]

    return AskResponse(
        answer=result.get("answer", ""),
        sources=sources,
        rewritten_query=result.get("rewritten_query")
    )


# --- Health Check Endpoint ---
@router.get("/health")
def health_endpoint():
    return {"status": "ok"}
