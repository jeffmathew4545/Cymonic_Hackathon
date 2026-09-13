import pytest
from src.engine import decide
from src.config import DISCOUNT_TIER_HIGH, DISCOUNT_TIER_MED, DISCOUNT_TIER_LOW

def test_decide_no_action():
    # Test 1: High fill rate + long lead time
    slot = {
        "historical_fill_rate": 0.85,
        "lead_time_hours": 30.0,
        "margin_pct": 50.0
    }
    decision = decide(slot)
    
    assert decision["action"] == "no_action"
    assert decision["discount_pct"] == 0.0
    assert decision["segment_notified"] is None
    assert "low risk" in decision["reasoning"].lower() or "no intervention needed" in decision["reasoning"].lower()

def test_decide_notify_and_discount():
    # Test 2: Low fill rate + short lead time + healthy margin
    slot = {
        "historical_fill_rate": 0.20,
        "lead_time_hours": 1.5,
        "margin_pct": 50.0
    }
    decision = decide(slot)
    
    assert decision["action"] == "notify_and_discount"
    assert decision["discount_pct"] == DISCOUNT_TIER_HIGH
    assert "high risk" in decision["reasoning"].lower()
    
def test_decide_thin_margin():
    # Test 3: Thin margin prevents discount despite risk
    slot = {
        "historical_fill_rate": 0.20,
        "lead_time_hours": 1.5,
        "margin_pct": 18.0 # Very thin margin!
    }
    decision = decide(slot)
    
    # Assuming MIN_REQUIRED_MARGIN_AFTER_DISCOUNT is 15.0,
    # max discount is 3.0, which is below DISCOUNT_TIER_LOW (10.0)
    assert decision["action"] == "notify_only"
    assert decision["discount_pct"] == 0.0
    assert "exceeds margin threshold" in decision["reasoning"].lower()
    
def test_decide_different_reasoning():
    # Test 4: Different slot values produce different reasoning
    slot1 = {"historical_fill_rate": 0.20, "lead_time_hours": 1.5, "margin_pct": 50.0}
    slot2 = {"historical_fill_rate": 0.50, "lead_time_hours": 10.0, "margin_pct": 45.0}
    
    dec1 = decide(slot1)
    dec2 = decide(slot2)
    
    assert dec1["reasoning"] != dec2["reasoning"]
    
def test_returned_dictionary_structure():
    # Test 5: Returned dictionary contains required keys
    slot = {"historical_fill_rate": 0.5, "lead_time_hours": 10.0, "margin_pct": 40.0}
    decision = decide(slot)
    
    assert "action" in decision
    assert "discount_pct" in decision
    assert "segment_notified" in decision
    assert "reasoning" in decision
