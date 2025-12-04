"""FastAPI application for Medicare LLM Evaluation System."""

import asyncio
import json
from typing import List
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .database import DatabaseManager
from .test_runner import run_test
from .config import AVAILABLE_MODELS, QUESTIONS_PATH, DATABASE_PATH

# Initialize FastAPI app
app = FastAPI(title="Medicare LLM Evaluation API", version="1.0")

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
db = DatabaseManager(DATABASE_PATH)


# Request models
class TestRunRequest(BaseModel):
    """Request to start a new test run."""
    models: List[str]
    quick_test: bool = False  # If True, only run 1 question for testing


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Medicare LLM Evaluation API",
        "version": "1.0",
        "endpoints": {
            "models": "/api/models",
            "questions": "/api/questions",
            "test_runs": "/api/test-runs",
            "create_test": "/api/test-runs (POST)"
        }
    }


@app.get("/api/models")
async def get_models():
    """Get list of available models."""
    return {
        "models": [
            {
                "id": model_id,
                "name": name,
                "description": f"Test using {name}"
            }
            for name, model_id in AVAILABLE_MODELS.items()
        ]
    }


@app.get("/api/questions")
async def get_questions():
    """Get current question set."""
    try:
        with open(QUESTIONS_PATH, 'r') as f:
            questions_data = json.load(f)
        return questions_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading questions: {str(e)}")


@app.post("/api/test-runs")
async def create_test_run(request: TestRunRequest, background_tasks: BackgroundTasks):
    """
    Start a new test run.

    Runs in the background and returns immediately with the run_id.
    """
    # Validate models
    available_model_ids = list(AVAILABLE_MODELS.values())
    for model in request.models:
        if model not in available_model_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model: {model}. Available models: {available_model_ids}"
            )

    if not request.models:
        raise HTTPException(status_code=400, detail="At least one model must be selected")

    # Start test run in background
    background_tasks.add_task(run_test, request.models, db, request.quick_test)

    # Create the test run record immediately to get run_id
    run_id = db.create_test_run(request.models)

    return {
        "run_id": run_id,
        "status": "running",
        "message": "Test run started"
    }


@app.get("/api/test-runs/{run_id}")
async def get_test_run(run_id: str):
    """Get test run details including status, responses, and aggregates."""
    test_run = db.get_test_run(run_id)

    if not test_run:
        raise HTTPException(status_code=404, detail="Test run not found")

    # Get responses
    responses = db.get_responses(run_id)

    # Calculate aggregates
    aggregates = db.calculate_aggregates(run_id)

    return {
        "test_run": test_run,
        "responses": responses,
        "aggregates": aggregates
    }


@app.get("/api/test-runs/{run_id}/logs")
async def get_test_run_logs(run_id: str):
    """Get logs for a test run."""
    test_run = db.get_test_run(run_id)

    if not test_run:
        raise HTTPException(status_code=404, detail="Test run not found")

    logs = db.get_logs(run_id)

    return {
        "run_id": run_id,
        "logs": logs
    }


@app.get("/api/test-runs")
async def list_test_runs(limit: int = 50, offset: int = 0):
    """List all test runs with pagination."""
    test_runs = db.get_all_test_runs(limit, offset)

    return {
        "test_runs": test_runs,
        "limit": limit,
        "offset": offset
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
