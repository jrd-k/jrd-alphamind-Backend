"""API endpoints for position sizing and risk management."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from pydantic import BaseModel, Field

from app.core.security import get_current_user
from app.services.position_sizing import PositionSizer, RiskStrategy, calculate_position_size_simple
from app.services.execution import get_broker_client

router = APIRouter()


class PositionSizeRequest(BaseModel):
    """Request body for calculating position size."""
    symbol: str = Field(..., description="Trading pair (e.g., EURUSD)")
    stop_loss_pips: float = Field(..., ge=0.1, description="Distance in pips to stop-loss")
    account_balance: Optional[float] = Field(None, description="Account balance in USD (if not provided, fetches from broker)")
    leverage: Optional[int] = Field(1, ge=1, le=500, description="Account leverage")
    risk_strategy: str = Field("fixed_risk", description="Strategy: fixed_risk, fixed_lot, kelly, volatility")
    risk_percent: Optional[float] = Field(2.0, ge=0.1, le=10, description="% of account to risk per trade")
    fixed_lot_size: Optional[float] = Field(0.1, description="Fixed lot size (for fixed_lot strategy)")
    min_lot_size: Optional[float] = Field(0.01, description="Minimum lot size")
    max_lot_size: Optional[float] = Field(10.0, description="Maximum lot size")
    current_price: Optional[float] = Field(1.0, description="Current pair price")
    atr: Optional[float] = Field(None, description="Average True Range in pips (for volatility strategy)")
    win_rate: Optional[float] = Field(None, description="Historical win rate as decimal 0-1 (for Kelly)")


class RiskAmountRequest(BaseModel):
    """Request body for reverse calculation: risk amount -> lot size."""
    symbol: str = Field(..., description="Trading pair")
    risk_amount_usd: float = Field(..., gt=0, description="USD amount to risk on this trade")
    stop_loss_pips: float = Field(..., ge=0.1, description="Distance in pips to stop-loss")
    account_balance: Optional[float] = Field(None, description="Account balance in USD")


class MultipleEntriesRequest(BaseModel):
    """Request body for scale-in positions."""
    symbol: str = Field(..., description="Trading pair")
    stop_loss_pips: float = Field(..., ge=0.1, description="Distance in pips to stop-loss")
    num_entries: int = Field(3, ge=1, le=10, description="Number of entries")
    account_balance: Optional[float] = Field(None, description="Account balance in USD")
    risk_strategy: str = Field("fixed_risk", description="Risk strategy")
    risk_percent: Optional[float] = Field(2.0, description="% of account to risk")


@router.post("/calculate")
async def calculate_position_size(
    request: PositionSizeRequest,
    current_user=Depends(get_current_user),
):
    """
    Calculate recommended position size based on risk parameters.

    Strategies:
    - **fixed_risk**: Risk a fixed % of account per trade (recommended for beginners)
    - **fixed_lot**: Use same lot size for all trades
    - **kelly**: Kelly Criterion for optimal long-term growth (requires win_rate)
    - **volatility**: Inverse relationship with market volatility (requires ATR)

    Example request (2% risk, 50 pips stop-loss):
    ```json
    {
        "symbol": "EURUSD",
        "stop_loss_pips": 50,
        "account_balance": 10000,
        "leverage": 1,
        "risk_strategy": "fixed_risk",
        "risk_percent": 2.0
    }
    ```

    Response:
    ```json
    {
        "lot_size": 0.4,
        "position_value_usd": 40000,
        "risk_amount_usd": 200,
        "risk_percent_of_account": 2.0,
        "stop_loss_pips": 50
    }
    ```
    """
    try:
        # Fetch account balance from broker if not provided
        if request.account_balance is None:
            try:
                broker = await get_broker_client()
                account_info = await broker.get_balance()
                account_balance = float(account_info.get("balance", 10000))
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="account_balance required; could not fetch from broker"
                )
        else:
            account_balance = request.account_balance

        # Create position sizer
        sizer = PositionSizer(
            account_balance=account_balance,
            leverage=request.leverage or 1,
            risk_strategy=RiskStrategy(request.risk_strategy),
            risk_percent=request.risk_percent or 2.0,
            fixed_lot_size=request.fixed_lot_size or 0.1,
            min_lot_size=request.min_lot_size or 0.01,
            max_lot_size=request.max_lot_size or 10.0,
        )

        # Calculate lot size
        result = sizer.calculate_lot_size(
            symbol=request.symbol,
            stop_loss_pips=request.stop_loss_pips,
            current_price=request.current_price or 1.0,
            atr=request.atr,
            win_rate=request.win_rate,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.post("/risk-amount")
async def calculate_from_risk_amount(
    request: RiskAmountRequest,
    current_user=Depends(get_current_user),
):
    """
    Reverse calculation: Given a risk amount, calculate lot size.

    Useful when you want to risk a specific USD amount per trade.

    Example request (risk $50 on EURUSD with 50 pips stop):
    ```json
    {
        "symbol": "EURUSD",
        "risk_amount_usd": 50,
        "stop_loss_pips": 50
    }
    ```

    Response:
    ```json
    {
        "lot_size": 0.1,
        "target_risk_usd": 50,
        "actual_risk_usd": 50,
        "risk_percent_of_account": 0.5
    }
    ```
    """
    try:
        # Fetch account balance if not provided
        if request.account_balance is None:
            try:
                broker = await get_broker_client()
                account_info = await broker.get_balance()
                account_balance = float(account_info.get("balance", 10000))
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="account_balance required; could not fetch from broker"
                )
        else:
            account_balance = request.account_balance

        sizer = PositionSizer(account_balance=account_balance)
        result = sizer.calculate_lot_for_risk_amount(
            symbol=request.symbol,
            risk_amount_usd=request.risk_amount_usd,
            stop_loss_pips=request.stop_loss_pips,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scale-in")
async def calculate_scale_in(
    request: MultipleEntriesRequest,
    current_user=Depends(get_current_user),
):
    """
    Calculate scale-in positions (multiple entries).

    Useful for pyramiding strategy: Enter position gradually.

    Example request (3 entries for EURUSD):
    ```json
    {
        "symbol": "EURUSD",
        "stop_loss_pips": 50,
        "num_entries": 3,
        "account_balance": 10000
    }
    ```

    Response:
    ```json
    {
        "total_lot_size": 0.4,
        "entry_lot_size": 0.133,
        "num_entries": 3,
        "entries": [
            {"entry": 1, "lot_size": 0.133, "cumulative_lot": 0.133},
            {"entry": 2, "lot_size": 0.133, "cumulative_lot": 0.267},
            {"entry": 3, "lot_size": 0.133, "cumulative_lot": 0.4}
        ]
    }
    ```
    """
    try:
        # Fetch account balance if not provided
        if request.account_balance is None:
            try:
                broker = await get_broker_client()
                account_info = await broker.get_balance()
                account_balance = float(account_info.get("balance", 10000))
            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="account_balance required; could not fetch from broker"
                )
        else:
            account_balance = request.account_balance

        sizer = PositionSizer(
            account_balance=account_balance,
            risk_strategy=RiskStrategy(request.risk_strategy),
            risk_percent=request.risk_percent or 2.0,
        )

        result = sizer.calculate_multiple_entries(
            symbol=request.symbol,
            stop_loss_pips=request.stop_loss_pips,
            num_entries=request.num_entries,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/simple")
async def simple_calculation(
    symbol: str = Query("EURUSD", description="Trading pair"),
    account_balance: float = Query(..., gt=0, description="Account balance in USD"),
    stop_loss_pips: float = Query(..., ge=0.1, description="Stop-loss distance in pips"),
    risk_percent: float = Query(2.0, ge=0.1, le=10, description="Risk % per trade"),
    current_user=Depends(get_current_user),
):
    """
    Quick calculation: Lot size for fixed % risk strategy.

    Simplest option for traders wanting standard 2% risk rule.

    Example:
    ```
    GET /api/v1/position-sizing/simple?
        symbol=EURUSD&
        account_balance=10000&
        stop_loss_pips=50&
        risk_percent=2.0
    ```

    Response:
    ```json
    {
        "lot_size": 0.4,
        "risk_usd": 200,
        "account_balance": 10000
    }
    ```
    """
    try:
        lot_size = calculate_position_size_simple(
            account_balance=account_balance,
            risk_percent=risk_percent,
            stop_loss_pips=stop_loss_pips,
            symbol=symbol,
        )

        return {
            "symbol": symbol,
            "lot_size": round(lot_size, 3),
            "risk_usd": round(account_balance * (risk_percent / 100), 2),
            "account_balance": account_balance,
            "risk_percent": risk_percent,
            "stop_loss_pips": stop_loss_pips,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
