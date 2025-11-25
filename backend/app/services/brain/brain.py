from typing import Any, Dict, List, Optional
import asyncio
import logging

from app.core import config
from app.services.indicators.fibonacci import compute_fibonacci
from app.services.brain import store as brain_store

logger = logging.getLogger(__name__)
settings = config.settings

# Import optional AI clients lazily to avoid requiring API keys during tests
try:
    from app.services.ai.deepseek import DeepSeekClient
except Exception:  # pragma: no cover - optional
    DeepSeekClient = None  # type: ignore

try:
    from app.services.ai.openai_client import OpenAIClient
except Exception:  # pragma: no cover - optional
    OpenAIClient = None  # type: ignore


class Brain:
    """Compose indicator signals and optional AI signals into a trade decision.

    The Brain will:
    - compute indicators (currently Fibonacci) from provided candles
    - enrich market context using DeepSeek search if configured
    - ask OpenAI for a concise decision if configured
    - merge signals and return a final recommendation: buy/sell/hold
    """

    def __init__(self):
        self.deepseek = None
        self.openai = None
        if DeepSeekClient and settings.deepseek_api_key:
            try:
                self.deepseek = DeepSeekClient()
            except Exception as e:
                logger.warning("DeepSeek client not initialized: %s", e)

        if OpenAIClient and settings.openai_api_key:
            try:
                self.openai = OpenAIClient()
            except Exception as e:
                logger.warning("OpenAI client not initialized: %s", e)

    async def decide(
        self,
        symbol: str,
        candles: Optional[List[Dict[str, Any]]] = None,
        current_price: Optional[float] = None,
        indicators: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Return a decision dict combining indicators and optional AI inputs.

        If `indicators` is provided, the Brain will use those instead of computing
        indicators from `candles` (useful when the orchestrator already provides
        indicator signals).
        """

        # If indicators are provided, create a lightweight summary instead of recomputing
        if indicators:
            try:
                # Build a concise summary and pick a best-effort signal
                summaries = []
                signal_votes = []
                for ind in indicators:
                    s = ind.get("signal") or ind.get("value") or ""
                    summaries.append(f"{ind.get('source')}:{s}")
                    if isinstance(s, str):
                        signal_votes.append(s.upper())

                summary = "; ".join(summaries)
                # pick most common signal if any
                indicator_signal = max(set(signal_votes), key=signal_votes.count) if signal_votes else "HOLD"
                fib = {"summary": summary, "signals": indicator_signal}
            except Exception as e:
                logger.exception("Error constructing summary from indicators: %s", e)
                raise
        else:
            # Compute Fibonacci from raw candles if provided
            try:
                fib = compute_fibonacci(candles or [], lookback=50)
            except Exception as e:
                logger.exception("Error computing fibonacci: %s", e)
                raise

            summary = fib.get("summary", "")
            indicator_signal = fib.get("signals", "HOLD")

        decision = {"symbol": symbol, "indicator": fib, "deepseek": None, "openai": None, "decision": "HOLD"}

        # Enrich with DeepSeek if available
        if self.deepseek:
            try:
                query = f"Market context for {symbol}. Indicator summary: {summary}"
                ds_res = await self.deepseek.search(query, top_k=3)
                decision["deepseek"] = ds_res
            except Exception as e:
                logger.warning("DeepSeek query failed: %s", e)

        # Ask OpenAI for recommendation if available
        if self.openai:
            try:
                messages = [
                    {"role": "system", "content": "You are a helpful trading assistant. Respond with a single recommended action: BUY, SELL, or HOLD, and one-line rationale."},
                    {"role": "user", "content": f"Symbol: {symbol}\nIndicator summary: {summary}\nCurrent price: {current_price}"},
                ]
                openai_res = await self.openai.chat(messages)
                decision["openai"] = openai_res
            except Exception as e:
                logger.warning("OpenAI chat failed: %s", e)

        # Fusion logic: confidence-weighted voting between indicator, DeepSeek, and OpenAI
        # Map signals to numeric scores: BUY=1, SELL=-1, HOLD=0
        def sig_to_score(s: Any) -> float:
            if not s:
                return 0.0
            s_up = str(s).upper()
            if "STRONG BUY" in s_up or s_up == "BUY":
                return 1.0
            if "STRONG SELL" in s_up or s_up == "SELL":
                return -1.0
            return 0.0

        # base confidences (tunable)
        conf_indicator = 0.6
        conf_deepseek = 0.1
        conf_openai = 0.3

        total_weight = 0.0
        score = 0.0

        # indicator contribution
        try:
            ind_score = sig_to_score(indicator_signal)
            score += ind_score * conf_indicator
            total_weight += conf_indicator
        except Exception:
            pass

        # DeepSeek contribution: look for an explicit recommendation in results
        try:
            if decision.get("deepseek"):
                # naive parsing: if DeepSeek returns 'recommendation' or top result contains BUY/SELL
                ds = decision["deepseek"]
                ds_text = str(ds)
                ds_score = 0.0
                if "BUY" in ds_text.upper():
                    ds_score = 1.0
                elif "SELL" in ds_text.upper():
                    ds_score = -1.0
                score += ds_score * conf_deepseek
                total_weight += conf_deepseek
        except Exception:
            pass

        # OpenAI contribution: parse assistant message
        try:
            if decision.get("openai"):
                choices = decision["openai"].get("choices", [])
                if choices:
                    # extract text whether using chat/completions or legacy
                    txt = ""
                    first = choices[0]
                    if isinstance(first.get("message"), dict):
                        txt = first.get("message", {}).get("content", "")
                    else:
                        txt = first.get("text", "")
                    ai_score = 0.0
                    if "BUY" in txt.upper():
                        ai_score = 1.0
                    elif "SELL" in txt.upper():
                        ai_score = -1.0
                    score += ai_score * conf_openai
                    total_weight += conf_openai
        except Exception:
            pass

        # Final decision based on weighted average
        final = "HOLD"
        if total_weight > 0:
            avg = score / total_weight
            if avg >= 0.4:
                final = "BUY"
            elif avg <= -0.4:
                final = "SELL"
            else:
                final = "HOLD"

        decision["decision"] = final

        # Persist decision to Redis and DB (best-effort, do not fail on error)
        try:
            # include a timestamp if not present
            if "timestamp" not in decision:
                from datetime import datetime, timezone

                decision["timestamp"] = datetime.now(timezone.utc).isoformat()

            # Save to Redis (async) and DB (background thread) concurrently. Do not raise on failure.
            try:
                # schedule DB write in background
                import asyncio

                await brain_store.save_decision(decision)
                # fire-and-forget DB write
                asyncio.create_task(brain_store.save_decision_db(decision))
            except Exception:
                logger.exception("Failed to persist decision to store")
        except Exception:
            logger.exception("Failed preparing timestamp for decision persistence")

        return decision
