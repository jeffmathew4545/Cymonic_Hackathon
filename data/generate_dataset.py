import random
from datetime import date, datetime, timedelta
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

NUM_FINE = 8
NUM_DESPERATE = 8
NUM_AMBIGUOUS = 20

OUTPUT_SLOTS = "slots.csv"
OUTPUT_SEGMENTS = "segments.csv"

# ------------------------------------------------------------
# Reference time for calculating lead_time_hours.
#
# This represents the moment when the optimisation engine runs.
# Change this value if you want to simulate a different date/time.
# ------------------------------------------------------------

REFERENCE_DATETIME = datetime(2026, 9, 13, 12, 0)

# Fixed random seed = reproducible dataset
random.seed(42)


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
# SPORT CONFIGURATION
# ============================================================

# Each sport contains:
#   time block
#   time category
#   base price
#   possible operating costs
#
# The operating cost is used internally to derive margin_pct.

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
        ],
        "operating_cost_range": (450, 850),
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
        ],
        "operating_cost_range": (400, 850),
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
        ],
        "operating_cost_range": (200, 650),
    },
}


# ============================================================
# DATE / TIME HELPERS
# ============================================================

def get_future_weekdays(count=40):
    """
    Generate future weekdays starting from the reference date.

    Weekends are excluded because the current dataset is
    intentionally focused mostly on weekday afternoon demand.
    """

    dates = []

    current = REFERENCE_DATETIME.date()

    while len(dates) < count:

        # Move to the next day
        current += timedelta(days=1)

        # Monday = 0 ... Sunday = 6
        if current.weekday() < 5:
            dates.append(current)

    return dates


def extract_start_hour(time_block):
    """
    Extract the starting hour from strings such as:

        '3:00 PM – 4:00 PM'
        '7:00 PM – 8:00 PM'

    Returns the 24-hour clock hour.
    """

    start_part = time_block.split("–")[0].strip()

    time_value, period = start_part.split(" ")

    hour, minute = map(int, time_value.split(":"))

    if period.upper() == "PM" and hour != 12:
        hour += 12

    if period.upper() == "AM" and hour == 12:
        hour = 0

    return hour


def calculate_lead_time(slot_date, time_block):
    """
    Calculate the actual number of hours between:

        REFERENCE_DATETIME
                    and
        slot start datetime

    Example:

        Reference:
        2026-09-13 12:00

        Slot:
        2026-09-15 15:00

        Lead time = 51 hours
    """

    start_hour = extract_start_hour(time_block)

    slot_start = datetime(
        slot_date.year,
        slot_date.month,
        slot_date.day,
        start_hour,
        0,
    )

    difference = slot_start - REFERENCE_DATETIME

    return round(difference.total_seconds() / 3600, 1)


# ============================================================
# SLOT / PRICE HELPERS
# ============================================================

def get_slot_details(sport, preferred_category):
    """
    Pick a time block and base price that belong to
    the requested sport and category.
    """

    options = SPORT_CONFIG[sport]["times"]

    matching = [
        item
        for item in options
        if item[1] == preferred_category
    ]

    # If there is no matching category,
    # fall back to any available slot for that sport.
    if not matching:
        matching = options

    return random.choice(matching)


def calculate_margin_pct(base_price, operating_cost):
    """
    Calculate the normal operating margin:

        margin % =
        (price - cost) / price * 100
    """

    margin = (
        (base_price - operating_cost)
        / base_price
    ) * 100

    return round(margin, 1)


def choose_operating_cost(sport, target_margin=None, base_price=None):
    """
    Choose an operating cost.

    If target_margin is supplied, the cost is calculated
    to approximately produce that margin.

    Otherwise a random cost is generated from the sport's
    configured cost range.
    """

    low, high = SPORT_CONFIG[sport]["operating_cost_range"]

    if target_margin is not None and base_price is not None:

        # Rearranging:
        #
        # margin = (price - cost) / price
        #
        # cost = price * (1 - margin)

        cost = base_price * (
            1 - target_margin / 100
        )

        return round(cost, 2)

    return round(random.uniform(low, high), 2)


# ============================================================
# CREATE ONE SLOT
# ============================================================

