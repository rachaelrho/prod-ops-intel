"""
Configuration for data generation and ETL pipelines.
Centralizes mappings, thresholds, and data quality parameters.
"""

# ============================================================================
# REFERENCE DATA
# ============================================================================

PRODUCT_CATEGORIES = {
    "Cleanser": [
        ("Gentle Foaming Cleanser", 24.00, 8.50),
        ("Hydrating Cream Cleanser", 26.00, 9.00),
        ("Exfoliating Gel Cleanser", 28.00, 9.50),
        ("Oil Cleanser", 32.00, 11.00),
    ],
    "Serum": [
        ("Vitamin C Brightening Serum", 48.00, 14.00),
        ("Hyaluronic Acid Serum", 42.00, 12.50),
        ("Retinol Night Serum", 52.00, 15.00),
        ("Niacinamide Serum", 38.00, 11.50),
        ("Peptide Firming Serum", 56.00, 16.50),
    ],
    "Moisturizer": [
        ("Daily Hydrating Moisturizer", 36.00, 12.00),
        ("Night Cream", 44.00, 14.00),
        ("Oil-Free Gel Moisturizer", 34.00, 11.00),
        ("Rich Barrier Cream", 48.00, 15.00),
        ("Eye Cream", 42.00, 13.50),
    ],
    "SPF": [
        ("Mineral Sunscreen SPF 50", 32.00, 10.50),
        ("Tinted Sunscreen SPF 45", 36.00, 11.50),
        ("Hydrating Sunscreen SPF 30", 30.00, 9.50),
    ],
    "Treatment": [
        ("AHA/BHA Exfoliating Toner", 28.00, 9.00),
        ("Vitamin C Mask", 38.00, 12.00),
        ("Overnight Sleeping Mask", 40.00, 13.00),
    ],
    "Set": [
        ("Starter Skincare Set", 89.00, 32.00),
        ("Anti-Aging Duo", 98.00, 35.00),
        ("Hydration Bundle", 76.00, 28.00),
    ],
}

CITIES = [
    ("New York", "NY"), ("Los Angeles", "CA"), ("Chicago", "IL"), ("Houston", "TX"),
    ("Phoenix", "AZ"), ("Philadelphia", "PA"), ("San Antonio", "TX"), ("San Diego", "CA"),
    ("Dallas", "TX"), ("Austin", "TX"), ("Seattle", "WA"), ("Denver", "CO"),
    ("Portland", "OR"), ("Miami", "FL"), ("Atlanta", "GA"), ("Boston", "MA"),
]

# State mappings used in both generation and cleaning
STATE_MAPPINGS = {
    # Lowercase full name -> Abbreviation (for cleaning)
    'new york': 'NY',
    'california': 'CA',
    'illinois': 'IL',
    'texas': 'TX',
    'arizona': 'AZ',
    'pennsylvania': 'PA',
    'washington': 'WA',
    'colorado': 'CO',
    'oregon': 'OR',
    'florida': 'FL',
    'georgia': 'GA',
    'massachusetts': 'MA'
}

# Reverse mapping: Abbreviation -> Full name (for data generation)
STATE_ABBREV_TO_FULL = {v: k.title() for k, v in STATE_MAPPINGS.items()}

ACQUISITION_CHANNELS = ["organic", "paid_social", "paid_search", "referral", "email", "influencer"]

ORDER_STATUSES = ["pending", "processing", "shipped", "delivered", "cancelled"]

RETURN_REASONS = [
    "changed_mind", "wrong_product", "skin_reaction", "damaged",
    "not_as_expected", "found_better_price", "too_expensive"
]

# ============================================================================
# DATE FORMATS
# ============================================================================

DATE_FORMATS = {
    'iso': "%Y-%m-%d",
    'us': "%m/%d/%Y",
    'iso_timestamp': "%Y-%m-%dT%H:%M:%S"
}

# List of formats for parsing (order matters - try most specific first)
DATE_PARSE_FORMATS = [
    DATE_FORMATS['iso'],
    DATE_FORMATS['us'],
    DATE_FORMATS['iso_timestamp']
]

# ============================================================================
# DATA QUALITY PARAMETERS
# ============================================================================

DATA_QUALITY_CONFIG = {
    # Product generation
    'product_whitespace_prob': 0.10,
    'product_case_inconsistency_prob': 0.15,

    # Customer generation
    'email_case_inconsistency_prob': 0.20,
    'email_whitespace_prob': 0.10,
    'state_full_name_prob': 0.30,
    'missing_acquisition_channel_prob': 0.20,

    # Order generation
    'guest_checkout_prob': 0.10,
    'weekend_skip_prob': 0.30,
    'discount_applied_prob': 0.20,
    'discount_amount': 0.9,  # 10% off
    'subscription_prob': 0.15,
    'null_status_prob': 0.05,
    'base_return_prob': 0.10,
    'negative_quantity_prob': 0.02,
    'duplicate_rate_min': 0.03,
    'duplicate_rate_max': 0.05,
}

# ============================================================================
# ORDER STATUS LOGIC
# ============================================================================

ORDER_STATUS_WEIGHTS = [
    # (min_days, status_weights) - checked in order from most recent
    # Format: days_threshold, then dict of status: probability
    {
        'min_days': 30,
        'label': 'old',
        'weights': {
            'pending': 0.0,
            'processing': 0.0,
            'shipped': 0.05,
            'delivered': 0.90,
            'cancelled': 0.05
        }
    },
    {
        'min_days': 7,
        'label': 'medium',
        'weights': {
            'pending': 0.0,
            'processing': 0.05,
            'shipped': 0.15,
            'delivered': 0.75,
            'cancelled': 0.05
        }
    },
    {
        'min_days': 0,
        'label': 'recent',
        'weights': {
            'pending': 0.1,
            'processing': 0.3,
            'shipped': 0.4,
            'delivered': 0.15,
            'cancelled': 0.05
        }
    }
]

# ============================================================================
# RETURN PROBABILITY MODIFIERS
# ============================================================================

RETURN_PROBABILITY_CONFIG = {
    'high_return_categories': ['Serum', 'Treatment'],
    'category_multiplier': 1.3,
    'high_value_threshold': 80,
    'value_multiplier': 1.2,
}

# ============================================================================
# SEASON MAPPING
# ============================================================================

MONTH_TO_SEASON = {
    1: 'winter', 2: 'winter',
    3: 'spring', 4: 'spring', 5: 'spring',
    6: 'summer', 7: 'summer', 8: 'summer',
    9: 'fall', 10: 'fall', 11: 'fall',
    12: 'winter'
}

# ============================================================================
# ORDER STATUS IMPUTATION RULES (for ETL cleaning)
# ============================================================================

STATUS_IMPUTATION_RULES = [
    # (threshold_days, status) - checked in order, first match wins
    (30, 'delivered'),
    (7, 'shipped'),
    (0, 'processing')  # default for all others
]

# ============================================================================
# INVENTORY & PRODUCT SETTINGS
# ============================================================================

INVENTORY_CONFIG = {
    'stock_level_min': 50,
    'stock_level_max': 500,
    'restock_threshold': 100,
}

# ============================================================================
# TEMPORAL SETTINGS
# ============================================================================

TEMPORAL_CONFIG = {
    'order_history_days': 540,  # 18 months
    'customer_age_days_min': 365,  # 12 months
    'customer_age_days_max': 730,  # 24 months
}

# ============================================================================
# ORDER COMPOSITION
# ============================================================================

ORDER_COMPOSITION = {
    'items_per_order': [1, 2, 3],
    'items_weights': [0.7, 0.2, 0.1],
}
