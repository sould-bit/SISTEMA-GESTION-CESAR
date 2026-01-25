"""
Unit Tests for Financial Calculations Module
=============================================

Tests para verificar la precisión de los cálculos financieros,
especialmente la eliminación de errores de redondeo.

Run with: pytest tests/unit/test_financial_calculations.py -v
"""

import pytest
from decimal import Decimal

# Import the functions to test
from app.utils.financial_calculations import (
    round_currency,
    calculate_proportional_value,
    calculate_wac,
    validate_batch_consistency,
    calculate_margin,
    DEFAULT_PRICE_PRECISION,
)


class TestRoundCurrency:
    """Tests for round_currency function."""
    
    def test_round_to_two_decimals(self):
        """Standard 2-decimal rounding."""
        result = round_currency(Decimal("1666.6666"))
        assert result == Decimal("1666.67")
    
    def test_round_half_up(self):
        """Verify ROUND_HALF_UP behavior."""
        assert round_currency(Decimal("1.555")) == Decimal("1.56")
        assert round_currency(Decimal("1.554")) == Decimal("1.55")
    
    def test_none_returns_zero(self):
        """None input should return zero."""
        assert round_currency(None) == Decimal("0.00")
    
    def test_custom_precision(self):
        """Custom precision parameter."""
        result = round_currency(Decimal("1666.6666"), Decimal("0.0001"))
        assert result == Decimal("1666.6666")


class TestCalculateProportionalValue:
    """Tests for proportional value calculation (CORE FIX)."""
    
    def test_full_stock_returns_exact_total(self):
        """
        CRITICAL: Full stock should return EXACTLY total_cost.
        This is the main bug we're fixing - no more $50,000.10
        """
        result = calculate_proportional_value(
            total_cost=Decimal("50000"),
            quantity_remaining=Decimal("30"),
            quantity_initial=Decimal("30")
        )
        # Must be EXACTLY 50000, not 50000.10
        assert result == Decimal("50000.00")
    
    def test_half_consumed_returns_half_value(self):
        """50% consumed = 50% of original value."""
        result = calculate_proportional_value(
            total_cost=Decimal("50000"),
            quantity_remaining=Decimal("15"),
            quantity_initial=Decimal("30")
        )
        assert result == Decimal("25000.00")
    
    def test_repeating_decimal_division(self):
        """Handle divisions that produce repeating decimals."""
        result = calculate_proportional_value(
            total_cost=Decimal("100"),
            quantity_remaining=Decimal("1"),
            quantity_initial=Decimal("3")
        )
        # 100 * (1/3) = 33.33 (rounded)
        assert result == Decimal("33.33")
    
    def test_zero_initial_quantity(self):
        """Division by zero should return 0, not error."""
        result = calculate_proportional_value(
            total_cost=Decimal("50000"),
            quantity_remaining=Decimal("10"),
            quantity_initial=Decimal("0")
        )
        assert result == Decimal("0.00")
    
    def test_none_total_cost(self):
        """None total_cost should return 0."""
        result = calculate_proportional_value(
            total_cost=None,
            quantity_remaining=Decimal("30"),
            quantity_initial=Decimal("30")
        )
        assert result == Decimal("0.00")
    
    def test_completely_consumed(self):
        """Zero remaining = zero value."""
        result = calculate_proportional_value(
            total_cost=Decimal("50000"),
            quantity_remaining=Decimal("0"),
            quantity_initial=Decimal("30")
        )
        assert result == Decimal("0.00")


class TestCalculateWAC:
    """Tests for Weighted Average Cost calculation."""
    
    def test_simple_wac(self):
        """Basic WAC calculation."""
        result = calculate_wac(
            total_value=Decimal("85000"),
            total_quantity=Decimal("50")
        )
        assert result == Decimal("1700.0000")
    
    def test_wac_with_decimals(self):
        """WAC with repeating decimals."""
        result = calculate_wac(
            total_value=Decimal("50000"),
            total_quantity=Decimal("30")
        )
        # 50000 / 30 = 1666.6666...
        assert result == Decimal("1666.6667")
    
    def test_zero_quantity_uses_fallback(self):
        """Zero stock should use fallback cost."""
        result = calculate_wac(
            total_value=Decimal("0"),
            total_quantity=Decimal("0"),
            fallback_cost=Decimal("1500")
        )
        assert result == Decimal("1500.0000")
    
    def test_negative_quantity_uses_fallback(self):
        """Negative stock (error state) uses fallback."""
        result = calculate_wac(
            total_value=Decimal("50000"),
            total_quantity=Decimal("-5"),
            fallback_cost=Decimal("1500")
        )
        assert result == Decimal("1500.0000")


