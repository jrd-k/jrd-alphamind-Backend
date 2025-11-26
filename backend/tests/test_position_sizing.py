"""Tests for position sizing service."""

import pytest
from app.services.position_sizing import (
    PositionSizer,
    RiskStrategy,
    calculate_position_size_simple,
)


class TestPositionSizerFixedRisk:
    """Test fixed risk % strategy."""

    def test_basic_calculation(self):
        """Test basic fixed risk calculation."""
        sizer = PositionSizer(
            account_balance=10000,
            leverage=1,
            risk_strategy=RiskStrategy.FIXED_RISK,
            risk_percent=2.0,
        )

        result = sizer.calculate_lot_size(
            symbol="EURUSD",
            stop_loss_pips=50,
            current_price=1.0835
        )

        assert result["lot_size"] == pytest.approx(0.4, rel=0.01)
        assert result["risk_amount_usd"] == pytest.approx(200, rel=0.01)
        assert result["risk_percent_of_account"] == pytest.approx(2.0, rel=0.01)
        assert result["stop_loss_pips"] == 50
        assert result["symbol"] == "EURUSD"

    def test_different_account_sizes(self):
        """Test scaling with different account sizes."""
        # Small account
        sizer_small = PositionSizer(
            account_balance=1000,
            risk_strategy=RiskStrategy.FIXED_RISK,
            risk_percent=2.0,
        )
        small_result = sizer_small.calculate_lot_size("EURUSD", 50)
        small_lot = small_result["lot_size"]

        # Large account
        sizer_large = PositionSizer(
            account_balance=100000,
            risk_strategy=RiskStrategy.FIXED_RISK,
            risk_percent=2.0,
        )
        large_result = sizer_large.calculate_lot_size("EURUSD", 50)
        large_lot = large_result["lot_size"]

        # Large account should have 100x larger position
        assert large_lot / small_lot == pytest.approx(100, rel=0.01)

    def test_different_stop_loss(self):
        """Test inverse relationship with stop-loss distance."""
        sizer = PositionSizer(
            account_balance=10000,
            risk_strategy=RiskStrategy.FIXED_RISK,
            risk_percent=2.0,
        )

        # Close stop-loss (50 pips)
        close_result = sizer.calculate_lot_size("EURUSD", 50)
        close_lot = close_result["lot_size"]

        # Wide stop-loss (100 pips)
        wide_result = sizer.calculate_lot_size("EURUSD", 100)
        wide_lot = wide_result["lot_size"]

        # Wide stop-loss should have half the lot size
        assert close_lot / wide_lot == pytest.approx(2.0, rel=0.01)

    def test_leverage_effect(self):
        """Test leverage multiplier on trading capital."""
        sizer_1x = PositionSizer(
            account_balance=10000,
            leverage=1,
            risk_strategy=RiskStrategy.FIXED_RISK,
            risk_percent=2.0,
        )

        sizer_10x = PositionSizer(
            account_balance=10000,
            leverage=10,
            risk_strategy=RiskStrategy.FIXED_RISK,
            risk_percent=2.0,
        )

        # Trading capital increases with leverage
        assert sizer_1x.trading_capital == 10000
        assert sizer_10x.trading_capital == 100000

        # Risk calculation is based on trading capital
        # With 10x leverage, same risk% on 100x capital = larger lot
        result_1x = sizer_1x.calculate_lot_size("EURUSD", 50)
        result_10x = sizer_10x.calculate_lot_size("EURUSD", 50)

        # Should show leverage effect in position value
        assert result_10x["leverage"] == 10
        assert result_1x["leverage"] == 1

    def test_min_max_constraints(self):
        """Test min/max lot size limits."""
        sizer = PositionSizer(
            account_balance=10000,
            risk_strategy=RiskStrategy.FIXED_RISK,
            risk_percent=2.0,
            min_lot_size=0.1,
            max_lot_size=1.0,
        )

        # Very tight stop-loss would require large position
        result = sizer.calculate_lot_size("EURUSD", 10)
        assert result["lot_size"] <= 1.0

        # Very wide stop-loss would require tiny position
        result = sizer.calculate_lot_size("EURUSD", 1000)
        assert result["lot_size"] >= 0.1


