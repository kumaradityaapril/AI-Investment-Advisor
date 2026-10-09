from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="GenAI-powered AI Investment Advisor API",
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ai-investment-advisor-api",
    }


@app.get("/health/db")
def database_health_check(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1"))
    value = result.scalar()
    return {
        "status": "healthy",
        "database": "connected",
        "result": value,
    }


@app.get("/health/vector")
def vector_health_check(db: Session = Depends(get_db)):
    result = db.execute(
        text("""
            SELECT
                '[1,2,3]'::vector <-> '[1,2,4]'::vector
                AS distance
        """)
    )
    distance = result.scalar()
    return {
        "status": "healthy",
        "extension": "pgvector",
        "vector_operation": "successful",
        "distance": distance,
    }
