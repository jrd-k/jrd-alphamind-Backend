"""
Background scheduler for independent indicator computation and orchestrator execution.
Runs on a timer to:
1. Fetch OHLCV candles for tracked instruments
2. Compute SuperTrend-AI indicators
3. Persist signals
4. Trigger orchestrator to generate strategies and execute trades
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.orm_models import Instrument, IndicatorSignal, Order
from app.services.indicators.supertrend_ai import compute_supertrend
from app.orchestrator.supervisor import Supervisor

logger = logging.getLogger(__name__)


class IndicatorScheduler:
    """Scheduler that runs indicator computation and orchestrator on intervals."""

    def __init__(self, interval_seconds: int = 60, enabled: bool = True):
        self.interval_seconds = interval_seconds
        self.enabled = enabled
        self.running = False

    async def start(self):
        """Start the scheduler loop."""
        if not self.enabled:
            logger.info("Scheduler disabled (SCHEDULER_ENABLED=false)")
            return

        self.running = True
        logger.info(f"Scheduler started (interval={self.interval_seconds}s)")
        while self.running:
            try:
                await self._tick()
            except Exception as e:
                logger.error(f"Scheduler tick error: {e}", exc_info=True)
            await asyncio.sleep(self.interval_seconds)

    async def stop(self):
        """Stop the scheduler loop."""
        self.running = False
        logger.info("Scheduler stopped")

    async def _tick(self):
        """Single scheduler tick: compute indicators and run orchestrator."""
        logger.debug("Scheduler tick: computing indicators...")

        # Get all instruments to compute indicators for
        db = SessionLocal()
        try:
            instruments = db.query(Instrument).all()
            for inst in instruments:
                await self._compute_indicator_for_symbol(inst.symbol, db)

            # Run orchestrator to generate strategies from latest indicators
            await self._run_orchestrator(db)
        finally:
            db.close()

    async def _compute_indicator_for_symbol(self, symbol: str, db) -> Optional[IndicatorSignal]:
        """Compute SuperTrend-AI for a symbol using simulated candles."""
        try:
            # Fetch or simulate OHLCV candles for the symbol
            # In a real system, this would fetch from a market data provider
            candles = self._fetch_candles_for_symbol(symbol)
            if not candles or len(candles) < 10:
                logger.debug(f"Skipping {symbol}: insufficient candles ({len(candles) or 0})")
                return None

            # Compute SuperTrend-AI
            result = compute_supertrend(
                candles,
                length=10,
                min_mult=1.0,
                max_mult=5.0,
                step=0.5,
                perf_alpha=10.0,
                from_cluster="default",
            )
            summary = result.get("summary") or {}

            # Check if we already have a signal for this candle timestamp
            candle_ts_str = summary.get("timestamp")
            existing = (
                db.query(IndicatorSignal)
                .filter(
                    IndicatorSignal.symbol == symbol,
                    IndicatorSignal.source == "supertrend_ai",
                    IndicatorSignal.timestamp == candle_ts_str,
                )
                .first()
            )
            if existing:
                logger.debug(f"{symbol}: indicator already computed for {candle_ts_str}")
                return existing

            # Persist signal
            signal_val = "bull" if summary.get("os") else "bear"
            ts_raw = summary.get("timestamp")
            if isinstance(ts_raw, str):
                try:
                    ts = datetime.fromisoformat(ts_raw)
                except Exception:
                    ts = datetime.now(timezone.utc)
            else:
                ts = datetime.now(timezone.utc)

            sig = IndicatorSignal(
                symbol=symbol,
                source="supertrend_ai",
                signal=signal_val,
                value=summary,
                timestamp=ts,
            )
            db.add(sig)
            db.commit()
            db.refresh(sig)
            logger.debug(f"{symbol}: {signal_val} signal stored (id={sig.id})")
            return sig
        except Exception as e:
            logger.error(f"Error computing indicator for {symbol}: {e}", exc_info=True)
            return None

    async def _run_orchestrator(self, db):
        """Run orchestrator to generate strategies from latest indicators."""
        try:
            logger.debug("Running orchestrator...")
            supervisor = Supervisor()

            # Fetch latest indicators for each symbol
            instruments = db.query(Instrument).all()
            for inst in instruments:
                latest_sig = (
                    db.query(IndicatorSignal)
                    .filter(IndicatorSignal.symbol == inst.symbol)
                    .order_by(IndicatorSignal.created_at.desc())
                    .first()
                )
                if not latest_sig:
                    continue

                # Run supervisor strategy generation
                indicators = [
                    {
                        "symbol": latest_sig.symbol,
                        "signal": latest_sig.signal,
                        "value": latest_sig.value,
                    }
                ]
                try:
                    strategy = supervisor.run_with_indicators(inst.symbol, indicators)
                    logger.debug(
                        f"{inst.symbol}: strategy generated: "
                        f"action={strategy.get('action')}, qty={strategy.get('quantity')}"
                    )

                    # Optionally auto-execute if strategy says so
                    if strategy.get("action") in ("buy", "sell"):
                        await self._auto_execute_strategy(inst.symbol, strategy, db)
                except Exception as e:
                    logger.error(f"Error running orchestrator for {inst.symbol}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Orchestrator tick error: {e}", exc_info=True)

    async def _auto_execute_strategy(self, symbol: str, strategy: dict, db):
        """Auto-execute a strategy if enabled."""
        # Only auto-execute if explicitly configured
        auto_execute = getattr(settings, "scheduler_auto_execute", False)
        if not auto_execute:
            logger.debug(f"Auto-execute disabled; skipping {symbol} strategy execution")
            return

        try:
            from app.services.execution import execute_order_sync

            side = strategy.get("action")  # "buy" or "sell"
            quantity = strategy.get("quantity", 1.0)
            price = strategy.get("entry_price") or 0.0  # 0 = market order

            order = Order(
                user_id=1,  # System user for scheduled trades
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                status="pending",
            )
            db.add(order)
            db.commit()
            db.refresh(order)

            logger.info(f"Auto-executing {side} {quantity} {symbol} (order_id={order.id})")
            trade = execute_order_sync(order)
            logger.info(f"Trade executed: {trade}")
        except Exception as e:
            logger.error(f"Error auto-executing strategy for {symbol}: {e}", exc_info=True)

    def _fetch_candles_for_symbol(self, symbol: str, num_candles: int = 30) -> list:
        """
        Fetch OHLCV candles for a symbol.
        In dev/test, returns simulated candles.
        In production, connect to a real market data provider.
        """
        # For now, return simulated increasing candles
        # In production, fetch from IQFeed, Alpaca, etc.
        candles = []
        t = datetime.now(timezone.utc)
        p = 100.0

        for i in range(num_candles):
            o = p
            h = p * 1.001
            l = p * 0.999
            c = p * (1.0005 + (i % 3 - 1) * 0.0001)
            v = 1000 + i * 100

            candles.append(
                {
                    "t": (t - timedelta(minutes=num_candles - i)).isoformat(),
                    "o": o,
                    "h": h,
                    "l": l,
                    "c": c,
                    "v": v,
                }
            )
            p = c

        return candles


# Global scheduler instance
_scheduler_instance: Optional[IndicatorScheduler] = None


def get_scheduler() -> IndicatorScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        enabled = getattr(settings, "scheduler_enabled", True)
        interval = getattr(settings, "scheduler_interval_seconds", 60)
        _scheduler_instance = IndicatorScheduler(interval_seconds=interval, enabled=enabled)
    return _scheduler_instance
