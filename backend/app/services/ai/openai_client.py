from typing import Any, Dict, List, Optional
import httpx

from app.core import config

settings = config.settings


class OpenAIClient:
    """Minimal OpenAI Chat completions client using `httpx`.

    This is intentionally small to avoid adding the `openai` package as a dependency.
    It expects `OPENAI_API_KEY` to be set in environment or settings.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, timeout: float = 10.0):
        self.api_key = api_key or settings.openai_api_key
        self.base_url = base_url or settings.openai_base_url
        self.timeout = timeout
        if not self.api_key:
            raise ValueError("OpenAI API key is not configured. Set OPENAI_API_KEY in environment.")

    async def chat(self, messages: List[Dict[str, str]], model: str = "gpt-3.5-turbo") -> Dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": model, "messages": messages, "temperature": 0.2, "max_tokens": 256}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()
