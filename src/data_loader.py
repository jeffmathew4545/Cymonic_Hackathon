import os
import pandas as pd
from typing import List, Dict, Optional

def load_slots(file_path="data/slots.csv") -> List[Dict]:
    """Load slots as a list of dictionaries with fallback path handling."""
    target_path = file_path
    if not os.path.exists(target_path) and os.path.exists("slots.csv"):
        target_path = "slots.csv"
        
    try:
        df = pd.read_csv(target_path)
        # Ensure correct types and handle NaN/missing values
        df['margin_pct'] = df['margin_pct'].astype(float)
        df['historical_fill_rate'] = df['historical_fill_rate'].astype(float)
        df['lead_time_hours'] = df['lead_time_hours'].astype(float)
        df['base_price'] = df['base_price'].astype(float)
        
        # Replace NaN in output columns with empty strings
        for col in ['action_taken', 'discount_pct_applied', 'segment_notified', 'reasoning']:
            if col in df.columns:
                df[col] = df[col].fillna('')
                
        return df.to_dict('records')
    except FileNotFoundError:
        return []

def load_segments(file_path="data/segments.csv") -> List[Dict]:
    """Load segments as a list of dictionaries with fallback path handling."""
    target_path = file_path
    if not os.path.exists(target_path) and os.path.exists("segments.csv"):
        target_path = "segments.csv"
        
    try:
        return pd.read_csv(target_path).to_dict('records')
    except FileNotFoundError:
        return []

def get_time_category(time_block: str) -> str:
    """Categorize time block string into Mornings, Afternoons, or Evenings."""
    if not time_block:
        return "Evenings"
    time_str = str(time_block).upper()
    if "AM" in time_str:
        return "Mornings"
    if any(h in time_str for h in ["1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM"]):
        return "Afternoons"
    return "Evenings"

def match_segment(sport: str, segments: List[Dict], time_block: Optional[str] = None) -> str:
    """Find the best matching customer segment deterministically based on sport and preferred time."""
    sport_matches = [s for s in segments if s.get('preferred_sport') == sport]
    if not sport_matches:
        return "General Audience"
        
    if time_block:
        category = get_time_category(time_block)
        time_matches = [s for s in sport_matches if s.get('preferred_time') == category]
        if time_matches:
            return sorted(time_matches, key=lambda s: s.get('segment_id', ''))[0]['segment_name']
            
    # Deterministic fallback to first sport match by segment_id
    return sorted(sport_matches, key=lambda s: s.get('segment_id', ''))[0]['segment_name']

def apply_decision_to_slot(slot: Dict, decision: Dict, segments: List[Dict]) -> Dict:
    """Update a slot dictionary with the decision from the engine."""
    action = decision['action']
    slot['action_taken'] = action
    slot['discount_pct_applied'] = decision['discount_pct']
    slot['reasoning'] = decision['reasoning']
    
    if action in ['notify_only', 'notify_and_discount']:
        segment = match_segment(slot.get('sport_type', ''), segments, slot.get('time_block'))
        slot['segment_notified'] = segment
        slot['current_status'] = "notified"
        decision['segment_notified'] = segment
    else:
        slot['segment_notified'] = ""
        slot['current_status'] = "monitored"
        decision['segment_notified'] = None
        
    return slot

def save_slots(slots: List[Dict], file_path="data/slots.csv"):
    """Save the updated slots list back to CSV, synchronizing root and data files."""
    df = pd.DataFrame(slots)
    
    # Save to designated path
    os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
    df.to_csv(file_path, index=False)
    
    # Synchronize root / data copy if applicable
    if file_path == "data/slots.csv" and os.path.exists("slots.csv"):
        df.to_csv("slots.csv", index=False)
    elif file_path == "slots.csv" and os.path.exists("data/slots.csv"):
        df.to_csv("data/slots.csv", index=False)

