from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from app.models import (
    FailureInfo,
    Experience,
    AnalyseRequest,
    AnalyseResponse,
    OutcomeUpdateRequest
)
from app.config import ACTIVE_BANK_ID, LOCAL_STORE_PATH
from app.hindsight_service import HindsightService
from app.experience_store import ExperienceStore
from app.relevance import RelevanceFilter
from app.learning_engine import LearningEngine

app = FastAPI(
    title="Experience-Driven CI Failure Resolution Agent API",
    version="1.0.0",
    description="Backend service for CI failure analysis and empirical experience-driven recommendations"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services
hindsight_service = HindsightService()
experience_store = ExperienceStore(storage_path=LOCAL_STORE_PATH)

@app.get("/api/health")
def health_check():
    """Health check endpoint confirming service and Hindsight bank status."""
    try:
        hindsight_status = hindsight_service.health_check()
    except Exception as e:
        hindsight_status = {"status": "error", "error": str(e)}

    return {
        "status": "healthy",
        "active_bank": ACTIVE_BANK_ID,
        "hindsight": hindsight_status,
        "stored_experiences_count": len(experience_store.list_all())
    }

@app.post("/api/analyse", response_model=AnalyseResponse)
def analyse_failure(req: AnalyseRequest):
    """
    Analyse a CI failure.
    If memory_enabled=False: DO NOT call Hindsight recall(); return baseline diagnosis.
    If memory_enabled=True: Call Hindsight recall(), apply relevance filtering,
    compare outcomes, and synthesize experience-driven recommendation.
    """
    failure = req.failure

    if not req.memory_enabled:
        # Strict requirement: Do NOT call Hindsight recall() when memory is OFF
        return LearningEngine.synthesize(
            current_failure=failure,
            recalled_items=[],
            memory_enabled=False
        )

    # Memory is ON: Query Hindsight TEMPR retrieval engine
    search_query = (
        f"CI failure in {failure.repository} workflow {failure.workflow}: "
        f"{failure.failure_signature} {failure.error_type} {failure.error_message}"
    )

    try:
        raw_memories = hindsight_service.recall_memories(query=search_query)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to query Hindsight memory bank: {str(e)}"
        )

    # Apply relevance scoring and operational filtering
    scored_memories = RelevanceFilter.filter_and_rank(
        raw_memories=raw_memories,
        current_failure=failure
    )

    # Synthesize outcome-based recommendation
    response = LearningEngine.synthesize(
        current_failure=failure,
        recalled_items=scored_memories,
        memory_enabled=True
    )

    return response

@app.post("/api/experience")
def record_experience(exp: Experience):
    """Store a completed CI experience locally and retain in Hindsight."""
    # 1. Store in local experience store
    saved_exp = experience_store.add(exp)

    # 2. Retain in Hindsight development bank
    try:
        retain_result = hindsight_service.retain_experience(saved_exp)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to retain experience in Hindsight: {str(e)}"
        )

    return {
        "status": "recorded",
        "experience": saved_exp,
        "hindsight_retain": retain_result
    }

@app.get("/api/experiences", response_model=List[Experience])
def list_experiences():
    """Retrieve all stored CI experiences."""
    return experience_store.list_all()

@app.post("/api/experiences/{experience_id}/outcome")
def update_outcome(experience_id: str, outcome: OutcomeUpdateRequest):
    """
    Update an existing experience with the engineer's action, outcome result,
    resolution, and lesson learned, then retain the updated knowledge in Hindsight.
    """
    updated_exp = experience_store.update_outcome(experience_id, outcome)
    if not updated_exp:
        raise HTTPException(
            status_code=404,
            detail=f"Experience with ID '{experience_id}' not found."
        )

    # Retain the updated experience with its confirmed outcome in Hindsight
    try:
        retain_result = hindsight_service.retain_experience(updated_exp)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to retain updated experience in Hindsight: {str(e)}"
        )

    return {
        "status": "outcome_updated",
        "experience": updated_exp,
        "hindsight_retain": retain_result
    }

# Serve built frontend if available
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

_dist_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
if os.path.exists(_dist_dir):
    _assets_dir = os.path.join(_dist_dir, "assets")
    if os.path.exists(_assets_dir):
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")

    @app.get("/")
    def serve_frontend_root():
        index_file = os.path.join(_dist_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "Experience-Driven CI Failure Resolution Agent API is online."}