class TestValidateBatchConsistency:
    """Tests for batch data validation."""
    
    def test_consistent_batch(self):
        """Perfectly consistent batch."""
        is_valid, diff = validate_batch_consistency(
            total_cost=Decimal("50001"),
            quantity_initial=Decimal("30"),
            cost_per_unit=Decimal("1666.70")
        )
        assert is_valid is True
        assert diff < Decimal("0.50")
    
    def test_inconsistent_batch(self):
        """Batch with large discrepancy."""
        is_valid, diff = validate_batch_consistency(
            total_cost=Decimal("50000"),
            quantity_initial=Decimal("30"),
            cost_per_unit=Decimal("2000")  # Wrong!
        )
        assert is_valid is False
        assert diff > Decimal("10000")  # 60000 - 50000


class TestCalculateMargin:
    """Tests for profit margin calculation."""
    
    def test_standard_margin(self):
        """Standard margin calculation."""
        absolute, percentage = calculate_margin(
            sale_price=Decimal("5000"),
            cost=Decimal("1666.67")
        )
        assert absolute == Decimal("3333.33")
        assert percentage == Decimal("66.67")
    
    def test_zero_price(self):
        """Zero price returns zero margin."""
        absolute, percentage = calculate_margin(
            sale_price=Decimal("0"),
            cost=Decimal("1000")
        )
        assert absolute == Decimal("0.00")
        assert percentage == Decimal("0.00")
    
    def test_none_cost(self):
        """None cost treated as zero."""
        absolute, percentage = calculate_margin(
            sale_price=Decimal("5000"),
            cost=None
        )
        assert absolute == Decimal("5000.00")
        assert percentage == Decimal("100.00")


class TestIntegrationScenario:
    """Integration tests simulating real scenarios."""
    
    def test_multiple_batches_exact_valuation(self):
        """
        Simulates multiple batches and verifies no accumulated error.
        
        Scenario:
        - Batch 1: 30 units @ $50,000 total (full stock)
        - Batch 2: 20 units @ $35,000 total (full stock)
        
        Expected total value: $85,000 exactly
        """
        batch1_value = calculate_proportional_value(
            total_cost=Decimal("50000"),
            quantity_remaining=Decimal("30"),
            quantity_initial=Decimal("30")
        )
        
        batch2_value = calculate_proportional_value(
            total_cost=Decimal("35000"),
            quantity_remaining=Decimal("20"),
            quantity_initial=Decimal("20")
        )
        
        total_value = batch1_value + batch2_value
        
        # MUST be exactly 85000, no rounding errors
        assert total_value == Decimal("85000.00")
    
    def test_partial_consumption_accuracy(self):
        """
        Scenario with partial consumption.
        
        - Batch: 30 units @ $50,000
        - Consumed: 10 units
        - Remaining: 20 units
        
        Expected value: $33,333.33 (50000 * 20/30)
        """
        result = calculate_proportional_value(
            total_cost=Decimal("50000"),
            quantity_remaining=Decimal("20"),
            quantity_initial=Decimal("30")
        )
        
        # 50000 * (20/30) = 33333.33...
        expected = round_currency(Decimal("50000") * (Decimal("20") / Decimal("30")))
        assert result == expected
    
    def test_wac_with_mixed_batches(self):
        """
        WAC calculation with partially consumed batches.
        
        - Batch 1: 30 units @ $50,000 → 20 remaining → value: $33,333.33
        - Batch 2: 20 units @ $35,000 → 20 remaining → value: $35,000.00
        
        Total: 40 units, $68,333.33
        WAC: $1,708.33
        """
        batch1_value = calculate_proportional_value(
            total_cost=Decimal("50000"),
            quantity_remaining=Decimal("20"),
            quantity_initial=Decimal("30")
        )
        
        batch2_value = calculate_proportional_value(
            total_cost=Decimal("35000"),
            quantity_remaining=Decimal("20"),
            quantity_initial=Decimal("20")
        )
        
        total_value = batch1_value + batch2_value
        total_quantity = Decimal("40")
        
        wac = calculate_wac(total_value, total_quantity)
        
        # Verify WAC is reasonable (around $1708)
        assert Decimal("1708") <= wac <= Decimal("1709")
