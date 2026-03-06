from fastapi import APIRouter, HTTPException
from typing import Dict
import uuid

router = APIRouter()

sessions: Dict[str, Dict] = {}

@router.post("/", response_model=dict)
def create_session():
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "step": "upload",
        "image": None,
        "analysis_data": None,
        "questions": [],
        "user_answers": [],
        "portion_estimates": None,
        "nutrition_summary": None,
        "recommendations": None
    }
    return {"session_id": session_id}

@router.delete("/{session_id}")
def delete_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
        return {"message": "Session deleted"}
    raise HTTPException(status_code=404, detail="Session not found")

@router.get("/{session_id}")
def get_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    # Filter out non-serializable objects (e.g. PIL Image) from session data
    session_data = {}
    for key, value in sessions[session_id].items():
        try:
            import json
            json.dumps(value)  # Test serializability
            session_data[key] = value
        except (TypeError, ValueError):
            session_data[key] = str(type(value).__name__) if value is not None else None
    return {"session_id": session_id, "data": session_data}