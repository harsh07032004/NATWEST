from fastapi import APIRouter
from src.core.model_handler import model_handler

router = APIRouter()

@router.post("/compute")
def compute(payload: dict):
    """Primary endpoint called by the Node.js orchestrator."""
    return model_handler(payload)

@router.post("/analyze")
def analyze(payload: dict):
    """Alias for /compute — both route to the same deterministic math engine."""
    return model_handler(payload)