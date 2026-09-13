import re
from typing import Dict, List, Optional, Union, Any

def classify_time_block(time_block: str) -> str:
    """
    Classify a time block string (e.g. '7:00 PM – 8:00 PM') into:
    'Mornings', 'Afternoons', or 'Evenings'.
    
    Rules:
    - Before 12:00 PM -> Mornings
    - 12:00 PM to 4:59 PM -> Afternoons
    - 5:00 PM onwards -> Evenings
    """
    if not time_block or not isinstance(time_block, str):
        return "Afternoons"
        
    match = re.search(r'(\d{1,2})(?::\d{2})?\s*(AM|PM)', time_block, re.IGNORECASE)
    if not match:
        time_lower = time_block.lower()
        if "morning" in time_lower:
            return "Mornings"
        if "evening" in time_lower:
            return "Evenings"
        return "Afternoons"
        
    hour = int(match.group(1))
    period = match.group(2).upper()
    
    # Convert to 24-hour format
    if period == "PM" and hour != 12:
        hour_24 = hour + 12
    elif period == "AM" and hour == 12:
        hour_24 = 0
    else:
        hour_24 = hour
        
    if hour_24 < 12:
        return "Mornings"
    elif 12 <= hour_24 < 17:
        return "Afternoons"
    else:
        return "Evenings"


def find_best_segment(
    slot: Dict[str, Any], 
    segments: Union[List[Dict[str, Any]], Any], 
    discount_pct: float = 0.0
) -> Optional[Dict[str, Any]]:
    """
    Milestone 3.1: Multi-Attribute Audience Matcher.
    
    Finds the single best customer segment for a given slot by evaluating:
    1. Sport match (strict requirement)
    2. Time block alignment (+15 points)
    3. Price sensitivity alignment with discount depth (+0 to +30 points)
    
    Returns the highest-scoring segment dictionary, or None if no match.
    """
    # Ensure segments is a list of dictionaries (handles DataFrame or list)
    if hasattr(segments, 'to_dict'):
        segments_list = segments.to_dict('records')
    elif isinstance(segments, list):
        segments_list = segments
    else:
        segments_list = list(segments)

    sport = slot.get('sport_type')
    if not sport:
        return None

    # Step 1: Filter by Sport (Hard constraint)
    candidates = [s for s in segments_list if s.get('preferred_sport') == sport]
    if not candidates:
        return None

    # Step 2: Classify the slot's time block (Mornings / Afternoons / Evenings)
    slot_time = classify_time_block(slot.get('time_block', ''))

    # Step 3: Score candidates on Time and Price Sensitivity
    scored_candidates = []
    for s in candidates:
        score = 0

        # Time compatibility (+15 pts)
        if s.get('preferred_time') == slot_time:
            score += 15

        # Price sensitivity vs. discount percentage
        sensitivity = str(s.get('price_sensitivity', 'Medium')).capitalize()
        if discount_pct >= 20.0:
            # Deep discount: prioritize high price sensitivity (students, deal seekers)
            if sensitivity == 'High':
                score += 30
            elif sensitivity == 'Medium':
                score += 15
            elif sensitivity == 'Low':
                score += 0
        elif discount_pct == 0.0:
            # 0% discount (notify_only): prioritize low price sensitivity (corporates, regular clubs)
            if sensitivity == 'Low':
                score += 30
            elif sensitivity == 'Medium':
                score += 15
            elif sensitivity == 'High':
                score += 0
        else:
            # Moderate discount (10% - 15%): prioritize medium price sensitivity
            if sensitivity == 'Medium':
                score += 30
            elif sensitivity == 'High':
                score += 20
            elif sensitivity == 'Low':
                score += 10

        scored_candidates.append((score, s))

    # Step 4: Pick winner deterministically
    # Sort by -score (highest score first), tiebreak by segment_id ascending
    scored_candidates.sort(key=lambda item: (-item[0], str(item[1].get('segment_id', ''))))

    return scored_candidates[0][1]


def calculate_pricing(base_price: float, discount_pct: float = 0.0) -> Dict[str, Any]:
    """
    Milestone 3.2: Pricing Math & Copy Integrity.
    
    Computes exact rounded integer discounted prices and savings:
    - discounted_price = round(base_price * (1 - discount_pct / 100))
    - savings = int(base_price) - int(discounted_price)
    
    Guarantees integer representation with zero floating-point artifacts.
    """
    base = round(float(base_price))
    discount = float(discount_pct)
    
    if discount <= 0.0:
        discounted = base
        savings = 0
        discount_clean = 0.0
    else:
        discounted = round(base * (1.0 - (discount / 100.0)))
        savings = max(0, base - discounted)
        discount_clean = round(discount, 1)
        
    return {
        "base_price": base,
        "discount_pct": discount_clean,
        "discounted_price": discounted,
        "savings": savings,
        "currency": "₹"
    }


