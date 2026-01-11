"""Trade Orchestrator: Unified workflow combining Brain signals, Position Sizing, and Risk Management.

This module provides a complete, production-ready trading workflow:
1. Get trading signal from Brain (AI + indicators)
2. Calculate optimal position size
3. Run comprehensive risk checks
4. Execute order if all checks pass
5. Return detailed pre-trade analysis
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from app.services.brain.brain import Brain
from app.services.position_sizing import PositionSizer, RiskStrategy
from app.services.risk_manager import RiskManager, RiskLevel
from app.services.execution import execute_order
from app.core.config import settings

logger = logging.getLogger(__name__)


class TradeOrchestrator:
    """Orchestrates complete trading workflow from signal to execution."""

    def __init__(self):
        self.brain = Brain()

    async def orchestrate_trade(
        self,
        symbol: str,
        candles: Optional[List[Dict[str, Any]]] = None,
        current_price: Optional[float] = None,
        indicators: Optional[List[Dict[str, Any]]] = None,
        account_balance: Optional[float] = None,
        stop_loss_pips: Optional[float] = None,
        risk_strategy: str = "fixed_risk",
        risk_percent: float = 2.0,
        leverage: int = 1,
        existing_positions: Optional[List[Dict[str, Any]]] = None,
        pending_positions: Optional[List[Dict[str, Any]]] = None,
        requested_qty: Optional[float] = None,
        order_id: Optional[str] = None,
        user_id: Optional[int] = None,
        auto_execute: bool = False,
    ) -> Dict[str, Any]:
        """
        Complete orchestrated trade workflow.

        Args:
            symbol: Trading pair (e.g., EURUSD)
            candles: OHLCV data for Brain analysis
            current_price: Current market price
            indicators: Pre-computed indicators
            account_balance: Account balance in USD
            stop_loss_pips: Distance in pips to stop-loss
            risk_strategy: Position sizing strategy
            risk_percent: % of account to risk
            leverage: Account leverage
            existing_positions: Current open positions
            user_id: User ID for trade tracking
            auto_execute: If True, execute order if all checks pass

        Returns:
            Dict with complete trade analysis:
            {
                "symbol": str,
                "timestamp": str,
                "workflow": {
                    "brain_signal": {...},
                    "position_sizing": {...},
                    "risk_checks": {...},
                    "execution": {...}
                },
                "decision": "PROCEED" | "HOLD" | "REJECT",
                "can_execute": bool,
                "lot_size": float,
                "risk_level": str,
                "reasons": [str],
                "warnings": [str],
                "execution_result": {...} if auto_execute
            }
        """
        start_time = datetime.now(timezone.utc)
        result = {
            "symbol": symbol,
            "timestamp": start_time.isoformat(),
            "workflow": {},
            "decision": "HOLD",
            "can_execute": False,
            "lot_size": 0.0,
            "risk_level": "SAFE",
            "reasons": [],
            "warnings": [],
            "execution_result": None,
        }

        try:
            # ===== STEP 1: Get Brain Signal =====
            logger.info(f"[{symbol}] Step 1: Getting Brain signal...")
            try:
                brain_signal = await self.brain.decide(
                    symbol=symbol,
                    candles=candles,
                    current_price=current_price,
                    indicators=indicators,
                )
                result["workflow"]["brain_signal"] = brain_signal
                result["decision"] = brain_signal.get("decision", "HOLD")

                # Check confidence threshold - reject if below minimum
                confidence = brain_signal.get("confidence", 0.0)
                if confidence < settings.brain_min_confidence and brain_signal.get("decision") != "HOLD":
                    result["reasons"].append(f"Brain confidence {confidence:.2f} below minimum threshold {settings.brain_min_confidence}")
                    result["decision"] = "HOLD"
                    return result

                if brain_signal.get("decision") == "HOLD":
                    result["reasons"].append("Brain signal is HOLD")
                    return result

                logger.info(f"[{symbol}] Brain signal: {brain_signal['decision']} (confidence: {confidence:.2f})")
            except Exception as e:
                logger.exception(f"[{symbol}] Brain decision failed: {e}")
                result["reasons"].append(f"Brain decision failed: {e}")
                return result

            # ===== STEP 2: Calculate Position Size =====
            logger.info(f"[{symbol}] Step 2: Calculating position size...")
            try:
                sizer = PositionSizer(
                    account_balance=account_balance or 0.0,
                    leverage=leverage,
                    risk_strategy=RiskStrategy[risk_strategy.upper()],
                    risk_percent=risk_percent,
                )

                if not stop_loss_pips:
                    result["warnings"].append("Stop-loss not provided, using default 50 pips")
                    stop_loss_pips = 50

                # If caller provided an explicit requested_qty, use that instead of sizing
                # (the orders endpoint will pass requested_qty when user supplies quantity)
                if requested_qty and requested_qty > 0:
                    lot_size = requested_qty
                    size_result = {"lot_size": lot_size}
                else:
                    size_result = sizer.calculate_lot_size(
                        symbol=symbol,
                        stop_loss_pips=stop_loss_pips,
                        current_price=current_price or 1.0,
                    )
                    lot_size = size_result.get("lot_size", 0.0)

                # Leverage safety: warn when leverage is high and scale down sizing for safety
                if leverage and leverage > 20 and lot_size:
                    result["warnings"].append(
                        f"High leverage ({leverage}x) detected — limiting effective sizing to 20x equivalent"
                    )
                    # scale factor to reduce risk when leverage > 20
                    scale = 20.0 / float(leverage)
                    lot_size = round(float(lot_size) * scale, 5)
                    size_result["lot_size"] = lot_size

                result["workflow"]["position_sizing"] = {
                    "lot_size": lot_size,
                    "stop_loss_pips": stop_loss_pips,
                    "risk_strategy": risk_strategy,
                    "risk_percent": risk_percent,
                    "leverage": leverage,
                }
                result["lot_size"] = lot_size

                logger.info(f"[{symbol}] Position size: {lot_size} lots")
            except Exception as e:
                logger.exception(f"[{symbol}] Position sizing failed: {e}")
                result["reasons"].append(f"Position sizing failed: {e}")
                return result

            # ===== STEP 3: Run Risk Checks =====
            logger.info(f"[{symbol}] Step 3: Running risk checks...")
            try:
                rm = RiskManager(account_balance=account_balance or 10000)

                # Calculate stop-loss price (assume entry at current_price)
                if current_price:
                    if brain_signal.get("decision") == "BUY":
                        stop_loss_price = current_price - (stop_loss_pips * 0.0001)
                    else:  # SELL
                        stop_loss_price = current_price + (stop_loss_pips * 0.0001)
                else:
                    stop_loss_price = current_price or 1.0

                risk_checks = rm.check_all_risks(
                    symbol=symbol,
                    qty=lot_size,
                    entry_price=current_price or 1.0,
                    stop_loss_price=stop_loss_price,
                    current_positions=existing_positions or [],
                )

                result["workflow"]["risk_checks"] = {
                    "checks": [
                        {
                            "name": check.details.get("check_type", "unknown"),
                            "level": check.level.value,
                            "message": check.message,
                        }
                        for check in risk_checks
                    ],
                }

                # Get overall risk level
                risk_levels = [check.level for check in risk_checks]
                # Sort by severity: SAFE (0) < WARNING (1) < CRITICAL (2)
                if risk_levels:
                    max_level = risk_levels[0]
                    for level in risk_levels:
                        if level.value > max_level.value:
                            max_level = level
                    overall_level = max_level
                else:
                    overall_level = RiskLevel.SAFE
                
                result["workflow"]["risk_checks"]["overall_level"] = overall_level.value
                result["risk_level"] = overall_level.value

                # Extract warnings and failure reasons
                for check in risk_checks:
                    if check.level == RiskLevel.WARNING:
                        result["warnings"].append(f"{check.message}")
                    elif check.level == RiskLevel.CRITICAL:
                        result["reasons"].append(f"CRITICAL: {check.message}")

                logger.info(f"[{symbol}] Risk level: {overall_level.value}")

                # Can only execute if no critical risks
                result["can_execute"] = all(
                    check.level != RiskLevel.CRITICAL for check in risk_checks
                )

                if not result["can_execute"]:
                    result["decision"] = "REJECT"
                    return result

            except Exception as e:
                logger.exception(f"[{symbol}] Risk checks failed: {e}")
                result["reasons"].append(f"Risk checks failed: {e}")
                return result

            # ===== STEP 4: Execute Order (if approved) =====
            if auto_execute and result["can_execute"]:
                logger.info(f"[{symbol}] Step 4: Executing order...")
                try:
                    # Determine side from brain signal
                    side = "buy" if brain_signal.get("decision") == "BUY" else "sell"

                    order = {
                        "symbol": symbol,
                        "side": side,
                        "qty": lot_size,
                        "price": 0.0,  # Market order
                        "order_id": order_id,
                        "user_id": user_id,
                        "metadata": {
                            "orchestrated": True,
                            "brain_signal": brain_signal.get("decision"),
                            "risk_level": result["risk_level"],
                            "strategy": risk_strategy,
                        },
                    }

                    exec_result = await execute_order(order)
                    result["execution_result"] = exec_result
                    result["decision"] = "PROCEED"

                    logger.info(f"[{symbol}] Order executed: {exec_result}")
                except Exception as e:
                    logger.exception(f"[{symbol}] Order execution failed: {e}")
                    result["reasons"].append(f"Execution failed: {e}")
                    result["can_execute"] = False
            else:
                if result["can_execute"]:
                    result["decision"] = "PROCEED"
                    result["reasons"].append("All checks passed (auto_execute=False)")

        except Exception as e:
            logger.exception(f"[{symbol}] Orchestration failed: {e}")
            result["reasons"].append(f"Orchestration error: {e}")
            result["can_execute"] = False

        # Add execution time
        end_time = datetime.now(timezone.utc)
        result["execution_time_ms"] = (end_time - start_time).total_seconds() * 1000

        return result

    async def analyze_trade(
        self,
        symbol: str,
        candles: Optional[List[Dict[str, Any]]] = None,
        current_price: Optional[float] = None,
        indicators: Optional[List[Dict[str, Any]]] = None,
        account_balance: Optional[float] = None,
        stop_loss_pips: Optional[float] = None,
        risk_strategy: str = "fixed_risk",
        risk_percent: float = 2.0,
        leverage: int = 1,
        existing_positions: Optional[List[Dict[str, Any]]] = None,
        pending_positions: Optional[List[Dict[str, Any]]] = None,
        requested_qty: Optional[float] = None,
        order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze trade WITHOUT executing (auto_execute=False)."""
        return await self.orchestrate_trade(
            symbol=symbol,
            candles=candles,
            current_price=current_price,
            indicators=indicators,
            account_balance=account_balance,
            stop_loss_pips=stop_loss_pips,
            risk_strategy=risk_strategy,
            risk_percent=risk_percent,
            leverage=leverage,
            existing_positions=existing_positions,
            pending_positions=pending_positions,
            requested_qty=requested_qty,
            order_id=order_id,
            user_id=None,
            auto_execute=False,
        )
