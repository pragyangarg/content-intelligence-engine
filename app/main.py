from app.models.database import engine
from app.models import content
from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="Content Intelligence Engine",
    description="AI-powered content processing pipeline",
    version="1.0.0"
)
content.Base.metadata.create_all(bind=engine)
app.include_router(router)

@app.get("/")
def root():
    return {"message": "Content Intelligence Engine is running"}
