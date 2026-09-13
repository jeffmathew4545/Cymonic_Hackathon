import pytest
import pandas as pd
from src.messaging import (
    classify_time_block,
    find_best_segment,
    calculate_pricing,
    generate_channel_payloads,
    generate_payload,
    generate_outreach_message
)

@pytest.fixture
def sample_segments():
    return pd.read_csv("data/segments.csv")

def test_classify_time_block():
    assert classify_time_block("8:00 AM – 9:00 AM") == "Mornings"
    assert classify_time_block("11:30 AM – 12:30 PM") == "Mornings"
    assert classify_time_block("12:00 PM – 1:00 PM") == "Afternoons"
    assert classify_time_block("2:00 PM – 3:00 PM") == "Afternoons"
    assert classify_time_block("4:00 PM – 5:00 PM") == "Afternoons"
    assert classify_time_block("5:00 PM – 6:00 PM") == "Evenings"
    assert classify_time_block("7:00 PM – 8:00 PM") == "Evenings"

def test_audience_matcher_deep_discount(sample_segments):
    # Afternoon badminton slot with 25% discount should target Student Badminton Club (High sensitivity)
    slot = {
        "sport_type": "Badminton",
        "time_block": "3:00 PM – 4:00 PM"
    }
    best = find_best_segment(slot, sample_segments, discount_pct=25.0)
    assert best is not None
    assert best["segment_name"] == "Student Badminton Club"
    assert best["price_sensitivity"] == "High"

def test_audience_matcher_zero_discount(sample_segments):
    # Evening badminton slot with 0% discount should target Corporate Badminton League (Low sensitivity)
    slot = {
        "sport_type": "Badminton",
        "time_block": "7:00 PM – 8:00 PM"
    }
    best = find_best_segment(slot, sample_segments, discount_pct=0.0)
    assert best is not None
    assert best["segment_name"] == "Corporate Badminton League"
    assert best["price_sensitivity"] == "Low"

def test_pricing_math_integrity():
    # 25% off 1000 -> 750 (save 250)
    p1 = calculate_pricing(1000, 25.0)
    assert p1["base_price"] == 1000
    assert p1["discounted_price"] == 750
    assert p1["savings"] == 250
    assert p1["discount_pct"] == 25.0
    assert p1["base_price"] - p1["discounted_price"] == p1["savings"]

    # 15% off 700 -> 595 (save 105)
    p2 = calculate_pricing(700, 15.0)
    assert p2["discounted_price"] == 595
    assert p2["savings"] == 105
    assert isinstance(p2["discounted_price"], int)

    # 0% off 800 -> 800 (save 0)
    p3 = calculate_pricing(800, 0.0)
    assert p3["discounted_price"] == 800
    assert p3["savings"] == 0

def test_multichannel_payloads():
    slot = {
        "slot_id": "S1015",
        "sport_type": "Badminton",
        "time_block": "7:00 PM – 8:00 PM"
    }
    segment = {
        "segment_id": "SEG02",
        "segment_name": "Corporate Badminton League"
    }
    pricing = calculate_pricing(800, 25.0)
    payloads = generate_channel_payloads(slot, segment, pricing, action="notify_and_discount")

    # Push Notification
    push = payloads["PUSH_NOTIFICATION"]
    assert "25%" in push["title"]
    assert len(push["body"]) < 100
    assert "https://cymonic.in/book/S1015" == push["action_url"]

    # In-App Banner
    banner = payloads["IN_APP_BANNER"]
    assert "Corporate Badminton League" in banner["headline"]
    assert "25% OFF" in banner["badge"]

    # SMS Preview
    sms = payloads["SMS_PREVIEW"]
    assert sms["char_count"] <= 160
    assert "cymonic.in/s/S1015" in sms["text"]

def test_contract_handoff_no_action(sample_segments):
    slot = {"slot_id": "S1001", "sport_type": "Football", "base_price": 1000}
    decision = {"action": "no_action", "discount_pct": 0.0}
    payload = generate_payload(slot, decision, sample_segments)
    assert payload is None

def test_contract_handoff_valid(sample_segments):
    slot = {
        "slot_id": "S1028",
        "sport_type": "Cricket",
        "time_block": "2:00 PM – 3:00 PM",
        "base_price": 900,
        "lead_time_hours": 9.4,
        "historical_fill_rate": 0.53
    }
    decision = {
        "action": "notify_and_discount",
        "discount_pct": 25.0,
        "reasoning": "High risk of vacancy with healthy margin."
    }
    payload = generate_payload(slot, decision, sample_segments)

    assert payload is not None
    assert payload["slot_id"] == "S1028"
    assert payload["action"] == "notify_and_discount"
    assert "segment" in payload
    assert payload["segment"]["segment_name"] == "College Cricket Group"
    assert payload["pricing"]["discounted_price"] == 675
    assert payload["pricing"]["savings"] == 225
    assert "PUSH_NOTIFICATION" in payload["channels"]
    assert "IN_APP_BANNER" in payload["channels"]
    assert "SMS_PREVIEW" in payload["channels"]
    assert "metadata" in payload

def test_backward_compatible_message():
    slot = {
        "sport_type": "Cricket",
        "time_block": "2:00 PM – 3:00 PM",
        "base_price": 900,
        "lead_time_hours": 9.4,
        "historical_fill_rate": 0.53
    }
    decision = {
        "action": "notify_and_discount",
        "discount_pct": 25.0,
        "segment_notified": "College Cricket Group"
    }
    msg = generate_outreach_message(slot, decision)
    assert msg is not None
    assert "College Cricket Group" in msg
    assert "25% Discount" in msg
    assert "Save" in msg
