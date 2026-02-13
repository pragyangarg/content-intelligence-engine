from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.database import SessionLocal
from app.models.content import Content
from app.schemas.content_schema import ContentCreate, ContentResponse
from typing import List

router = APIRouter()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/contents", response_model=ContentResponse)
def create_content(content: ContentCreate, db: Session = Depends(get_db)):
    db_content = Content(
        title=content.title,
        source=content.source
    )
    db.add(db_content)
    db.commit()
    db.refresh(db_content)
    return db_content


@router.get("/contents", response_model=List[ContentResponse])
def get_contents(db: Session = Depends(get_db)):
    return db.query(Content).all()