def create_slot(
    slot_number,
    slot_date,
    sport,
    category,
    fill_rate,
    target_margin=None,
):
    """
    Create one complete slot.

    Lead time is NOT randomly generated.

    It is calculated from:

        reference datetime
                  ↓
        slot date + time block
    """

    time_block, _, base_price = get_slot_details(
        sport,
        category
    )

    # --------------------------------------------------------
    # Calculate actual lead time
    # --------------------------------------------------------

    lead_time_hours = calculate_lead_time(
        slot_date,
        time_block
    )

    # --------------------------------------------------------
    # Choose operating cost
    # --------------------------------------------------------

    operating_cost = choose_operating_cost(
        sport,
        target_margin,
        base_price
    )

    # --------------------------------------------------------
    # Derive margin %
    # --------------------------------------------------------

    margin_pct = calculate_margin_pct(
        base_price,
        operating_cost
    )

    return {
        "slot_id": f"S{slot_number:04d}",

        "sport_type": sport,

        "date": slot_date.isoformat(),

        "time_block": time_block,

        "is_weekday": slot_date.weekday() < 5,

        # Derived from actual date + actual time
        "lead_time_hours": lead_time_hours,

        "historical_fill_rate": round(
            fill_rate,
            2
        ),

        "base_price": base_price,

        "margin_pct": margin_pct,

        "current_status": "vacant",

        # ----------------------------------------------------
        # Agent output columns
        # ----------------------------------------------------

        "action_taken": "",

        "discount_pct_applied": "",

        "segment_notified": "",

        "reasoning": "",
    }


# ============================================================
# GENERATE DATES
# ============================================================

dates = get_future_weekdays(40)

sports = list(SPORT_CONFIG.keys())

slots = []

slot_number = 1001


# ============================================================
# BUCKET 1 — OBVIOUSLY FINE
#
# High historical fill rate
# Long lead time
#
# Expected agent behaviour:
#     no_action
#
# IMPORTANT:
# We deliberately choose future dates that guarantee
# a lead time of at least ~15 hours.
# ============================================================

fine_candidates = [
    d for d in dates
    if calculate_lead_time(
        d,
        "3:00 PM – 4:00 PM"
    ) >= 15
]

for _ in range(NUM_FINE):

    sport = random.choice(sports)

    category = random.choice([
        "Afternoons",
        "Evenings"
    ])

    fill_rate = random.uniform(
        0.70,
        0.90
    )

    # Use a healthy margin for most "fine" cases.
    target_margin = random.choice([
        35,
        40,
        45,
        50,
        55,
    ])

    slot_date = random.choice(
        fine_candidates
    )

    slots.append(
        create_slot(
            slot_number,
            slot_date,
            sport,
            category,
            fill_rate,
            target_margin,
        )
    )

    slot_number += 1


# ============================================================
# BUCKET 2 — OBVIOUSLY DESPERATE
#
# Low historical fill rate
# Very short lead time
#
# Expected agent behaviour:
#     notify_and_discount
#
# We deliberately choose slot dates/times whose actual lead
# time falls between 0.5 and 3 hours.
# ============================================================

# ------------------------------------------------------------
# Find candidate slot starts from dates far enough in the
# future that we can still create a short lead time relative
# to the reference point.
#
# Since the reference time is fixed at 12:00 PM, the easiest
# way is to explicitly use the first future weekday when
# appropriate.
# ------------------------------------------------------------

desperate_candidates = []

for d in dates:

    for sport in sports:

        for time_block, category, _ in SPORT_CONFIG[sport]["times"]:

            lead = calculate_lead_time(
                d,
                time_block
            )

            if 0.5 <= lead <= 3.0:
                desperate_candidates.append(
                    (d, sport, category, time_block)
                )

# If the fixed reference date happens to have no suitable
# candidate because of the selected date range, create
# artificial candidates by using tomorrow's date.
#
# For the current reference date/time this should normally
# not be necessary, but keeping a fallback makes the
# generator robust.

if not desperate_candidates:

    tomorrow = REFERENCE_DATETIME.date() + timedelta(days=1)

    for sport in sports:

        # Manually use a time close to the reference time.
        # For example, 1 PM gives a 25-hour lead, so it won't
        # satisfy the 0.5–3 hour requirement.
        #
        # Therefore, for a future-day dataset, an exactly
        # "2-hours-from-now" slot requires the slot date to
        # equal the reference date.
        #
        # We handle this below using a special same-day date.
        pass


# ------------------------------------------------------------
# To guarantee genuinely short lead-time examples, we use
# the reference date itself for these simulated urgent slots.
#
# This is intentional: a real optimiser may run at noon while
# a 12:30 PM / 1 PM / 2 PM slot is still vacant.
# ------------------------------------------------------------

urgent_date = REFERENCE_DATETIME.date()

urgent_time_blocks = [
    ("12:30 PM – 1:30 PM", "Afternoons"),
    ("1:00 PM – 2:00 PM", "Afternoons"),
    ("2:00 PM – 3:00 PM", "Afternoons"),
]

