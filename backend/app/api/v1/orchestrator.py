from fastapi import APIRouter
from app.orchestrator.supervisor import Supervisor

router = APIRouter()
supervisor = Supervisor()


@router.post("/generate_strategy")
async def generate_strategy(market: str = "EURUSD"):
    """Generate a strategy (via Qwen), validate with DeepSeek, and run a paper backtest."""
    result = await supervisor.generate_and_test(market)
    return result
