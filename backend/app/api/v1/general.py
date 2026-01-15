from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from typing import Dict, Any

router = APIRouter()


@router.post("/data")
async def submit_data(data: Dict[str, Any], current_user=Depends(get_current_user)):
    """Generic data submission endpoint for frontend forms"""
    # Process and store data as needed
    # In a real implementation, you might save this to database
    return {
        "success": True,
        "message": "Data submitted successfully",
        "received": data,
        "user_id": current_user.id if current_user else None
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "2025-01-15T12:00:00Z"}