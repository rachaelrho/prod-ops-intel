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
import string
import logging
from datetime import datetime, timedelta
from pathlib import Path

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

# Product catalog - DTC skincare brand
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

# No PII - customers are anonymized

CITIES = [
    ("New York", "NY"), ("Los Angeles", "CA"), ("Chicago", "IL"), ("Houston", "TX"),
    ("Phoenix", "AZ"), ("Philadelphia", "PA"), ("San Antonio", "TX"), ("San Diego", "CA"),
    ("Dallas", "TX"), ("Austin", "TX"), ("Seattle", "WA"), ("Denver", "CO"),
    ("Portland", "OR"), ("Miami", "FL"), ("Atlanta", "GA"), ("Boston", "MA"),
]

ACQUISITION_CHANNELS = ["organic", "paid_social", "paid_search", "referral", "email", "influencer"]

ORDER_STATUSES = ["pending", "processing", "shipped", "delivered", "cancelled"]

RETURN_REASONS = [
    "changed_mind", "wrong_product", "skin_reaction", "damaged", "not_as_expected",
    "found_better_price", "too_expensive"
]


def generate_products():
    """Generate product catalog with minor data quality issues."""
    products = []
    product_id = 1

    for category, items in PRODUCT_CATEGORIES.items():
        for name, price, cost in items:
            # Introduce minor issues
            display_name = name
            display_category = category

            # 10% chance of trailing whitespace
            if random.random() < 0.10:
                display_name = display_name + "  "

            # 15% chance of inconsistent capitalization in category
            if random.random() < 0.15:
                display_category = category.lower()

            stock_level = random.randint(50, 500)
            restock_threshold = 100

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

        # 20% chance of case inconsistencies
        if random.random() < 0.20:
            email = email.upper()  # "CUSTOMER_0001@EXAMPLE.COM"

        # 10% chance of whitespace
        if random.random() < 0.10:
            email = " " + email + " "

        city, state = random.choice(CITIES)

        # 30% chance of state being spelled out vs abbreviated
        if random.random() < 0.30:
            state_full_names = {
                "NY": "New York", "CA": "California", "IL": "Illinois", "TX": "Texas",
                "AZ": "Arizona", "PA": "Pennsylvania", "WA": "Washington", "CO": "Colorado",
                "OR": "Oregon", "FL": "Florida", "GA": "Georgia", "MA": "Massachusetts"
            }
            state = state_full_names.get(state, state)

        # Acquisition channel - 20% missing (older customers)
        acquisition_channel = random.choice(ACQUISITION_CHANNELS) if random.random() > 0.20 else None

        # Customer created date (12-24 months ago)
        days_ago = random.randint(365, 730)
        created_at = datetime.now() - timedelta(days=days_ago)

        customers.append({
            "customer_id": i,
            "customer_ref": customer_ref,
            "email": email,
            "city": city,
            "state": state,
            "acquisition_channel": acquisition_channel,
            "created_at": created_at.strftime("%Y-%m-%d"),
        })

    return customers


def generate_orders(customers, products, n=1800):
    """Generate orders with significant data quality issues."""
    orders = []
    order_id = 1000

    # Generate clean orders first
    start_date = datetime.now() - timedelta(days=540)  # 18 months

    for _ in range(n):
        customer = random.choice(customers)

        # 10% guest checkout (missing customer link)
        customer_id = customer["customer_id"] if random.random() > 0.10 else None
        customer_email = customer["email"] if customer_id else None

        # Generate order date with temporal patterns
        # More orders on weekends, seasonal spikes
        days_offset = random.randint(0, 540)
        order_date = start_date + timedelta(days=days_offset)

        # Weekend spike
        if order_date.weekday() in [5, 6]:  # Sat/Sun
            if random.random() < 0.3:  # Skip 30% to reduce weekend volume slightly
                continue

        # Seasonal patterns (summer for SPF, winter for rich creams)
        month = order_date.month

        # Select product(s)
        num_items = random.choices([1, 2, 3], weights=[0.7, 0.2, 0.1])[0]
        order_items = random.sample(products, num_items)

        subtotal = sum(p["price"] for p in order_items)

        # Discount code (20% of orders)
        discount_applied = random.random() < 0.20
        if discount_applied:
            subtotal *= 0.9  # 10% off

        # Subscription (15% of orders)
        is_subscription = random.random() < 0.15

        # Order status distribution
        if (datetime.now() - order_date).days > 30:
            status = random.choices(ORDER_STATUSES, weights=[0.0, 0.0, 0.05, 0.90, 0.05])[0]
        elif (datetime.now() - order_date).days > 7:
            status = random.choices(ORDER_STATUSES, weights=[0.0, 0.05, 0.15, 0.75, 0.05])[0]
        else:
            status = random.choices(ORDER_STATUSES, weights=[0.1, 0.3, 0.4, 0.15, 0.05])[0]

        # 5% null status (data collection issue)
        if random.random() < 0.05:
            status = None

        # Return flag (10% overall, varies by factors)
        returned = False
        return_reason = None
        if status == "delivered":
            return_probability = 0.10
            # Higher return rate for certain categories
            if any(item["category"] in ["Serum", "Treatment"] for item in order_items):
                return_probability *= 1.3
            # Higher for expensive orders
            if subtotal > 80:
                return_probability *= 1.2

            if random.random() < return_probability:
                returned = True
                return_reason = random.choice(RETURN_REASONS)

        # Format date with inconsistencies
        date_format_choice = random.choice([1, 2, 3])
        if date_format_choice == 1:
            order_date_str = order_date.strftime("%Y-%m-%d")
        elif date_format_choice == 2:
            order_date_str = order_date.strftime("%m/%d/%Y")
        else:
            order_date_str = order_date.strftime("%Y-%m-%dT%H:%M:%S")

        # Create order
        for item in order_items:
            quantity = 1

            # 2% chance of negative quantity (return recorded as negative line item)
            if returned and random.random() < 0.02:
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

    # Now introduce duplicates (3-5% of orders)
    num_duplicates = int(len(orders) * random.uniform(0.03, 0.05))
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
