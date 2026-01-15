from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user
from app.models.orm_models import User
from typing import Dict, Any

router = APIRouter()


@router.get("/", dependencies=[Depends(get_current_user)])
async def list_users():
    """List all users (admin endpoint)"""
    return [{"id": 1, "username": "alice"}]


@router.get("/{user_id}", dependencies=[Depends(get_current_user)])
async def get_user(user_id: int):
    """Get user by ID"""
    return {"id": user_id, "username": "user"}


@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile - Frontend compatible endpoint"""
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.username,  # Using username as email for simplicity
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "is_active": True
    }
