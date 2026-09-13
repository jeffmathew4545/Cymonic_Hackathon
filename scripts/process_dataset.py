import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_loader import load_slots, load_segments, apply_decision_to_slot, save_slots
from src.engine import decide

def main():
    print("Loading slots and segments...")
    slots = load_slots("data/slots.csv")
    segments = load_segments("data/segments.csv")

    if not slots:
        print("No slots found! Checking root directory...")
        slots = load_slots("slots.csv")
        segments = load_segments("segments.csv")

    print(f"Loaded {len(slots)} slots and {len(segments)} segments.")

    processed_count = 0
    action_counts = {}

    for slot in slots:
        decision = decide(slot)
        apply_decision_to_slot(slot, decision, segments)
        processed_count += 1
        action = decision['action']
        action_counts[action] = action_counts.get(action, 0) + 1

    print("\nBatch Decision Processing Summary:")
    print("-" * 40)
    for action, count in action_counts.items():
        print(f"  {action.upper()}: {count} slots")

    print("\nSaving updated dataset to CSV files...")
    save_slots(slots, "data/slots.csv")
    save_slots(slots, "slots.csv")
    print("Successfully written output decisions to data/slots.csv and slots.csv!")

if __name__ == "__main__":
    main()
