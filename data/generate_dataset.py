import random
from datetime import date, timedelta
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

NUM_FINE = 8
NUM_DESPERATE = 8
NUM_AMBIGUOUS = 20

TOTAL_ROWS = NUM_FINE + NUM_DESPERATE + NUM_AMBIGUOUS

OUTPUT_SLOTS = "slots.csv"
OUTPUT_SEGMENTS = "segments.csv"

# Fixed seed makes the generated dataset reproducible.
random.seed(41)


# ============================================================
# SEGMENTS DATA
# ============================================================

segments = [
    {
        "segment_id": "SEG01",
        "segment_name": "College Cricket Group",
        "preferred_sport": "Cricket",
        "preferred_time": "Afternoons",
        "price_sensitivity": "High",
    },
    {
        "segment_id": "SEG02",
        "segment_name": "Corporate Badminton League",
        "preferred_sport": "Badminton",
        "preferred_time": "Evenings",
        "price_sensitivity": "Low",
    },
    {
        "segment_id": "SEG03",
        "segment_name": "Weekend Regulars",
        "preferred_sport": "Football",
        "preferred_time": "Evenings",
        "price_sensitivity": "Medium",
    },
    {
        "segment_id": "SEG04",
        "segment_name": "Corporate Football League",
        "preferred_sport": "Football",
        "preferred_time": "Evenings",
        "price_sensitivity": "Low",
    },
    {
        "segment_id": "SEG05",
        "segment_name": "Student Badminton Club",
        "preferred_sport": "Badminton",
        "preferred_time": "Afternoons",
        "price_sensitivity": "High",
    },
    {
        "segment_id": "SEG06",
        "segment_name": "Family Weekend Players",
        "preferred_sport": "Football",
        "preferred_time": "Afternoons",
        "price_sensitivity": "Medium",
    },
    {
        "segment_id": "SEG07",
        "segment_name": "Local Cricket Friends",
        "preferred_sport": "Cricket",
        "preferred_time": "Evenings",
        "price_sensitivity": "Medium",
    },
]

segments_df = pd.DataFrame(segments)


# ============================================================
# SLOT GENERATION HELPERS
# ============================================================

SPORT_CONFIG = {
    "Football": {
        "times": [
            ("2:00 PM – 3:00 PM", "Afternoons", 1000),
            ("3:00 PM – 4:00 PM", "Afternoons", 1000),
            ("4:00 PM – 5:00 PM", "Afternoons", 1100),
            ("5:00 PM – 6:00 PM", "Evenings", 1200),
            ("6:00 PM – 7:00 PM", "Evenings", 1300),
            ("7:00 PM – 8:00 PM", "Evenings", 1300),
            ("8:00 PM – 9:00 PM", "Evenings", 1300),
        ]
    },
    "Cricket": {
        "times": [
            ("1:00 PM – 2:00 PM", "Afternoons", 900),
            ("2:00 PM – 3:00 PM", "Afternoons", 900),
            ("3:00 PM – 4:00 PM", "Afternoons", 1000),
            ("4:00 PM – 5:00 PM", "Afternoons", 1100),
            ("5:00 PM – 6:00 PM", "Evenings", 1200),
            ("6:00 PM – 7:00 PM", "Evenings", 1200),
            ("7:00 PM – 8:00 PM", "Evenings", 1200),
        ]
    },
    "Badminton": {
        "times": [
            ("8:00 AM – 9:00 AM", "Mornings", 600),
            ("9:00 AM – 10:00 AM", "Mornings", 600),
            ("3:00 PM – 4:00 PM", "Afternoons", 700),
            ("4:00 PM – 5:00 PM", "Afternoons", 700),
            ("5:00 PM – 6:00 PM", "Evenings", 800),
            ("6:00 PM – 7:00 PM", "Evenings", 800),
            ("7:00 PM – 8:00 PM", "Evenings", 800),
        ]
    },
}


def get_future_weekdays(count=30):
    """
    Generate upcoming weekdays starting from tomorrow.
    Weekends are excluded so that most/all generated slots are weekdays.
    """
    dates = []

    current = date.today() + timedelta(days=1)

    while len(dates) < count:
        if current.weekday() < 5:  # Monday = 0, Friday = 4
            dates.append(current)

        current += timedelta(days=1)

    return dates


def get_slot_details(sport, preferred_category):
    """
    Pick a time block and base price.
    preferred_category can be:
    Mornings / Afternoons / Evenings
    """
    options = SPORT_CONFIG[sport]["times"]

    matching = [
        item for item in options
        if item[1] == preferred_category
    ]

    if not matching:
        matching = options

    return random.choice(matching)


def calculate_margin(base_price, margin_pct):
    """
    Convert margin percentage into an approximate cost.
    The cost is not stored because your current schema
    doesn't require it, but this shows the intended relationship.
    """
    return base_price * (margin_pct / 100)