for _ in range(NUM_DESPERATE):

    sport = random.choice(sports)

    time_block, category = random.choice(
        urgent_time_blocks
    )

    # Check the actual lead time.
    lead = calculate_lead_time(
        urgent_date,
        time_block
    )

    # The selected reference is 12:00 PM.
    # Therefore:
    # 12:30 PM -> 0.5 hours
    # 1:00 PM  -> 1 hour
    # 2:00 PM  -> 2 hours

    fill_rate = random.uniform(
        0.10,
        0.30
    )

    target_margin = random.choice([
        18,
        20,
        25,
        40,
        45,
    ])

    # Create the slot manually because the normal sport
    # configuration may not contain exactly these times.
    base_price = random.choice([
        item[2]
        for item in SPORT_CONFIG[sport]["times"]
        if item[1] == category
    ])

    operating_cost = choose_operating_cost(
        sport,
        target_margin,
        base_price
    )

    margin_pct = calculate_margin_pct(
        base_price,
        operating_cost
    )

    slots.append(
        {
            "slot_id": f"S{slot_number:04d}",
            "sport_type": sport,
            "date": urgent_date.isoformat(),
            "time_block": time_block,
            "is_weekday": urgent_date.weekday() < 5,
            "lead_time_hours": lead,
            "historical_fill_rate": round(
                fill_rate,
                2
            ),
            "base_price": base_price,
            "margin_pct": margin_pct,
            "current_status": "vacant",
            "action_taken": "",
            "discount_pct_applied": "",
            "segment_notified": "",
            "reasoning": "",
        }
    )

    slot_number += 1


# ============================================================
# BUCKET 3 — AMBIGUOUS MIDDLE
#
# Moderate fill rates
# Moderate lead times
# Mixed margins
#
# These are the cases where the optimiser must actually
# reason about the trade-offs.
# ============================================================

ambiguous_candidates = [
    d for d in dates
    if calculate_lead_time(
        d,
        "3:00 PM – 4:00 PM"
    ) >= 3
]

for _ in range(NUM_AMBIGUOUS):

    sport = random.choice(sports)

    category = random.choice([
        "Mornings",
        "Afternoons",
        "Evenings",
    ])

    fill_rate = random.uniform(
        0.31,
        0.69
    )

    target_margin = random.choice([
        15,
        18,
        20,
        25,
        30,
        35,
        40,
        45,
        50,
        55,
    ])

    slot_date = random.choice(
        ambiguous_candidates
    )

    slots.append(
        create_slot(
            slot_number,
            slot_date,
            sport,
            category,
            fill_rate,
            target_margin,
        )
    )

    slot_number += 1


# ============================================================
# SHUFFLE FINAL ROW ORDER
# ============================================================

# The underlying buckets are still deliberately constructed,
# but the rows appear in a mixed order in the CSV.

random.shuffle(slots)


# ============================================================
# CONVERT TO DATAFRAMES
# ============================================================

slots_df = pd.DataFrame(slots)


# ============================================================
# SAVE CSV FILES
# ============================================================

slots_df.to_csv(
    OUTPUT_SLOTS,
    index=False
)

segments_df.to_csv(
    OUTPUT_SEGMENTS,
    index=False
)


# ============================================================
# DISPLAY SUMMARY
# ============================================================

print("=" * 60)
print("SPORTS LOT OPTIMISER - DATASET GENERATOR")
print("=" * 60)

print(
    f"\nReference datetime: "
    f"{REFERENCE_DATETIME}"
)

print(
    f"\nCreated: {OUTPUT_SLOTS}"
)

print(
    f"Rows: {len(slots_df)}"
)

print(
    f"\nCreated: {OUTPUT_SEGMENTS}"
)

print(
    f"Rows: {len(segments_df)}"
)


# ------------------------------------------------------------
# Sport distribution
# ------------------------------------------------------------

print("\nSports distribution:")

print(
    slots_df["sport_type"].value_counts()
)


# ------------------------------------------------------------
# Lead-time information
# ------------------------------------------------------------

print("\nLead-time statistics:")

print(
    f"Minimum: "
    f"{slots_df['lead_time_hours'].min():.1f} hours"
)

print(
    f"Maximum: "
    f"{slots_df['lead_time_hours'].max():.1f} hours"
)

print(
    f"Average: "
    f"{slots_df['lead_time_hours'].mean():.1f} hours"
)


# ------------------------------------------------------------
# Fill-rate information
# ------------------------------------------------------------

print("\nHistorical fill-rate range:")

print(
    f"Minimum: "
    f"{slots_df['historical_fill_rate'].min():.2f}"
)

print(
    f"Maximum: "
    f"{slots_df['historical_fill_rate'].max():.2f}"
)


# ------------------------------------------------------------
# Margin information
# ------------------------------------------------------------

print("\nMargin statistics:")

print(
    f"Minimum: "
    f"{slots_df['margin_pct'].min():.1f}%"
)

print(
    f"Maximum: "
    f"{slots_df['margin_pct'].max():.1f}%"
)

print(
    f"Average: "
    f"{slots_df['margin_pct'].mean():.1f}%"
)


# ------------------------------------------------------------
# Preview
# ------------------------------------------------------------

print("\nPreview of slots.csv:")

print(
    slots_df.head(10).to_string(
        index=False
    )
)

print("\nPreview of segments.csv:")

print(
    segments_df.to_string(
        index=False
    )
)

print("\nDataset generation complete.")
