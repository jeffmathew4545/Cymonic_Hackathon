try:
    from src.config import (
        WEIGHT_FILL_RATE,
        WEIGHT_LEAD_TIME,
        RISK_THRESHOLD_HIGH,
        RISK_THRESHOLD_MEDIUM,
        MIN_REQUIRED_MARGIN_AFTER_DISCOUNT,
        DISCOUNT_TIER_HIGH,
        DISCOUNT_TIER_MED,
        MAX_LEAD_TIME_HOURS,
    )
except ImportError:
    from config import (
        WEIGHT_FILL_RATE,
        WEIGHT_LEAD_TIME,
        RISK_THRESHOLD_HIGH,
        RISK_THRESHOLD_MEDIUM,
        MIN_REQUIRED_MARGIN_AFTER_DISCOUNT,
        DISCOUNT_TIER_HIGH,
        DISCOUNT_TIER_MED,
        MAX_LEAD_TIME_HOURS,
    )


def decide(slot: dict) -> dict:
    """
    Evaluate vacant slot and return deterministic decision dictionary.
    
    Expected slot structure:
    {
        'historical_fill_rate': float/int/str,
        'lead_time_hours': float/int/str,
        'margin_pct': float/int/str,
        ...
    }
    """
    fill_rate = float(slot['historical_fill_rate'])
    lead_time_hours = float(slot['lead_time_hours'])
    margin_pct = float(slot['margin_pct'])

    # 1. Compute Risk Score (0.0 to 1.0, rounded to 2 decimal places)
    fill_rate_component = (1.0 - fill_rate) * WEIGHT_FILL_RATE
    lead_time_component = (1.0 - min(lead_time_hours / MAX_LEAD_TIME_HOURS, 1.0)) * WEIGHT_LEAD_TIME
    risk_score = round(fill_rate_component + lead_time_component, 2)

    # 2. Compute Margin Guardrail
    max_safe_discount = max(0, int(margin_pct) - int(MIN_REQUIRED_MARGIN_AFTER_DISCOUNT))

    # 3. Decision Logic & Dynamic Reasoning
    if risk_score < RISK_THRESHOLD_MEDIUM:
        # Case 1: Low risk
        action = "no_action"
        discount_pct = 0
        reasoning = f"Healthy baseline demand ({int(fill_rate * 100)}% fill rate) and {slot['lead_time_hours']}h lead time. Urgency is low ({risk_score}). Leaving slot at standard base price."
    elif max_safe_discount <= 0:
        # Case 2: Elevated risk but margin too restricted
        action = "notify_only"
        discount_pct = 0
        reasoning = f"Elevated vacancy risk ({risk_score}) with {slot['lead_time_hours']}h lead time, but margin is restricted at {slot['margin_pct']}%. Discounting would breach minimum operating margin. Retaining base price."
    elif risk_score < RISK_THRESHOLD_HIGH:
        # Case 3: Moderate risk with available margin
        action = "notify_and_discount"
        discount_pct = min(int(DISCOUNT_TIER_MED), max_safe_discount)
        reasoning = f"Moderate vacancy risk ({risk_score}) with {slot['lead_time_hours']}h lead time. Applied safe discount of {discount_pct}% within margin cap of {slot['margin_pct']}%."
    else:
        # Case 4: Critical risk with available margin
        action = "notify_and_discount"
        discount_pct = min(int(DISCOUNT_TIER_HIGH), max_safe_discount)
        reasoning = f"Critical urgency! Fill rate is only {int(fill_rate * 100)}% with {slot['lead_time_hours']}h remaining (Risk: {risk_score}). Applied {discount_pct}% discount (margin allows up to {max_safe_discount}%)."

    # 4. Return Contract
    return {
        "action": action,
        "discount_pct": int(discount_pct),
        "risk_score": float(risk_score),
        "reasoning": reasoning
    }


