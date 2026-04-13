"""
Generate raw e-commerce data with realistic data quality issues.

IMPORTANT: All data is synthetic. Names, emails, and personal information are
randomly generated and do not represent real individuals.

This script simulates what a client would export from their e-commerce platform:
- Duplicate records from payment retries
- Missing values from guest checkouts and incomplete data collection
- Inconsistent formatting (dates, emails, capitalization)
- Data entry errors (negative quantities from returns)

Seed is fixed for reproducibility.
"""

import sqlite3
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path

from config import (
    PRODUCT_CATEGORIES,
    CITIES,
    STATE_ABBREV_TO_FULL,
    ACQUISITION_CHANNELS,
    ORDER_STATUSES,
    RETURN_REASONS,
    DATE_FORMATS,
    DATA_QUALITY_CONFIG,
    ORDER_STATUS_WEIGHTS,
    RETURN_PROBABILITY_CONFIG,
    INVENTORY_CONFIG,
    TEMPORAL_CONFIG,
    ORDER_COMPOSITION,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Fixed seed for reproducibility
random.seed(42)

# Database path (scripts are in scripts/ directory, data is in data/)
DB_PATH = Path(__file__).parent.parent / "data" / "raw_ecommerce.db"
DB_PATH.parent.mkdir(exist_ok=True)


def generate_products():
    """Generate product catalog with minor data quality issues."""
    products = []
    product_id = 1

    for category, items in PRODUCT_CATEGORIES.items():
        for name, price, cost in items:
            # Introduce minor issues
            display_name = name
            display_category = category

            # Apply data quality issues based on config
            if random.random() < DATA_QUALITY_CONFIG['product_whitespace_prob']:
                display_name = display_name + "  "

            if random.random() < DATA_QUALITY_CONFIG['product_case_inconsistency_prob']:
                display_category = category.lower()

            stock_level = random.randint(
                INVENTORY_CONFIG['stock_level_min'],
                INVENTORY_CONFIG['stock_level_max']
            )
            restock_threshold = INVENTORY_CONFIG['restock_threshold']

            products.append({
                "product_id": product_id,
                "name": display_name,
                "category": display_category,
                "price": price,
                "cost": cost,
                "stock_level": stock_level,
                "restock_threshold": restock_threshold,
            })
            product_id += 1

    return products


def generate_customers(n=500):
    """Generate anonymized customers with realistic data quality issues."""
    customers = []

    for i in range(1, n + 1):
        # Anonymized customer reference
        customer_ref = f"CUST_{i:04d}"

        # Anonymized email (some with formatting issues)
        email = f"customer_{i:04d}@example.com"

        # Apply data quality issues based on config
        if random.random() < DATA_QUALITY_CONFIG['email_case_inconsistency_prob']:
            email = email.upper()

        if random.random() < DATA_QUALITY_CONFIG['email_whitespace_prob']:
            email = " " + email + " "

        city, state = random.choice(CITIES)

        # Expand state abbreviation to full name for some records
        if random.random() < DATA_QUALITY_CONFIG['state_full_name_prob']:
            state = STATE_ABBREV_TO_FULL.get(state, state)

        # Missing acquisition channel based on config probability
        if random.random() < DATA_QUALITY_CONFIG['missing_acquisition_channel_prob']:
            acquisition_channel = None
        else:
            acquisition_channel = random.choice(ACQUISITION_CHANNELS)

        # Customer created date
        days_ago = random.randint(
            TEMPORAL_CONFIG['customer_age_days_min'],
            TEMPORAL_CONFIG['customer_age_days_max']
        )
        created_at = datetime.now() - timedelta(days=days_ago)

        customers.append({
            "customer_id": i,
            "customer_ref": customer_ref,
            "email": email,
            "city": city,
            "state": state,
            "acquisition_channel": acquisition_channel,
            "created_at": created_at.strftime(DATE_FORMATS['iso']),
        })

    return customers


def generate_orders(customers, products, n=1800):
    """Generate orders with significant data quality issues."""
    orders = []
    order_id = 1000

    # Generate clean orders first
    start_date = datetime.now() - timedelta(days=TEMPORAL_CONFIG['order_history_days'])

    for _ in range(n):
        customer = random.choice(customers)

        # Guest checkout (missing customer link)
        customer_id = customer["customer_id"] if random.random() > DATA_QUALITY_CONFIG['guest_checkout_prob'] else None
        customer_email = customer["email"] if customer_id else None

        # Generate order date with temporal patterns
        # More orders on weekends, seasonal spikes
        days_offset = random.randint(0, TEMPORAL_CONFIG['order_history_days'])
        order_date = start_date + timedelta(days=days_offset)

        # Weekend spike
        if order_date.weekday() in [5, 6]:  # Sat/Sun
            if random.random() < DATA_QUALITY_CONFIG['weekend_skip_prob']:  # Skip to reduce weekend volume slightly
                continue

        # Seasonal patterns (summer for SPF, winter for rich creams)
        month = order_date.month

        # Select product(s)
        num_items = random.choices(
            ORDER_COMPOSITION['items_per_order'],
            weights=ORDER_COMPOSITION['items_weights']
        )[0]
        order_items = random.sample(products, num_items)

        subtotal = sum(p["price"] for p in order_items)

        # Discount code
        discount_applied = random.random() < DATA_QUALITY_CONFIG['discount_applied_prob']
        if discount_applied:
            subtotal *= DATA_QUALITY_CONFIG['discount_amount']  # 10% off

        # Subscription
        is_subscription = random.random() < DATA_QUALITY_CONFIG['subscription_prob']

        # Order status distribution based on age
        days_old = (datetime.now() - order_date).days
        status_config = None
        for config in ORDER_STATUS_WEIGHTS:
            if days_old >= config['min_days']:
                status_config = config
                break

        if status_config:
            status = random.choices(
                list(status_config['weights'].keys()),
                weights=list(status_config['weights'].values())
            )[0]
        else:
            status = 'pending'  # fallback

        # Null status (data collection issue)
        if random.random() < DATA_QUALITY_CONFIG['null_status_prob']:
            status = None

        # Return flag (varies by factors)
        returned = False
        return_reason = None
        if status == "delivered":
            return_probability = DATA_QUALITY_CONFIG['base_return_prob']
            # Higher return rate for certain categories
            if any(item["category"] in RETURN_PROBABILITY_CONFIG['high_return_categories'] for item in order_items):
                return_probability *= RETURN_PROBABILITY_CONFIG['category_multiplier']
            # Higher for expensive orders
            if subtotal > RETURN_PROBABILITY_CONFIG['high_value_threshold']:
                return_probability *= RETURN_PROBABILITY_CONFIG['value_multiplier']

            if random.random() < return_probability:
                returned = True
                return_reason = random.choice(RETURN_REASONS)

        # Format date with inconsistencies
        date_format_choice = random.choice([1, 2, 3])
        if date_format_choice == 1:
            order_date_str = order_date.strftime(DATE_FORMATS['iso'])
        elif date_format_choice == 2:
            order_date_str = order_date.strftime(DATE_FORMATS['us'])
        else:
            order_date_str = order_date.strftime(DATE_FORMATS['iso_timestamp'])

        # Create order
        for item in order_items:
            quantity = 1

            # Chance of negative quantity (return recorded as negative line item)
            if returned and random.random() < DATA_QUALITY_CONFIG['negative_quantity_prob']:
                quantity = -1

            orders.append({
                "order_id": order_id,
                "customer_id": customer_id,
                "customer_email": customer_email,
                "order_date": order_date_str,
                "product_id": item["product_id"],
                "quantity": quantity,
                "price": item["price"],
                "discount_applied": discount_applied,
                "is_subscription": is_subscription,
                "order_status": status,
                "returned": returned,
                "return_reason": return_reason,
            })

        order_id += 1

    # Now introduce duplicates
    num_duplicates = int(len(orders) * random.uniform(
        DATA_QUALITY_CONFIG['duplicate_rate_min'],
        DATA_QUALITY_CONFIG['duplicate_rate_max']
    ))
    for _ in range(num_duplicates):
        original = random.choice(orders)
        duplicate = original.copy()
        orders.append(duplicate)

    return orders


def create_database(products, customers, orders):
    """Create SQLite database with raw tables."""
    # Remove existing database
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Products table
    cursor.execute("""
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            name TEXT,
            category TEXT,
            price REAL,
            cost REAL,
            stock_level INTEGER,
            restock_threshold INTEGER
        )
    """)

    for p in products:
        cursor.execute("""
            INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (p["product_id"], p["name"], p["category"], p["price"],
              p["cost"], p["stock_level"], p["restock_threshold"]))

    # Customers table
    cursor.execute("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            customer_ref TEXT,
            email TEXT,
            city TEXT,
            state TEXT,
            acquisition_channel TEXT,
            created_at TEXT
        )
    """)

    for c in customers:
        cursor.execute("""
            INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (c["customer_id"], c["customer_ref"], c["email"],
              c["city"], c["state"], c["acquisition_channel"], c["created_at"]))

    # Orders table
    cursor.execute("""
        CREATE TABLE orders (
            order_id INTEGER,
            customer_id INTEGER,
            customer_email TEXT,
            order_date TEXT,
            product_id INTEGER,
            quantity INTEGER,
            price REAL,
            discount_applied INTEGER,
            is_subscription INTEGER,
            order_status TEXT,
            returned INTEGER,
            return_reason TEXT
        )
    """)

    for o in orders:
        cursor.execute("""
            INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (o["order_id"], o["customer_id"], o["customer_email"], o["order_date"],
              o["product_id"], o["quantity"], o["price"], o["discount_applied"],
              o["is_subscription"], o["order_status"], o["returned"], o["return_reason"]))

    conn.commit()
    conn.close()

    logger.info(f"Created raw database at {DB_PATH}")
    logger.info(f"  {len(products)} products")
    logger.info(f"  {len(customers)} customers")
    logger.info(f"  {len(orders)} order line items")


if __name__ == "__main__":
    logger.info("Generating raw e-commerce data with realistic quality issues...")

    products = generate_products()
    logger.info(f"Generated {len(products)} products (with whitespace and capitalization issues)")

    customers = generate_customers(500)
    logger.info(f"Generated {len(customers)} customers (with email/location formatting issues)")

    orders = generate_orders(customers, products, 1800)
    logger.info(f"Generated {len(orders)} order records (with duplicates, nulls, and format issues)")

    create_database(products, customers, orders)

    logger.info("Data generation complete.")
    logger.info("")
    logger.info("Expected data quality issues:")
    logger.info("  3-5% duplicate order IDs")
    logger.info("  8-10% missing customer information")
    logger.info("  Mixed date formats across records")
    logger.info("  5% null order statuses")
    logger.info("  Email case inconsistencies and whitespace")
    logger.info("  Inconsistent state formatting")
    logger.info("  20% missing acquisition channels")
