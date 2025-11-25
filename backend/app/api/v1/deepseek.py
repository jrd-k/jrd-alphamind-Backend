from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx

from app.services.ai.deepseek import DeepSeekClient

router = APIRouter(prefix="/ai/deepseek", tags=["ai"])


class SearchPayload(BaseModel):
    query: str
    top_k: int = 5


@router.post("/search")
async def deepseek_search(payload: SearchPayload):
    try:
        client = DeepSeekClient()
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))

    try:
        res = await client.search(payload.query, payload.top_k)
        return res
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
