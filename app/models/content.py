from sqlalchemy import Column, Integer, String, Text
from app.models.database import Base

class Content(Base):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    source = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    sentiment = Column(String, nullable=True)