from typing import Any, Dict, List, Optional
import httpx

from app.core import config

settings = config.settings


class KimiClient:
    """Kimi AI (Moonshot AI) Chat completions client using `httpx`.

    This client uses OpenAI-compatible API endpoints.
    It expects `KIMI_API_KEY` to be set in environment or settings.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, timeout: float = 10.0):
        self.api_key = api_key or settings.kimi_api_key
        self.base_url = base_url or settings.kimi_base_url
        self.timeout = timeout
        if not self.api_key:
            raise ValueError("Kimi API key is not configured. Set KIMI_API_KEY in environment.")

    async def chat(self, messages: List[Dict[str, str]], model: str = "moonshot-v1-8k") -> Dict[str, Any]:
        """Send chat completion request to Kimi AI."""
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 256,
            "stream": False
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()

    async def decide_trade(self, symbol: str, indicators: str, market_context: str = "") -> str:
        """Get trading decision from Kimi AI based on indicators and market context."""
        system_prompt = """You are an expert forex trader. Analyze the given indicators and market context, then provide a concise trading decision.

Rules:
- Respond with only one word: BUY, SELL, or HOLD
- Base decision on technical indicators and market context
- Consider risk management principles
- Be conservative when signals are mixed"""

        user_prompt = f"""Symbol: {symbol}
Indicators: {indicators}
Market Context: {market_context}

What is your trading decision?"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = await self.chat(messages)
            decision = response.get("choices", [{}])[0].get("message", {}).get("content", "").strip().upper()

            # Validate response is one of the expected values
            if decision not in ["BUY", "SELL", "HOLD"]:
                return "HOLD"  # Default to hold if unclear

            return decision
        except Exception:
            return "HOLD"  # Default to hold on error