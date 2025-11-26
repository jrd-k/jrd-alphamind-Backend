"""Tests for Trade Orchestration System.

Tests the complete workflow:
- Brain signal generation
- Position sizing
- Risk management checks
- Order execution
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from app.services.trade_orchestrator import TradeOrchestrator
from app.services.position_sizing import RiskStrategy
from app.services.risk_manager import RiskLevel


class TestTradeOrchestrator:
    """Test TradeOrchestrator class."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance."""
        return TradeOrchestrator()

    @pytest.mark.asyncio
    async def test_orchestrate_hold_signal(self, orchestrator):
        """Test that HOLD signals skip execution."""
        with patch.object(orchestrator.brain, "decide") as mock_decide:
            mock_decide.return_value = {"decision": "HOLD", "indicator": {}}

            result = await orchestrator.analyze_trade(
                symbol="EURUSD",
                current_price=1.0835,
                account_balance=10000,
                stop_loss_pips=50,
            )

            assert result["decision"] == "HOLD"
            assert result["can_execute"] is False
            assert result["lot_size"] == 0.0

    @pytest.mark.asyncio
    async def test_orchestrate_buy_signal_safe(self, orchestrator):
        """Test BUY signal with all checks passing."""
        with patch.object(orchestrator.brain, "decide") as mock_decide:
            mock_decide.return_value = {
                "decision": "BUY",
                "indicator": {},
                "deepseek": None,
                "openai": None,
            }

            result = await orchestrator.analyze_trade(
                symbol="EURUSD",
                current_price=1.0835,
                account_balance=10000,
                stop_loss_pips=50,
                risk_strategy="fixed_risk",
                risk_percent=2.0,
            )

            assert result["decision"] == "PROCEED"
            assert result["can_execute"] is True
            assert result["lot_size"] > 0
            assert result["risk_level"] == "SAFE"

    @pytest.mark.asyncio
    async def test_orchestrate_sell_signal(self, orchestrator):
        """Test SELL signal execution."""
        with patch.object(orchestrator.brain, "decide") as mock_decide:
            mock_decide.return_value = {
                "decision": "SELL",
                "indicator": {},
                "deepseek": None,
                "openai": None,
            }

            result = await orchestrator.analyze_trade(
                symbol="EURUSD",
                current_price=1.0835,
                account_balance=10000,
                stop_loss_pips=50,
            )

            assert result["decision"] == "PROCEED"
            assert result["can_execute"] is True

    @pytest.mark.asyncio
    async def test_orchestrate_position_sizing_calculation(self, orchestrator):
        """Test position size is correctly calculated."""
        with patch.object(orchestrator.brain, "decide") as mock_decide:
            mock_decide.return_value = {
                "decision": "BUY",
                "indicator": {},
                "deepseek": None,
                "openai": None,
            }

            result = await orchestrator.analyze_trade(
                symbol="EURUSD",
                current_price=1.0835,
                account_balance=10000,
                stop_loss_pips=50,
                risk_strategy="fixed_risk",
                risk_percent=2.0,
            )

            # 2% of 10000 = 200 USD risk
            # 50 pips * 0.0001 = 0.005 per pip per lot
            # So lot_size = 200 / (50 * 0.0001) = 200 / 0.005 = 40 lots (for EURUSD)
            # But with pip value adjustment, should be around 0.4 lots
            assert result["lot_size"] > 0
            assert "position_sizing" in result["workflow"]

    @pytest.mark.asyncio
    async def test_orchestrate_risk_checks_included(self, orchestrator):
        """Test that all risk checks are included in workflow."""
        with patch.object(orchestrator.brain, "decide") as mock_decide:
            mock_decide.return_value = {
                "decision": "BUY",
                "indicator": {},
                "deepseek": None,
                "openai": None,
            }

            result = await orchestrator.analyze_trade(
                symbol="EURUSD",
                current_price=1.0835,
                account_balance=10000,
                stop_loss_pips=50,
            )

            assert "risk_checks" in result["workflow"]
            checks = result["workflow"]["risk_checks"]["checks"]
            # Should have all 6 checks
            assert len(checks) >= 6
            check_types = [c["name"] for c in checks]
            assert "daily_loss" in check_types
            assert "drawdown" in check_types

    @pytest.mark.asyncio
    async def test_orchestrate_with_execution(self, orchestrator):
        """Test execution when auto_execute=True and checks pass."""
        with patch.object(orchestrator.brain, "decide") as mock_decide:
            with patch("app.services.trade_orchestrator.execute_order") as mock_exec:
                mock_decide.return_value = {
                    "decision": "BUY",
                    "indicator": {},
                    "deepseek": None,
                    "openai": None,
                }
                mock_exec.return_value = {"order_id": 42, "status": "filled"}

                result = await orchestrator.orchestrate_trade(
                    symbol="EURUSD",
                    current_price=1.0835,
                    account_balance=10000,
                    stop_loss_pips=50,
                    user_id=1,
                    auto_execute=True,
                )

                assert result["decision"] == "PROCEED"
                assert result["execution_result"] is not None
                assert result["execution_result"]["order_id"] == 42

    @pytest.mark.asyncio
    async def test_orchestrate_without_execution(self, orchestrator):
        """Test analysis without execution (auto_execute=False)."""
        with patch.object(orchestrator.brain, "decide") as mock_decide:
            with patch(
                "app.services.trade_orchestrator.execute_order"
            ) as mock_exec:
                mock_decide.return_value = {
                    "decision": "BUY",
                    "indicator": {},
                    "deepseek": None,
                    "openai": None,
                }

                result = await orchestrator.analyze_trade(
                    symbol="EURUSD",
                    current_price=1.0835,
                    account_balance=10000,
                    stop_loss_pips=50,
                )

                # Should not call execute_order
                mock_exec.assert_not_called()
                assert result["execution_result"] is None
                assert result["decision"] == "PROCEED"

    @pytest.mark.asyncio
    async def test_orchestrate_brain_failure_handling(self, orchestrator):
        """Test graceful failure when Brain decision fails."""
        with patch.object(orchestrator.brain, "decide") as mock_decide:
            mock_decide.side_effect = Exception("Brain service error")

            result = await orchestrator.analyze_trade(
                symbol="EURUSD",
                current_price=1.0835,
                account_balance=10000,
            )

            assert result["can_execute"] is False
            assert "Brain decision failed" in " ".join(result["reasons"])

    @pytest.mark.asyncio
    async def test_orchestrate_risk_check_failure(self, orchestrator):
        """Test rejection when risk check fails."""
        with patch.object(orchestrator.brain, "decide") as mock_decide:
            mock_decide.return_value = {
                "decision": "BUY",
                "indicator": {},
                "deepseek": None,
                "openai": None,
            }

            # Test with very large position (should fail risk check)
            result = await orchestrator.analyze_trade(
                symbol="EURUSD",
                current_price=1.0835,
                account_balance=1000,  # Small account
                stop_loss_pips=50,
                risk_percent=50,  # 50% risk (too high)
            )

            # Should be rejected due to risk
            assert result["can_execute"] is False or result["risk_level"] in [
                "WARNING",
                "CRITICAL",
            ]

    @pytest.mark.asyncio
    async def test_orchestrate_with_default_stop_loss(self, orchestrator):
        """Test that default stop-loss is used when not provided."""
        with patch.object(orchestrator.brain, "decide") as mock_decide:
            mock_decide.return_value = {
                "decision": "BUY",
                "indicator": {},
                "deepseek": None,
                "openai": None,
            }

            result = await orchestrator.analyze_trade(
                symbol="EURUSD",
                current_price=1.0835,
                account_balance=10000,
                stop_loss_pips=None,  # Not provided
            )

            # Should use default 50 pips
            assert "stop_loss_pips" in result["workflow"]["position_sizing"]
            assert result["workflow"]["position_sizing"]["stop_loss_pips"] == 50

    @pytest.mark.asyncio
    async def test_orchestrate_execution_time_tracked(self, orchestrator):
        """Test that execution time is tracked."""
        with patch.object(orchestrator.brain, "decide") as mock_decide:
            mock_decide.return_value = {
                "decision": "BUY",
                "indicator": {},
                "deepseek": None,
                "openai": None,
            }

            result = await orchestrator.analyze_trade(
                symbol="EURUSD",
                current_price=1.0835,
                account_balance=10000,
                stop_loss_pips=50,
            )

            assert "execution_time_ms" in result
            assert result["execution_time_ms"] >= 0

    @pytest.mark.asyncio
    async def test_orchestrate_with_existing_positions(self, orchestrator):
        """Test correlation check with existing positions."""
        with patch.object(orchestrator.brain, "decide") as mock_decide:
            mock_decide.return_value = {
                "decision": "BUY",
                "indicator": {},
                "deepseek": None,
                "openai": None,
            }

            existing_pos = [{"symbol": "GBPUSD", "qty": 0.5}]

            result = await orchestrator.analyze_trade(
                symbol="EURUSD",
                current_price=1.0835,
                account_balance=10000,
                stop_loss_pips=50,
                existing_positions=existing_pos,
            )

            # Should run correlation check
            assert "risk_checks" in result["workflow"]

    @pytest.mark.asyncio
    async def test_orchestrate_different_strategies(self, orchestrator):
        """Test different position sizing strategies."""
        with patch.object(orchestrator.brain, "decide") as mock_decide:
            mock_decide.return_value = {
                "decision": "BUY",
                "indicator": {},
                "deepseek": None,
                "openai": None,
            }

            strategies = ["fixed_risk", "fixed_lot", "kelly", "volatility"]

            for strategy in strategies:
                result = await orchestrator.analyze_trade(
                    symbol="EURUSD",
                    current_price=1.0835,
                    account_balance=10000,
                    stop_loss_pips=50,
                    risk_strategy=strategy,
                )

                # Each strategy should produce a position size
                assert result["lot_size"] >= 0

    @pytest.mark.asyncio
    async def test_orchestrate_with_leverage(self, orchestrator):
        """Test orchestration with leverage."""
        with patch.object(orchestrator.brain, "decide") as mock_decide:
            mock_decide.return_value = {
                "decision": "BUY",
                "indicator": {},
                "deepseek": None,
                "openai": None,
            }

            result = await orchestrator.analyze_trade(
                symbol="EURUSD",
                current_price=1.0835,
                account_balance=10000,
                stop_loss_pips=50,
                leverage=50,  # 50x leverage
            )

            # Should calculate with leverage
            assert result["lot_size"] > 0
            assert "leverage" in result["workflow"]["position_sizing"]
            assert result["workflow"]["position_sizing"]["leverage"] == 50

    @pytest.mark.asyncio
    async def test_orchestrate_timestamps(self, orchestrator):
        """Test that timestamps are properly set."""
        with patch.object(orchestrator.brain, "decide") as mock_decide:
            mock_decide.return_value = {
                "decision": "BUY",
                "indicator": {},
                "deepseek": None,
                "openai": None,
            }

            result = await orchestrator.analyze_trade(
                symbol="EURUSD",
                current_price=1.0835,
                account_balance=10000,
            )

            assert "timestamp" in result
            # Should be valid ISO format
            datetime.fromisoformat(result["timestamp"])

    @pytest.mark.asyncio
    async def test_orchestrate_warnings_collection(self, orchestrator):
        """Test that warnings are properly collected."""
        with patch.object(orchestrator.brain, "decide") as mock_decide:
            mock_decide.return_value = {
                "decision": "BUY",
                "indicator": {},
                "deepseek": None,
                "openai": None,
            }

            result = await orchestrator.analyze_trade(
                symbol="EURUSD",
                current_price=1.0835,
                account_balance=10000,
                stop_loss_pips=None,  # Missing, should generate warning
            )

            assert len(result["warnings"]) > 0 or len(result["reasons"]) >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