def create_slot(
    slot_number,
    slot_date,
    sport,
    category,
    lead_time,
    fill_rate,
    margin_pct,
):
    time_block, _, base_price = get_slot_details(sport, category)

    return {
        "slot_id": f"S{slot_number:04d}",
        "sport_type": sport,
        "date": slot_date.isoformat(),
        "time_block": time_block,
        "is_weekday": slot_date.weekday() < 5,
        "lead_time_hours": round(lead_time, 1),
        "historical_fill_rate": round(fill_rate, 2),
        "base_price": base_price,
        "margin_pct": margin_pct,
        "current_status": "vacant",

        # These are outputs of your agent.
        # They intentionally start blank.
        "action_taken": "",
        "discount_pct_applied": "",
        "segment_notified": "",
        "reasoning": "",
    }


# ============================================================
# CREATE SLOT DATA
# ============================================================

dates = get_future_weekdays(40)

sports = list(SPORT_CONFIG.keys())

slots = []
slot_number = 1001


# ------------------------------------------------------------
# BUCKET 1: OBVIOUSLY FINE
# High fill rate + long lead time
# Expected agent behaviour: no_action
# ------------------------------------------------------------

for _ in range(NUM_FINE):

    sport = random.choice(sports)
    category = random.choice(["Afternoons", "Evenings"])

    fill_rate = random.uniform(0.70, 0.90)
    lead_time = random.uniform(15, 36)

    # Healthy or moderate margins
    margin_pct = random.choice([35, 40, 45, 50, 55])

    slots.append(
        create_slot(
            slot_number,
            random.choice(dates),
            sport,
            category,
            lead_time,
            fill_rate,
            margin_pct,
        )
    )

    slot_number += 1


# ------------------------------------------------------------
# BUCKET 2: OBVIOUSLY DESPERATE
# Low fill rate + short lead time
# Expected agent behaviour: notify_and_discount
# ------------------------------------------------------------

for _ in range(NUM_DESPERATE):

    sport = random.choice(sports)
    category = random.choice(["Afternoons", "Evenings"])

    fill_rate = random.uniform(0.10, 0.30)
    lead_time = random.uniform(0.5, 3.0)

    # Mix healthy and thin margins.
    # Thin margins force the agent to be careful with discount size.
    margin_pct = random.choice([18, 20, 25, 40, 45])

    slots.append(
        create_slot(
            slot_number,
            random.choice(dates),
            sport,
            category,
            lead_time,
            fill_rate,
            margin_pct,
        )
    )

    slot_number += 1


# ------------------------------------------------------------
# BUCKET 3: AMBIGUOUS MIDDLE
# Mixed fill rate + mixed lead time + mixed margin
#
# These cases are deliberately not obvious.
# ------------------------------------------------------------

for _ in range(NUM_AMBIGUOUS):

    sport = random.choice(sports)

    category = random.choice([
        "Mornings",
        "Afternoons",
        "Evenings",
    ])

    # Middle-range historical demand
    fill_rate = random.uniform(0.31, 0.69)

    # Anything from very short to fairly long lead time
    lead_time = random.uniform(3.0, 18.0)

    # Some slots have tight margins and others are healthy.
    margin_pct = random.choice([
        15, 18, 20, 25,
        30, 35, 40,
        45, 50, 55
    ])

    slots.append(
        create_slot(
            slot_number,
            random.choice(dates),
            sport,
            category,
            lead_time,
            fill_rate,
            margin_pct,
        )
    )

    slot_number += 1


# ============================================================
# SHUFFLE ROWS
# ============================================================
# We shuffle only the final row order.
# The three buckets remain intentionally represented in the data.

random.shuffle(slots)


slots_df = pd.DataFrame(slots)


# ============================================================
# SAVE CSV FILES
# ============================================================

slots_df.to_csv(OUTPUT_SLOTS, index=False)
segments_df.to_csv(OUTPUT_SEGMENTS, index=False)


# ============================================================
# DISPLAY SUMMARY
# ============================================================

print("=" * 60)
print("Sports Lot Optimiser - Dataset Generator")
print("=" * 60)

print(f"\nCreated: {OUTPUT_SLOTS}")
print(f"Rows: {len(slots_df)}")

print(f"\nCreated: {OUTPUT_SEGMENTS}")
print(f"Rows: {len(segments_df)}")


print("\nSports distribution:")
print(slots_df["sport_type"].value_counts())


print("\nHistorical fill-rate ranges:")
print(
    f"Minimum: {slots_df['historical_fill_rate'].min():.2f}"
)
print(
    f"Maximum: {slots_df['historical_fill_rate'].max():.2f}"
)


print("\nLead-time ranges:")
print(
    f"Minimum: {slots_df['lead_time_hours'].min():.1f} hours"
)
print(
    f"Maximum: {slots_df['lead_time_hours'].max():.1f} hours"
)


print("\nMargin distribution:")
print(slots_df["margin_pct"].value_counts().sort_index())


print("\nPreview of slots.csv:")
print(slots_df.head(10).to_string(index=False))

print("\nPreview of segments.csv:")
print(segments_df.to_string(index=False))

print("\nDataset generation complete.")
