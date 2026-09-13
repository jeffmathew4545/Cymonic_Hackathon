import pandas as pd
import random
from typing import List, Dict

def load_slots(file_path="data/slots.csv") -> List[Dict]:
    """Load slots as a list of dictionaries."""
    try:
        df = pd.read_csv(file_path)
        # Ensure correct types
        df['margin_pct'] = df['margin_pct'].astype(float)
        df['historical_fill_rate'] = df['historical_fill_rate'].astype(float)
        df['lead_time_hours'] = df['lead_time_hours'].astype(float)
        df['base_price'] = df['base_price'].astype(float)
        return df.to_dict('records')
    except FileNotFoundError:
        return []

def load_segments(file_path="data/segments.csv") -> List[Dict]:
    """Load segments as a list of dictionaries."""
    try:
        return pd.read_csv(file_path).to_dict('records')
    except FileNotFoundError:
        return []

def match_segment(sport: str, segments: List[Dict]) -> str:
    """Find a segment that prefers this sport. Return segment_name."""
    possible_segments = [s for s in segments if s.get('preferred_sport') == sport]
    if not possible_segments:
        return "General Audience"
    # Choose randomly among matching segments to show variety, 
    # or you could map specific times but keeping it simple.
    return random.choice(possible_segments)['segment_name']

def apply_decision_to_slot(slot: Dict, decision: Dict, segments: List[Dict]) -> Dict:
    """Update a slot dictionary with the decision from the engine."""
    action = decision['action']
    slot['action_taken'] = action
    slot['discount_pct_applied'] = decision['discount_pct']
    slot['reasoning'] = decision['reasoning']
    
    if action in ['notify_only', 'notify_and_discount']:
        segment = match_segment(slot['sport_type'], segments)
        slot['segment_notified'] = segment
        slot['current_status'] = "notified"
        decision['segment_notified'] = segment
    else:
        slot['segment_notified'] = ""
        slot['current_status'] = "monitored"
        decision['segment_notified'] = None
        
    return slot

def save_slots(slots: List[Dict], file_path="data/slots.csv"):
    """Save the updated slots list back to CSV."""
    df = pd.DataFrame(slots)
    df.to_csv(file_path, index=False)
