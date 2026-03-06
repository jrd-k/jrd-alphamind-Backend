from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user
from app.models.orm_models import User
from typing import Dict, Any, Optional
from pydantic import BaseModel

router = APIRouter()


class UserSettingsModel(BaseModel):
    """User settings schema"""
    theme: Optional[str] = "light"
    defaultSymbol: Optional[str] = "EURUSD"
    defaultTimeframe: Optional[str] = "1h"
    notifications: Optional[Dict[str, Any]] = None
    riskSettings: Optional[Dict[str, Any]] = None


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


@router.get("/settings", response_model=Dict[str, Any])
async def get_user_settings(current_user: User = Depends(get_current_user)):
    """Get current user settings - Returns default settings"""
    return {
        "theme": "light",
        "defaultSymbol": "EURUSD",
        "defaultTimeframe": "1h",
        "notifications": {
            "email": True,
            "browser": True,
            "tradeAlerts": True,
            "priceAlerts": False,
        },
        "riskSettings": {
            "maxDrawdown": 5,
            "maxDailyLoss": 100,
            "defaultRiskPerTrade": 1,
        }
    }


@router.put("/settings", response_model=Dict[str, Any])
async def update_user_settings(
    settings: UserSettingsModel,
    current_user: User = Depends(get_current_user)
):
    """Update current user settings"""
    # In a production system, you would persist these settings to the database
    # For now, we'll just return success response
    return {
        "message": "Settings updated successfully",
        "settings": {
            "theme": settings.theme or "light",
            "defaultSymbol": settings.defaultSymbol or "EURUSD",
            "defaultTimeframe": settings.defaultTimeframe or "1h",
            "notifications": settings.notifications or {},
            "riskSettings": settings.riskSettings or {}
        }
    }


@router.get("/", dependencies=[Depends(get_current_user)])
async def list_users():
    """List all users (admin endpoint)"""
    return [{"id": 1, "username": "alice"}]


@router.get("/{user_id}", dependencies=[Depends(get_current_user)])
async def get_user(user_id: int):
    """Get user by ID"""
    return {"id": user_id, "username": "user"}