def generate_channel_payloads(
    slot: Dict[str, Any], 
    segment: Dict[str, Any], 
    pricing: Dict[str, Any], 
    action: str
) -> Dict[str, Any]:
    """
    Milestone 3.3: Multi-Channel Payload Generator.
    
    Produces formatted, realistic marketing copy for:
    - PUSH_NOTIFICATION: High urgency, under 100 characters.
    - IN_APP_BANNER: Hero banner with headline, subtext, badge, and CTA button.
    - SMS_PREVIEW: Standard telecom text under 160 characters with short URL.
    """
    sport = slot.get('sport_type', 'Sport')
    time_block = slot.get('time_block', 'today')
    slot_id = slot.get('slot_id', 'SLOT')
    segment_name = segment.get('segment_name', 'Players')
    
    base = pricing.get('base_price', 0)
    final = pricing.get('discounted_price', 0)
    savings = pricing.get('savings', 0)
    discount = pricing.get('discount_pct', 0.0)
    curr = pricing.get('currency', '₹')
    
    is_discounted = (action == "notify_and_discount" and discount > 0)
    
    # 1. PUSH NOTIFICATION (<100 chars body)
    if is_discounted:
        push_title = f"⚡ {discount:.0f}% OFF: {sport} Today!"
        push_body = f"{time_block} slot now {curr}{final} (Save {curr}{savings}). Tap to book!"
    else:
        push_title = f"📢 Open Slot Alert: {sport}"
        push_body = f"{time_block} slot open today at {curr}{base}. Reserve your court now!"
        
    push_payload = {
        "title": push_title,
        "body": push_body,
        "action_url": f"https://cymonic.in/book/{slot_id}"
    }
    
    # 2. IN-APP BANNER
    if is_discounted:
        banner_headline = f"Exclusive {discount:.0f}% Off for {segment_name}"
        banner_subtext = f"Book today's {time_block} {sport} slot for {curr}{final} instead of {curr}{base}."
        banner_badge = f"{discount:.0f}% OFF"
        banner_cta = f"Book for {curr}{final}"
    else:
        banner_headline = f"Prime Slot Available for {segment_name}"
        banner_subtext = f"{sport} court open today at {time_block} for {curr}{base}."
        banner_badge = "AVAILABLE"
        banner_cta = f"Reserve for {curr}{base}"
        
    banner_payload = {
        "headline": banner_headline,
        "subtext": banner_subtext,
        "badge": banner_badge,
        "cta_button": banner_cta
    }
    
    # 3. SMS PREVIEW (<160 chars)
    short_url = f"cymonic.in/s/{slot_id}"
    if is_discounted:
        sms_text = f"Cymonic: Hi {segment_name}! {sport} slot open today {time_block} for {curr}{final} (was {curr}{base}, save {curr}{savings}). Book: {short_url}"
    else:
        sms_text = f"Cymonic: Hi {segment_name}! {sport} slot open today {time_block} at {curr}{base}. Reserve court now: {short_url}"
        
    sms_payload = {
        "sender_id": "CYMONIC",
        "text": sms_text,
        "char_count": len(sms_text)
    }
    
    return {
        "PUSH_NOTIFICATION": push_payload,
        "IN_APP_BANNER": banner_payload,
        "SMS_PREVIEW": sms_payload
    }


def generate_payload(
    slot: Dict[str, Any], 
    decision: Dict[str, Any], 
    segments_df: Any = None
) -> Optional[Dict[str, Any]]:
    """
    Milestone 3.4: Contract Handoff.
    
    Packages a standardized dictionary ready for Member 4's UI cards:
    - If action == "no_action": returns None
    - If action in ["notify_only", "notify_and_discount"]:
        integrates Audience Matcher (3.1), Pricing Math (3.2), and Multi-Channel Payloads (3.3).
    """
    if not decision or decision.get('action') == "no_action":
        return None
        
    action = decision.get('action', 'notify_only')
    discount_pct = float(decision.get('discount_pct', 0.0))
    
    # 1. Match best segment (Milestone 3.1)
    best_segment = None
    if segments_df is not None:
        best_segment = find_best_segment(slot, segments_df, discount_pct)
        
    if not best_segment:
        # Fallback to decision segment_notified or general
        seg_name = decision.get('segment_notified') or 'General Audience'
        best_segment = {
            "segment_id": "GEN01",
            "segment_name": seg_name,
            "preferred_sport": slot.get('sport_type', 'General'),
            "preferred_time": "Any",
            "price_sensitivity": "Medium"
        }
        
    # 2. Compute exact pricing math (Milestone 3.2)
    base_price = float(slot.get('base_price', 0))
    pricing = calculate_pricing(base_price, discount_pct)
    
    # 3. Generate multi-channel payloads (Milestone 3.3)
    channels = generate_channel_payloads(slot, best_segment, pricing, action)
    
    # 4. Standardized payload dictionary for Member 4 UI cards
    return {
        "slot_id": slot.get('slot_id', ''),
        "action": action,
        "segment": best_segment,
        "pricing": pricing,
        "channels": channels,
        "metadata": {
            "sport_type": slot.get('sport_type', ''),
            "date": slot.get('date', ''),
            "time_block": slot.get('time_block', ''),
            "lead_time_hours": float(slot.get('lead_time_hours', 0)),
            "historical_fill_rate": float(slot.get('historical_fill_rate', 0)),
            "reasoning": decision.get('reasoning', '')
        }
    }


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
    
    # Calculate exact integer price with calculate_pricing
    pricing = calculate_pricing(base_price, discount_pct)
    final_price = pricing['discounted_price']
    curr = pricing['currency']
    
    if action == "notify_and_discount" and pricing['discount_pct'] > 0:
        title = f"🔥 Notify + {pricing['discount_pct']:.0f}% Discount"
        price_line = f"{curr}{final_price} instead of {curr}{pricing['base_price']} (Save {curr}{pricing['savings']})"
    else:
        title = "📢 Notify Available Slot"
        price_line = f"{curr}{pricing['base_price']} (Base Price)"
        
    message = f"""{title}

{segment}

Slot: {sport} | {time_block} today

{price_line}

Historical fill rate: {fill_rate:.0%}
Time remaining: {lead_time} hours

Act fast!"""
    return message
