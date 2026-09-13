import math
from src.config import (
    WEIGHT_FILL_RATE, WEIGHT_LEAD_TIME,
    RISK_THRESHOLD_HIGH, RISK_THRESHOLD_MEDIUM,
    MIN_REQUIRED_MARGIN_AFTER_DISCOUNT,
    DISCOUNT_TIER_HIGH, DISCOUNT_TIER_MED, DISCOUNT_TIER_LOW,
    MAX_LEAD_TIME_HOURS
)

def _calculate_risk_score(fill_rate: float, lead_time_hours: float) -> float:
    """Calculate 0-1 risk score. Higher score = higher risk of vacancy."""
    # Inverse fill rate (0 fill rate = 1.0 risk)
    fill_risk = max(0.0, 1.0 - fill_rate)
    
    # Lead time risk (less lead time = more risk)
    # Capped at MAX_LEAD_TIME_HOURS (e.g. 48h)
    lead_time_ratio = min(lead_time_hours, MAX_LEAD_TIME_HOURS) / MAX_LEAD_TIME_HOURS
    lead_risk = 1.0 - lead_time_ratio
    
    # Weighted combination
    score = (fill_risk * WEIGHT_FILL_RATE) + (lead_risk * WEIGHT_LEAD_TIME)
    return score

def decide(slot: dict) -> dict:
    """
    Evaluate slot and return decision dictionary.
    
    Expected slot format:
    {
        'slot_id': str,
        'sport_type': str,
        'lead_time_hours': float,
        'historical_fill_rate': float,
        'margin_pct': float,
        ...
    }
    """
    fill_rate = float(slot.get('historical_fill_rate', 1.0))
    lead_time = float(slot.get('lead_time_hours', 48.0))
    margin = float(slot.get('margin_pct', 0.0))
    sport = slot.get('sport_type', 'Unknown')
    
    risk_score = _calculate_risk_score(fill_rate, lead_time)
    
    action = "no_action"
    discount_pct = 0.0
    segment_notified = None
    reasoning = ""
    
    # Base target discount based on risk
    target_discount = 0.0
    if risk_score >= RISK_THRESHOLD_HIGH:
        target_discount = DISCOUNT_TIER_HIGH
    elif risk_score >= RISK_THRESHOLD_MEDIUM:
        target_discount = DISCOUNT_TIER_MED
    
    # Check if target discount exceeds margin threshold
    max_allowable_discount = max(0.0, margin - MIN_REQUIRED_MARGIN_AFTER_DISCOUNT)
    
    if max_allowable_discount <= 0.0:
        # Margin is too thin to discount
        if risk_score >= RISK_THRESHOLD_MEDIUM:
            action = "notify_only"
            reasoning = f"Fill rate is {fill_rate:.0%} and only {lead_time}h remain, indicating risk. However, margin is only {margin}%, so discounting is unsafe. We will notify interested segments at base price."
        else:
            action = "no_action"
            reasoning = f"Fill rate is {fill_rate:.0%} and {lead_time}h remain, indicating low risk. The slot is safe to leave alone."
    else:
        # We can offer some discount
        if target_discount > 0.0:
            actual_discount = min(target_discount, max_allowable_discount)
            
            if actual_discount >= DISCOUNT_TIER_LOW:
                action = "notify_and_discount"
                discount_pct = actual_discount
                if actual_discount < target_discount:
                    reasoning = f"Fill rate is {fill_rate:.0%} and only {lead_time}h remain. High risk demands a discount, but margin is {margin}%. Reduced discount to {actual_discount}% to remain profitable."
                else:
                    reasoning = f"Fill rate is {fill_rate:.0%} and only {lead_time}h remain, indicating high risk of vacancy. With a healthy margin of {margin}%, offering a full {actual_discount}% discount to secure revenue."
            else:
                action = "notify_only"
                reasoning = f"Fill rate is {fill_rate:.0%} and {lead_time}h remain. Risk warrants action, but even minimal discount exceeds margin threshold. Notifying at base price."
        else:
            action = "no_action"
            reasoning = f"Fill rate is {fill_rate:.0%} and {lead_time}h remain. Risk score is very low, indicating natural fill probability is high. No intervention needed."

    # In a real app, the loader joins segment data to select segment dynamically, 
    # but the engine itself can just assign the category for now if needed.
    # We will pick the segment in data_loader/messaging when applying the action.
    # For now, we leave segment_notified as None here if no action, else we will populate it later or we can stub it.
    
    return {
        "action": action,
        "discount_pct": discount_pct,
        "segment_notified": segment_notified, # populated by data_loader mapping
        "reasoning": reasoning
    }
