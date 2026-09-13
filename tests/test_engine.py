import pytest
from src.engine import decide

def test_bucket_a_healthy_demand():
    """Test 1: Healthy baseline demand leads to no_action, 0 discount, and low risk score (< 0.40)."""
    slot = {
        "historical_fill_rate": 0.85,
        "lead_time_hours": 24.0,
        "margin_pct": 40,
        "base_price": 1000
    }
    decision = decide(slot)
    
    assert decision["action"] == "no_action"
    assert decision["discount_pct"] == 0
    assert decision["risk_score"] < 0.40

def test_bucket_b_desperate_high_margin():
    """Test 2: High urgency with high margin leads to notify_and_discount with max tier 25% discount."""
    slot = {
        "historical_fill_rate": 0.15,
        "lead_time_hours": 1.5,
        "margin_pct": 45,
        "base_price": 1200
    }
    decision = decide(slot)
    
    assert decision["action"] == "notify_and_discount"
    assert decision["discount_pct"] == 25
    assert decision["risk_score"] >= 0.70

def test_bucket_c_desperate_razor_thin_margin():
    """Test 3: High urgency but razor-thin margin (<=10%) results in notify_only and 0 discount."""
    slot = {
        "historical_fill_rate": 0.15,
        "lead_time_hours": 1.5,
        "margin_pct": 10,
        "base_price": 1000
    }
    decision = decide(slot)
    
    assert decision["action"] == "notify_only"
    assert decision["discount_pct"] == 0

def test_bucket_c_desperate_constrained_margin():
    """Test 4: High urgency with constrained margin (18%) caps discount at margin - 10% (8%)."""
    slot = {
        "historical_fill_rate": 0.15,
        "lead_time_hours": 1.5,
        "margin_pct": 18,
        "base_price": 1000
    }
    decision = decide(slot)
    
    assert decision["action"] == "notify_and_discount"
    assert decision["discount_pct"] == 8

def test_bucket_c_ambiguous_moderate():
    """Test 5: Moderate vacancy risk leads to notify_and_discount with 15% discount."""
    slot = {
        "historical_fill_rate": 0.50,
        "lead_time_hours": 12.0,
        "margin_pct": 35,
        "base_price": 1000
    }
    decision = decide(slot)
    
    assert decision["action"] == "notify_and_discount"
    assert decision["discount_pct"] == 15

def test_reasoning_string_contains_slot_metrics():
    """Test 6: Reasoning text dynamically includes string representations of slot metrics."""
    slot = {
        "historical_fill_rate": 0.50,
        "lead_time_hours": 12.0,
        "margin_pct": 35,
        "base_price": 1000
    }
    decision = decide(slot)
    reasoning = decision["reasoning"]
    
    # Verify lead time, margin, and risk metric representations are embedded in reasoning string
    assert str(slot["lead_time_hours"]) in reasoning
    assert str(slot["margin_pct"]) in reasoning
    assert str(decision["risk_score"]) in reasoning