class TestPositionSizerFixedLot:
    """Test fixed lot size strategy."""

    def test_fixed_lot(self):
        """Test fixed lot size strategy."""
        sizer = PositionSizer(
            account_balance=10000,
            risk_strategy=RiskStrategy.FIXED_LOT,
            fixed_lot_size=0.5,
        )

        result = sizer.calculate_lot_size("EURUSD", 50)

        assert result["lot_size"] == 0.5
        assert result["strategy_used"] == "fixed_lot"

    def test_fixed_lot_ignores_stop_loss(self):
        """Fixed lot should not change with stop-loss."""
        sizer = PositionSizer(
            account_balance=10000,
            risk_strategy=RiskStrategy.FIXED_LOT,
            fixed_lot_size=0.5,
        )

        result_50 = sizer.calculate_lot_size("EURUSD", 50)
        result_100 = sizer.calculate_lot_size("EURUSD", 100)

        assert result_50["lot_size"] == result_100["lot_size"]


class TestPositionSizerKellyCriterion:
    """Test Kelly Criterion strategy."""

    def test_kelly_profitable_system(self):
        """Kelly with profitable win rate (60%)."""
        sizer = PositionSizer(
            account_balance=10000,
            risk_strategy=RiskStrategy.KELLY_CRITERION,
        )

        result = sizer.calculate_lot_size(
            "EURUSD",
            stop_loss_pips=50,
            win_rate=0.60,  # 60% win rate
        )

        # Should recommend positive lot size
        assert result["lot_size"] > 0

    def test_kelly_break_even_system(self):
        """Kelly with 50% win rate (break-even)."""
        sizer = PositionSizer(
            account_balance=10000,
            risk_strategy=RiskStrategy.KELLY_CRITERION,
        )

        result = sizer.calculate_lot_size(
            "EURUSD",
            stop_loss_pips=50,
            win_rate=0.50,
        )

        # Should recommend minimal lot size (close to 0)
        assert result["lot_size"] >= 0.01

    def test_kelly_without_win_rate_raises(self):
        """Kelly requires win_rate parameter."""
        sizer = PositionSizer(
            account_balance=10000,
            risk_strategy=RiskStrategy.KELLY_CRITERION,
        )

        with pytest.raises(ValueError, match="win_rate required"):
            sizer.calculate_lot_size("EURUSD", stop_loss_pips=50)


class TestPositionSizerVolatility:
    """Test volatility-based strategy."""

    def test_volatility_low_atr(self):
        """Low volatility (low ATR) = larger lot."""
        sizer = PositionSizer(
            account_balance=10000,
            risk_strategy=RiskStrategy.VOLATILITY_BASED,
            risk_percent=2.0,
        )

        # Low ATR (20 pips)
        result_low = sizer.calculate_lot_size(
            "EURUSD",
            stop_loss_pips=50,
            atr=20,
        )

        # High ATR (100 pips)
        result_high = sizer.calculate_lot_size(
            "EURUSD",
            stop_loss_pips=50,
            atr=100,
        )

        # Low volatility should have larger position
        assert result_low["lot_size"] > result_high["lot_size"]

    def test_volatility_without_atr_raises(self):
        """Volatility strategy requires ATR."""
        sizer = PositionSizer(
            account_balance=10000,
            risk_strategy=RiskStrategy.VOLATILITY_BASED,
        )

        with pytest.raises(ValueError, match="ATR required"):
            sizer.calculate_lot_size("EURUSD", stop_loss_pips=50)


class TestReverseCalculation:
    """Test reverse: risk amount -> lot size."""

    def test_risk_amount_calculation(self):
        """Calculate lot size from desired risk amount."""
        sizer = PositionSizer(account_balance=10000)

        result = sizer.calculate_lot_for_risk_amount(
            symbol="EURUSD",
            risk_amount_usd=50,
            stop_loss_pips=50,
        )

        assert result["lot_size"] == pytest.approx(0.1, rel=0.01)
        assert result["target_risk_usd"] == 50
        assert result["risk_percent_of_account"] == pytest.approx(0.5, rel=0.01)

    def test_risk_amount_respects_constraints(self):
        """Reverse calculation respects min/max."""
        sizer = PositionSizer(
            account_balance=10000,
            min_lot_size=0.1,
            max_lot_size=0.5,
        )

        # High risk amount might exceed max
        result = sizer.calculate_lot_for_risk_amount(
            symbol="EURUSD",
            risk_amount_usd=500,  # Would want 1.0 lots, but capped at 0.5
            stop_loss_pips=50,
        )

        assert result["lot_size"] <= 0.5


