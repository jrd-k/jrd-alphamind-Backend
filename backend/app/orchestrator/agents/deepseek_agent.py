from typing import Dict, Any

class DeepSeekAgent:
    """Stubbed DeepSeek agent for heavy reasoning and risk checks.

    In production, this would call DeepSeek and return numerical analysis,
    risk constraints, and validation for proposed strategies.
    """

    async def validate_strategy(self, strategy_spec: Dict[str, Any]) -> Dict[str, Any]:
        # Simple validation: check params exist and are reasonable
        params = strategy_spec.get("params", {})
        window = params.get("window", 0)
        threshold = params.get("threshold", 0)
        ok = window >= 1 and 0 < threshold < 0.1
        return {"valid": ok, "reason": None if ok else "invalid params"}
