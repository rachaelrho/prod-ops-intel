# Data Directory

This directory contains generated SQLite databases. These files are **not committed** to the repository.

## Generating Data

To recreate the databases locally:

```bash
# Step 1: Generate raw data with quality issues
python scripts/generate_raw_data.py

# Step 2: Clean and engineer features
python scripts/clean_and_prep.py
```

## Output Files

- `raw_ecommerce.db` - Raw data with realistic quality issues (duplicates, nulls, format inconsistencies)
- `ecommerce_clean.db` - Cleaned data with engineered features, ready for retrieval system

## Data Quality

The ETL pipeline handles:
- ~3-5% duplicate records
- ~8-10% missing customer information
- Mixed date formats
- ~5% null order statuses
- Email/location formatting inconsistencies
- ~20% missing acquisition channels

See `clean_and_prep.py` for full cleaning logic and feature engineering details.
