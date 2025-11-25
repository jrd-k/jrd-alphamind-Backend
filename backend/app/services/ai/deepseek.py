from typing import Any, Dict
import httpx

from app.core import config

settings = config.settings


class DeepSeekClient:
    """Minimal DeepSeek API client.

    This client expects the API to expose a POST /search endpoint that accepts
    JSON payloads like {"q": "...", "top_k": N} and returns JSON results.
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None, timeout: float = 10.0):
        self.api_key = api_key or settings.deepseek_api_key
        self.base_url = base_url or settings.deepseek_base_url
        self.timeout = timeout
        if not self.api_key:
            raise ValueError("DeepSeek API key is not configured. Set DEEPSEEK_API_KEY in environment.")

    async def search(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/search"
        headers = {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}
        payload = {"q": query, "top_k": top_k}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()
