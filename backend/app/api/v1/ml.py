"""ML Trading API endpoints for frontend integration."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime

from app.services.ml import MLTradingService, MLDataLoader
from app.core.security import get_current_user

router = APIRouter(tags=["ml"])


class MLTrainingRequest(BaseModel):
    symbol: str
    days: int = 365
    force_retrain: bool = False


class MLPredictionRequest(BaseModel):
    symbol: str
    current_price: float
    features: Optional[Dict[str, Any]] = None


class MLTrainingResponse(BaseModel):
    symbol: str
    status: str
    training_results: Optional[Dict[str, Any]] = None
    validation_results: Optional[Dict[str, Any]] = None
    message: str


class MLPredictionResponse(BaseModel):
    symbol: str
    prediction: int  # 0 = no trade, 1 = long, 2 = short
    confidence: float
    features_used: List[str]
    timestamp: datetime


# Global ML service instance (in production, use dependency injection)
ml_service = MLTradingService()
data_loader = MLDataLoader()


@router.post("/train", response_model=MLTrainingResponse)
async def train_ml_model(
    request: MLTrainingRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user)
):
    """Train ML model for a specific symbol."""
    try:
        # Load historical data
        historical_data = await data_loader.generate_sample_data(
            symbol=request.symbol,
            timeframe='H1',
            days=request.days
        )

        if historical_data.empty:
            raise HTTPException(status_code=400, detail="No historical data available")

        # Train model in background
        background_tasks.add_task(
            ml_service.train_model,
            historical_data,
            request.symbol,
            request.force_retrain
        )

        return MLTrainingResponse(
            symbol=request.symbol,
            status="training_started",
            message=f"Training started for {request.symbol} with {len(historical_data)} data points"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.post("/predict", response_model=MLPredictionResponse)
async def get_ml_prediction(
    request: MLPredictionRequest,
    current_user=Depends(get_current_user)
):
    """Get ML prediction for current market conditions."""
    try:
        # Check if model exists for symbol
        if request.symbol not in ml_service.trained_models:
            raise HTTPException(
                status_code=404,
                detail=f"No trained model available for {request.symbol}"
            )

        # Generate features from current market data
        market_data = {
            'close': request.current_price,
            'timestamp': datetime.now(),
            'symbol': request.symbol
        }

        # Add any additional features provided
        if request.features:
            market_data.update(request.features)

        # Get ML prediction (this would integrate with the execution engine)
        # For now, return mock prediction
        prediction = {
            'symbol': request.symbol,
            'prediction': 1,  # Long signal
            'confidence': 0.75,
            'features_used': ['close', 'volume', 'rsi'],
            'timestamp': datetime.now()
        }

        return MLPredictionResponse(**prediction)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/status")
async def get_ml_status(current_user=Depends(get_current_user)):
    """Get ML service status."""
    try:
        status = ml_service.get_service_status()
        return {
            "service_status": status,
            "available_symbols": list(ml_service.trained_models.keys()),
            "total_models": len(ml_service.trained_models)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.get("/performance/{symbol}")
async def get_ml_performance(
    symbol: str,
    current_user=Depends(get_current_user)
):
    """Get ML model performance metrics."""
    try:
        performance = await ml_service.get_model_performance(symbol)

        if not performance:
            raise HTTPException(
                status_code=404,
                detail=f"No performance data available for {symbol}"
            )

        return performance

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance check failed: {str(e)}")


@router.get("/execution/stats")
async def get_execution_stats(current_user=Depends(get_current_user)):
    """Get ML execution statistics."""
    try:
        stats = await ml_service.get_execution_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution stats failed: {str(e)}")


@router.post("/start-trading")
async def start_live_trading(current_user=Depends(get_current_user)):
    """Start live ML trading."""
    try:
        success = await ml_service.start_live_trading()

        if success:
            return {"status": "started", "message": "Live ML trading started"}
        else:
            raise HTTPException(status_code=400, detail="Failed to start live trading")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Start trading failed: {str(e)}")


@router.post("/stop-trading")
async def stop_live_trading(current_user=Depends(get_current_user)):
    """Stop live ML trading."""
    try:
        success = await ml_service.stop_live_trading()

        if success:
            return {"status": "stopped", "message": "Live ML trading stopped"}
        else:
            raise HTTPException(status_code=400, detail="Failed to stop live trading")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stop trading failed: {str(e)}")


@router.get("/models")
async def list_trained_models(current_user=Depends(get_current_user)):
    """List all trained ML models."""
    try:
        models_info = []

        for symbol, model_info in ml_service.trained_models.items():
            models_info.append({
                "symbol": symbol,
                "trained_at": model_info.get("trained_at"),
                "data_points": model_info.get("data_points", 0),
                "feature_count": model_info.get("feature_count", 0),
                "best_score": model_info.get("training_results", {}).get("best_score", 0)
            })

        return {
            "total_models": len(models_info),
            "models": models_info
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model listing failed: {str(e)}")