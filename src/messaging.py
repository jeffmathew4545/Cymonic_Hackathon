from typing import Dict, Optional

def generate_outreach_message(slot: Dict, decision: Dict) -> Optional[str]:
    """Generate dynamic outreach message based on slot and decision."""
    
    action = decision.get('action')
    if action == "no_action":
        return None
        
    sport = slot.get('sport_type')
    time_block = slot.get('time_block')
    base_price = float(slot.get('base_price', 0))
    discount_pct = decision.get('discount_pct', 0)
    segment = decision.get('segment_notified', 'Unknown Segment')
    fill_rate = float(slot.get('historical_fill_rate', 0))
    lead_time = float(slot.get('lead_time_hours', 0))
    
    # Calculate new price
    final_price = base_price * (1 - (discount_pct / 100))
    
    if action == "notify_and_discount":
        title = f"🔥 Notify + {discount_pct:.0f}% Discount"
        price_line = f"₹{final_price:.0f} instead of ₹{base_price:.0f}"
    else:
        title = "📢 Notify Available Slot"
        price_line = f"₹{base_price:.0f} (Base Price)"
        
    message = f"""{title}

{segment}

Slot: {sport} | {time_block} today

{price_line}

Historical fill rate: {fill_rate:.0%}
Time remaining: {lead_time} hours

Act fast!"""
    return message
