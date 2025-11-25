from typing import Dict, Any, List, Optional


class QwenAgent:
    """Stubbed Qwen agent for code generation / NLP tasks.

    In production, this would call out to the Qwen API and return structured
    outputs (strategy parameters, code, or sentiment scores). This stub now
    accepts optional indicator signals so it can incorporate them into proposals.
    """

    async def propose_strategy(self, market: str, indicators: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        # Return a simple strategy spec as a placeholder and echo indicator context
        desc = "Buy when price drops 0.2% below 20-period moving avg, sell when above."
        if indicators:
            desc += f"\nIncorporates {len(indicators)} recent indicator signals."

        return {
            "name": f"mean_reversion_{market}",
            "params": {"window": 20, "threshold": 0.002},
            "description": desc,
            "indicators": indicators,
        }

    def propose_strategy_sync(self, market: str, indicators: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Synchronous wrapper for strategy proposal (for scheduler use)."""
        desc = "Buy when price drops 0.2% below 20-period moving avg, sell when above."
        if indicators:
            # Extract signal from latest indicator
            latest_signal = indicators[0].get("signal", "neutral") if indicators else "neutral"
            desc += f"\nLatest indicator signal: {latest_signal}"
            if latest_signal == "bull":
                return {
                    "action": "buy",
                    "quantity": 1.0,
                    "entry_price": 0.0,
                    "description": desc,
                }
            elif latest_signal == "bear":
                return {
                    "action": "sell",
                    "quantity": 1.0,
                    "entry_price": 0.0,
                    "description": desc,
                }

        return {
            "name": f"mean_reversion_{market}",
            "params": {"window": 20, "threshold": 0.002},
            "description": desc,
            "action": "hold",
            "quantity": 0.0,
            "indicators": indicators,
        }
