# Thresholds and settings for the decision engine

# Risk scoring weights
WEIGHT_FILL_RATE = 0.6
WEIGHT_LEAD_TIME = 0.4

# Risk categories
RISK_THRESHOLD_HIGH = 0.7   # Score > 0.7 means high risk of remaining vacant
RISK_THRESHOLD_MEDIUM = 0.4 # Score > 0.4 means medium risk

# Margin constraints
MIN_REQUIRED_MARGIN_AFTER_DISCOUNT = 15.0 # Absolute minimum % margin we must retain

# Discounts
DISCOUNT_TIER_HIGH = 25.0
DISCOUNT_TIER_MED = 15.0
DISCOUNT_TIER_LOW = 10.0

# Normalization constants (for converting to 0-1 score)
MAX_LEAD_TIME_HOURS = 48.0 # Beyond 48h, lead time risk is 0
