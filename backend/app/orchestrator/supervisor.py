import asyncio
import random
from typing import Dict, Any, List, Optional
from app.orchestrator.agents.qwen_agent import QwenAgent
from app.orchestrator.agents.deepseek_agent import DeepSeekAgent
from app.services.brain.brain import Brain
from app.services.brokers.paper_client import PaperTradingClient
from app.core.database import SessionLocal
from app.models.orm_models import IndicatorSignal


class Supervisor:
    """Simple orchestrator that routes tasks to agents and runs a paper backtest.

    This is a lightweight scaffold that mimics a LangChain/LangGraph supervisor
    but without external LLM dependencies. Use this as a starting point to
    integrate real LLM agents later.
    """

    def __init__(self):
        self.qwen = QwenAgent()
        self.deepseek = DeepSeekAgent()
        self.brain = Brain()

    async def generate_and_test(self, market: str, use_indicators: bool = True) -> Dict[str, Any]:
        # Optionally fetch recent indicator signals for this market and pass them to Qwen
        indicators: Optional[List[Dict[str, Any]]] = None
        if use_indicators:
            db = SessionLocal()
            try:
                rows = (
                    db.query(IndicatorSignal)
                    .filter(IndicatorSignal.symbol == market)
                    .order_by(IndicatorSignal.timestamp.desc())
                    .limit(100)
                    .all()
                )
                indicators = [
                    {
                        "id": r.id,
                        "symbol": r.symbol,
                        "source": r.source,
                        "signal": r.signal,
                        "value": r.value,
                        "timestamp": r.timestamp.isoformat() if getattr(r, "timestamp", None) is not None else None,
                    }
                    for r in rows
                ]
            finally:
                db.close()

        # Ask Brain for a decision combining indicators + AI (if available)
        decision = await self.brain.decide(market, indicators=indicators, current_price=None)

        # Convert decision into a candidate strategy for Qwen (or short-circuit)
        # If Brain strongly recommends BUY/SELL, propose a simple strategy reflecting that
        action = decision.get("decision", "HOLD")
        if action == "HOLD":
            # If hold, still ask Qwen for alternative strategies
            strategy = await self.qwen.propose_strategy(market, indicators=indicators)
        else:
            strategy = {
                "name": f"brain-{action.lower()}-strategy",
                "action": action,
                "params": {"window": 20, "threshold": 0.002},
            }

        # Validate with DeepSeek
        validation = await self.deepseek.validate_strategy(strategy)
        if not validation.get("valid"):
            return {"accepted": False, "reason": validation.get("reason"), "strategy": strategy}

    # Run a quick paper backtest using PaperTradingClient on synthetic data
        pnl, trades = await self._paper_backtest(strategy, market)
        return {"accepted": True, "strategy": strategy, "pnl": pnl, "trades": trades}

    async def _paper_backtest(self, strategy: Dict[str, Any], market: str) -> tuple[float, List[Dict[str, Any]]]:
        # Generate synthetic price series (random walk)
        n = 200
        prices = [1.0]
        for _ in range(n - 1):
            prices.append(prices[-1] * (1 + random.uniform(-0.005, 0.005)))

        window = strategy.get("params", {}).get("window", 20)
        threshold = strategy.get("params", {}).get("threshold", 0.002)

        client = PaperTradingClient()
        cash = 10000.0
        position = 0.0
        trades = []

        for i in range(window, n):
            ma = sum(prices[i - window : i]) / window
            price = prices[i]
            # mean reversion logic
            if price < ma * (1 - threshold) and position <= 0:
                qty = 1.0
                res = await client.place_order(market, "buy", qty)
                trades.append(res)
                position += qty
                cash -= res.get("price", 0) * qty
            elif price > ma * (1 + threshold) and position > 0:
                qty = position
                res = await client.place_order(market, "sell", qty)
                trades.append(res)
                cash += res.get("price", 0) * qty
                position -= qty

        # compute simple PnL: cash + position*last_price - initial cash
        pnl = cash + position * prices[-1] - 10000.0
        return pnl, trades

    def run_with_indicators(self, symbol: str, indicators: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Synchronous wrapper for generating strategy with indicators (for scheduler use).
        
        Args:
            symbol: Market/symbol to generate strategy for
            indicators: List of indicator dicts with signal/value data
        
        Returns:
            Strategy dict with action, quantity, entry_price, etc.
        """
        strategy = self.qwen.propose_strategy_sync(symbol, indicators=indicators)
        return strategy
