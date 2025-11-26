"""API endpoints for risk management."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel, Field

from app.core.security import get_current_user
from app.services.risk_manager import RiskManager, RiskLevel
from app.services.execution import get_broker_client

router = APIRouter()


class RiskCheckRequest(BaseModel):
    """Request body for comprehensive risk check."""
    symbol: str = Field(..., description="Trading pair")
    qty: float = Field(..., gt=0, description="Order quantity")
    entry_price: float = Field(..., gt=0, description="Entry price")
    stop_loss_price: float = Field(..., description="Stop-loss price")
    account_balance: Optional[float] = Field(None, description="Account balance")
    current_equity: Optional[float] = Field(None, description="Current equity")
    margin_available: Optional[float] = Field(None, description="Available margin")
    current_positions: Optional[List[dict]] = Field(None, description="List of open positions")
    max_daily_loss_pct: Optional[float] = Field(5.0, ge=0.1, le=50, description="Max daily loss %")
    max_drawdown_pct: Optional[float] = Field(15.0, ge=0.1, le=50, description="Max drawdown %")


class RiskOfRuinRequest(BaseModel):
    """Request body for risk of ruin calculation."""
    win_rate: float = Field(..., ge=0.01, le=0.99, description="Win rate as decimal (0-1)")
    avg_win_pct: float = Field(..., gt=0, le=10, description="Average win size (% of account)")
    avg_loss_pct: float = Field(..., gt=0, le=10, description="Average loss size (% of account)")
    trade_count: int = Field(100, ge=1, le=1000, description="Trades to project")


@router.post("/check")
async def check_trade_risk(
    request: RiskCheckRequest,
    current_user=Depends(get_current_user),
):
    """
    Run comprehensive risk checks before executing a trade.

    Checks:
    - Daily loss limit
    - Account drawdown
    - Position size limits
    - Margin requirements
    - Correlation with existing positions
    - Stop-loss validity

    Example request:
    ```json
    {
        "symbol": "EURUSD",
        "qty": 0.1,
        "entry_price": 1.0835,
        "stop_loss_price": 1.0785,
        "account_balance": 10000,
        "current_positions": []
    }
    ```

    Response includes pass/fail for each check.
    """
    try:
        # Fetch account info if not provided
        account_balance = request.account_balance
        if account_balance is None:
            try:
                broker = await get_broker_client()
                account_info = await broker.get_balance()
                account_balance = float(account_info.get("balance", 10000))
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="account_balance required; could not fetch from broker"
                )

        # Create risk manager
        rm = RiskManager(
            account_balance=account_balance,
            max_daily_loss_pct=request.max_daily_loss_pct or 5.0,
            max_drawdown_pct=request.max_drawdown_pct or 15.0,
        )

        # Run all checks
        results = rm.check_all_risks(
            symbol=request.symbol,
            qty=request.qty,
            entry_price=request.entry_price,
            stop_loss_price=request.stop_loss_price,
            current_positions=request.current_positions or [],
            current_equity=request.current_equity,
            margin_available=request.margin_available,
        )

        # Convert results to dict
        checks = []
        overall_level = RiskLevel.SAFE
        for result in results:
            checks.append({
                "level": result.level.value,
                "message": result.message,
                "details": result.details,
            })
            # Update overall level (worse case wins)
            if result.level == RiskLevel.CRITICAL:
                overall_level = RiskLevel.CRITICAL
            elif result.level == RiskLevel.WARNING and overall_level != RiskLevel.CRITICAL:
                overall_level = RiskLevel.WARNING

        return {
            "symbol": request.symbol,
            "overall_level": overall_level.value,
            "can_trade": overall_level != RiskLevel.CRITICAL,
            "checks": checks,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/daily-stats")
async def get_daily_statistics(
    account_balance: float = Query(..., gt=0, description="Account balance"),
    current_user=Depends(get_current_user),
):
    """
    Get daily trading statistics and risk metrics.

    Returns:
    - Daily P&L
    - Daily loss percentage
    - Number of trades today
    - Largest win/loss
    """
    try:
        rm = RiskManager(account_balance=account_balance)
        stats = rm.get_daily_stats()
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/risk-of-ruin")
async def calculate_risk_of_ruin(
    request: RiskOfRuinRequest,
    current_user=Depends(get_current_user),
):
    """
    Calculate probability of account ruin based on trading statistics.

    Uses Kelly Criterion and Gambler's Ruin formula.

    Example:
    - Win rate: 60%
    - Avg win: 1.5% of account
    - Avg loss: 1% of account
    - Projects over 100 trades

    Response includes:
    - Kelly fraction (optimal sizing)
    - Conservative Kelly/2
    - Risk of ruin probability
    - Trading system verdict

    High risk of ruin means: Adjust position sizing or improve win rate!
    """
    try:
        rm = RiskManager(account_balance=10000)  # Dummy balance for calc
        result = rm.calculate_risk_of_ruin(
            win_rate=request.win_rate,
            avg_win_pct=request.avg_win_pct,
            avg_loss_pct=request.avg_loss_pct,
            trade_count=request.trade_count,
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/margin-check")
async def check_margin_requirements(
    symbol: str = Query(..., description="Trading pair"),
    qty: float = Query(..., gt=0, description="Position quantity"),
    price: float = Query(..., gt=0, description="Current price"),
    account_balance: float = Query(..., gt=0, description="Account balance"),
    current_user=Depends(get_current_user),
):
    """
    Calculate margin requirements for a position.

    Returns required margin and usage percentage.

    Example:
    ```
    GET /api/v1/risk/margin-check?
        symbol=EURUSD&
        qty=1.0&
        price=1.0835&
        account_balance=10000
    ```
    """
    try:
        rm = RiskManager(account_balance=account_balance)
        position_value = qty * price
        
        margin_req_pct = rm.MARGIN_REQUIREMENTS.get(symbol, 2.0)
        required_margin = position_value * (margin_req_pct / 100)
        margin_available = account_balance - required_margin
        margin_usage_pct = (required_margin / account_balance) * 100

        return {
            "symbol": symbol,
            "quantity": qty,
            "price": price,
            "position_value": round(position_value, 2),
            "margin_requirement_pct": margin_req_pct,
            "required_margin": round(required_margin, 2),
            "account_balance": account_balance,
            "margin_available": round(margin_available, 2),
            "margin_usage_pct": round(margin_usage_pct, 2),
            "can_open": margin_available > 0,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/correlation")
async def check_pair_correlation(
    pair1: str = Query(..., description="First trading pair"),
    pair2: str = Query(..., description="Second trading pair"),
    current_user=Depends(get_current_user),
):
    """
    Check correlation between two trading pairs.

    Returns correlation value (-1 to 1):
    - 0.7+ : High positive correlation (move together)
    - -0.7- : High negative correlation (move opposite)
    - Near 0: Low correlation (independent)
    """
    try:
        rm = RiskManager(account_balance=10000)
        pair_key = tuple(sorted([pair1.upper(), pair2.upper()]))
        
        correlation = rm.PAIR_CORRELATIONS.get(pair_key)

        if correlation is None:
            return {
                "pair1": pair1,
                "pair2": pair2,
                "correlation": None,
                "message": "Correlation data not available",
            }

        # Interpret correlation
        abs_corr = abs(correlation)
        if abs_corr > 0.7:
            interpretation = "High correlation"
        elif abs_corr > 0.4:
            interpretation = "Moderate correlation"
        else:
            interpretation = "Low correlation"

        if correlation > 0:
            direction = "Positive (move together)"
        else:
            direction = "Negative (move opposite)"

        return {
            "pair1": pair1,
            "pair2": pair2,
            "correlation": round(correlation, 3),
            "interpretation": interpretation,
            "direction": direction,
            "recommended": "Avoid opening both positions simultaneously" if abs_corr > 0.7 else "OK to open both",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
