"""Trade Orchestration API - Complete trading workflow endpoint.

Unified endpoint that combines:
- Brain signal generation (AI + indicators)
- Position sizing calculation
- Risk management checks
- Order execution (optional)
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field

from app.core.security import get_current_user
from app.services.trade_orchestrator import TradeOrchestrator

router = APIRouter()
orchestrator = TradeOrchestrator()


class CandleData(BaseModel):
    """OHLCV candle data."""

    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class IndicatorInput(BaseModel):
    """Pre-computed indicator signal."""

    source: str = Field(..., description="Indicator name (RSI, MACD, etc.)")
    signal: str = Field(..., description="BUY, SELL, or HOLD")
    value: Optional[float] = Field(None, description="Indicator value")


class TradeAnalysisRequest(BaseModel):
    """Request for trade analysis (no execution)."""

    symbol: str = Field(..., description="Trading pair (e.g., EURUSD)")
    candles: Optional[List[CandleData]] = Field(
        None, description="OHLCV data for Brain analysis"
    )
    current_price: Optional[float] = Field(None, description="Current market price")
    indicators: Optional[List[IndicatorInput]] = Field(
        None, description="Pre-computed indicator signals"
    )
    account_balance: Optional[float] = Field(
        None, description="Account balance in USD (auto-fetches from broker if not provided)"
    )
    stop_loss_pips: Optional[float] = Field(
        None, description="Distance in pips to stop-loss (default 50)"
    )
    risk_strategy: str = Field(
        "fixed_risk",
        description="Position sizing strategy: fixed_risk, fixed_lot, kelly, volatility",
    )
    risk_percent: float = Field(
        2.0, ge=0.1, le=10, description="% of account to risk per trade"
    )
    leverage: int = Field(1, ge=1, le=500, description="Account leverage")
    existing_positions: Optional[List[Dict[str, Any]]] = Field(
        None, description="Current open positions for correlation check"
    )
    pending_positions: Optional[List[Dict[str, Any]]] = Field(
        None, description="Pending positions to consider in the same request"
    )
    requested_qty: Optional[float] = Field(
        None, description="Explicit lot size to use (overrides sizing calculations)"
    )
    order_id: Optional[str] = Field(
        None, description="Order ID to associate with the trade"
    )


class TradeExecutionRequest(TradeAnalysisRequest):
    """Request for trade execution (analysis + order placement)."""

    auto_execute: bool = Field(
        True, description="If true, place order if all checks pass"
    )


class TradeAnalysisResponse(BaseModel):
    """Complete trade analysis response."""

    symbol: str
    timestamp: str
    workflow: Dict[str, Any]
    decision: str  # PROCEED, HOLD, REJECT
    can_execute: bool
    lot_size: float
    risk_level: str  # SAFE, WARNING, CRITICAL
    reasons: List[str]
    warnings: List[str]
    execution_result: Optional[Dict[str, Any]]
    execution_time_ms: float


@router.post(
    "/analyze",
    response_model=TradeAnalysisResponse,
    summary="Analyze trade without executing",
    description="Run complete trade analysis: Brain signal → Position sizing → Risk checks. Does not execute order.",
)
async def analyze_trade(
    request: TradeAnalysisRequest,
    current_user=Depends(get_current_user),
) -> TradeAnalysisResponse:
    """
    Analyze a potential trade WITHOUT executing.

    **Workflow:**
    1. Generate Brain signal (indicators + AI)
    2. Calculate optimal position size
    3. Run 7 comprehensive risk checks
    4. Return detailed analysis

    **Returns:**
    - `decision`: PROCEED/HOLD/REJECT
    - `can_execute`: true if all checks pass
    - `lot_size`: calculated position size
    - `risk_level`: SAFE/WARNING/CRITICAL
    - Detailed reasons and warnings
    """
    try:
        result = await orchestrator.analyze_trade(
            symbol=request.symbol,
            candles=[c.dict() for c in request.candles] if request.candles else None,
            current_price=request.current_price,
            indicators=(
                [i.dict() for i in request.indicators] if request.indicators else None
            ),
            account_balance=request.account_balance,
            stop_loss_pips=request.stop_loss_pips,
            risk_strategy=request.risk_strategy,
            risk_percent=request.risk_percent,
            leverage=request.leverage,
            existing_positions=request.existing_positions,
            pending_positions=request.pending_positions,
            requested_qty=request.requested_qty,
            order_id=request.order_id,
        )
        return TradeAnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/execute",
    response_model=TradeAnalysisResponse,
    summary="Analyze and execute trade",
    description="Run complete trade analysis and execute order if all checks pass.",
)
async def execute_trade(
    request: TradeExecutionRequest,
    current_user=Depends(get_current_user),
) -> TradeAnalysisResponse:
    """
    Analyze a potential trade AND execute if all checks pass.

    **Workflow:**
    1. Generate Brain signal (indicators + AI)
    2. Calculate optimal position size
    3. Run 7 comprehensive risk checks
    4. Execute order if can_execute=true
    5. Return full execution details

    **Returns:**
    - Complete analysis + execution_result with order confirmation

    **Example Request:**
    ```json
    {
      "symbol": "EURUSD",
      "current_price": 1.0835,
      "stop_loss_pips": 50,
      "risk_strategy": "fixed_risk",
      "risk_percent": 2.0,
      "auto_execute": true
    }
    ```

    **Example Response:**
    ```json
    {
      "symbol": "EURUSD",
      "decision": "PROCEED",
      "can_execute": true,
      "lot_size": 0.4,
      "risk_level": "SAFE",
      "workflow": {
        "brain_signal": {"decision": "BUY", ...},
        "position_sizing": {"lot_size": 0.4, ...},
        "risk_checks": {...},
      },
      "execution_result": {
        "order_id": 42,
        "status": "filled"
      }
    }
    ```
    """
    try:
        result = await orchestrator.orchestrate_trade(
            symbol=request.symbol,
            candles=[c.dict() for c in request.candles] if request.candles else None,
            current_price=request.current_price,
            indicators=(
                [i.dict() for i in request.indicators] if request.indicators else None
            ),
            account_balance=request.account_balance,
            stop_loss_pips=request.stop_loss_pips,
            risk_strategy=request.risk_strategy,
            risk_percent=request.risk_percent,
            leverage=request.leverage,
            existing_positions=request.existing_positions,
            pending_positions=request.pending_positions,
            requested_qty=request.requested_qty,
            order_id=request.order_id,
            user_id=current_user.id,
            auto_execute=request.auto_execute,
        )
        return TradeAnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/quick-analyze",
    response_model=Dict[str, Any],
    summary="Quick trade analysis (simplified)",
    description="Fast trade analysis with minimal parameters",
)
async def quick_analyze(
    symbol: str = Query(..., description="Trading pair"),
    current_price: float = Query(..., description="Current market price"),
    stop_loss_pips: float = Query(50, description="Distance to stop-loss"),
    account_balance: Optional[float] = Query(
        None, description="Account balance (auto-fetches if not provided)"
    ),
    risk_percent: float = Query(2.0, ge=0.1, le=10),
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Quick trade analysis with minimal parameters.

    Perfect for rapid decision-making or webhook-triggered analysis.

    **Example:**
    ```
    GET /api/v1/orchestrator/quick-analyze?
      symbol=EURUSD&
      current_price=1.0835&
      stop_loss_pips=50&
      risk_percent=2.0
    ```
    """
    try:
        result = await orchestrator.analyze_trade(
            symbol=symbol,
            current_price=current_price,
            account_balance=account_balance,
            stop_loss_pips=stop_loss_pips,
            risk_percent=risk_percent,
        )

        # Simplified response
        return {
            "symbol": result["symbol"],
            "decision": result["decision"],
            "can_execute": result["can_execute"],
            "lot_size": result["lot_size"],
            "risk_level": result["risk_level"],
            "summary": " | ".join(result["reasons"])
            if result["reasons"]
            else "All checks passed",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
