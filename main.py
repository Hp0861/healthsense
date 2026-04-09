"""
main.py – FastAPI application entry point for HealthSense.

Run with:
    uvicorn backend.main:app --reload --port 8000
"""

import sys
from pathlib import Path

# Ensure repo root is on the path so sibling packages resolve correctly
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routes import router

app = FastAPI(
    title="HealthSense API",
    description="Family Health Report Understanding App – India-focused",
    version="1.0.0",
)

# Allow Streamlit (localhost:8501) to talk to FastAPI (localhost:8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialise the database on startup
@app.on_event("startup")
def startup():
    init_db()
    print("✅  HealthSense DB initialised.")


app.include_router(router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "app": "HealthSense",
        "status": "running",
        "docs": "/docs",
    }