class TestScaleIn:
    """Test scale-in (multiple entries) strategy."""

    def test_three_entries(self):
        """Test dividing position into 3 entries."""
        sizer = PositionSizer(
            account_balance=10000,
            risk_strategy=RiskStrategy.FIXED_RISK,
            risk_percent=2.0,
        )

        result = sizer.calculate_multiple_entries(
            symbol="EURUSD",
            stop_loss_pips=50,
            num_entries=3,
        )

        assert len(result["entries"]) == 3
        assert result["entries"][0]["entry"] == 1
        assert result["entries"][2]["entry"] == 3
        
        # Each entry should be 1/3 of total
        entry_lot = result["entry_lot_size"]
        total_lot = result["total_lot_size"]
        assert entry_lot * 3 == pytest.approx(total_lot, rel=0.01)

    def test_scale_in_cumulative(self):
        """Test cumulative lot size across entries."""
        sizer = PositionSizer(
            account_balance=10000,
            risk_strategy=RiskStrategy.FIXED_RISK,
            risk_percent=2.0,
        )

        result = sizer.calculate_multiple_entries(
            symbol="EURUSD",
            stop_loss_pips=50,
            num_entries=5,
        )

        # Check cumulative grows correctly
        for i, entry in enumerate(result["entries"]):
            expected_cum = entry["lot_size"] * (i + 1)
            assert entry["cumulative_lot"] == pytest.approx(expected_cum, rel=0.01)


class TestSimpleCalculation:
    """Test simple helper function."""

    def test_simple_2_percent_rule(self):
        """Test standard 2% risk calculation."""
        lot_size = calculate_position_size_simple(
            account_balance=10000,
            risk_percent=2.0,
            stop_loss_pips=50,
        )

        assert lot_size == pytest.approx(0.4, rel=0.01)

    def test_simple_with_custom_risk(self):
        """Test with custom risk percentage."""
        lot_size_1pct = calculate_position_size_simple(
            account_balance=10000,
            risk_percent=1.0,
            stop_loss_pips=50,
        )

        lot_size_3pct = calculate_position_size_simple(
            account_balance=10000,
            risk_percent=3.0,
            stop_loss_pips=50,
        )

        assert lot_size_3pct / lot_size_1pct == pytest.approx(3.0, rel=0.01)


class TestEdgeCases:
    """Test edge cases and validation."""

    def test_zero_stop_loss_raises(self):
        """Stop-loss must be > 0."""
        sizer = PositionSizer(account_balance=10000)

        with pytest.raises(ValueError, match="Stop-loss must be"):
            sizer.calculate_lot_size("EURUSD", stop_loss_pips=0)

    def test_negative_stop_loss_raises(self):
        """Negative stop-loss should raise."""
        sizer = PositionSizer(account_balance=10000)

        with pytest.raises(ValueError):
            sizer.calculate_lot_size("EURUSD", stop_loss_pips=-10)

    def test_unknown_symbol_uses_default_specs(self):
        """Unknown symbols should use default contract specs."""
        sizer = PositionSizer(account_balance=10000)

        # Should not raise, uses default specs
        result = sizer.calculate_lot_size("UNKNOWNSYMBOL", stop_loss_pips=50)

        assert result["lot_size"] > 0
        assert result["symbol"] == "UNKNOWNSYMBOL"

    def test_very_small_account(self):
        """Very small account should still calculate."""
        sizer = PositionSizer(account_balance=100)

        result = sizer.calculate_lot_size("EURUSD", stop_loss_pips=50)

        # Should be very small but valid
        assert result["lot_size"] > 0
        assert result["lot_size"] < 0.1
