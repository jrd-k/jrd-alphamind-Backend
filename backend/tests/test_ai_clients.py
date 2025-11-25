import pytest
import respx
from httpx import Response

from app.services.ai.openai_client import OpenAIClient
from app.services.ai.deepseek import DeepSeekClient


@pytest.mark.asyncio
async def test_openai_client_chat_success():
    # Arrange
    api_key = "testkey"
    base_url = "https://api.test-openai.com/v1"
    client = OpenAIClient(api_key=api_key, base_url=base_url)

    mock_url = f"{base_url}/chat/completions"
    expected = {"id": "cmpl-1", "choices": [{"message": {"content": "BUY because..."}}]}

    with respx.mock as rs:
        rs.post(mock_url).respond(200, json=expected)

        # Act
        res = await client.chat(messages=[{"role": "user", "content": "hello"}], model="gpt-test")

        # Assert
        assert res["id"] == "cmpl-1"
        assert "choices" in res


@pytest.mark.asyncio
async def test_deepseek_client_search_success():
    api_key = "ds-test"
    base_url = "https://api.test-deepseek.com/v1"
    client = DeepSeekClient(api_key=api_key, base_url=base_url)

    mock_url = f"{base_url}/search"
    expected = {"results": [{"id": "r1", "score": 0.9, "text": "context"}]}

    with respx.mock as rs:
        rs.post(mock_url).respond(200, json=expected)

        res = await client.search("market context", top_k=3)
        assert "results" in res
        assert res["results"][0]["id"] == "r1"
