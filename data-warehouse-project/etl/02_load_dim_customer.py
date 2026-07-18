"""
Load dim_customer — SCD Type 2.

Fixes vs previous version:
- LEFT join to geolocation (enrichment, not a qualifier): customers
  with unmatched zip prefixes are kept with NULL coordinates instead
  of being silently dropped (which also killed their fact rows later).
- No column rename; merge uses left_on/right_on, so natural column
  names survive — this also removes the row.customer_zip_code_prefix
  AttributeError landmine in the changed-customers loop.
- NaN -> None conversion on BOTH insert paths.
- Batch insert for new customers (fast_executemany).

SCD2 behaviour (unchanged):
- New customer_id            -> INSERT (start_date=today, is_current=1)
- Changed city/state         -> close old row (end_date, is_current=0),
                                INSERT new version
- Unchanged                  -> no-op  (this IS the idempotency)
"""

import os
import pandas as pd
import pyodbc
from datetime import datetime

CONN_STR = (
    'Driver={ODBC Driver 17 for SQL Server};'
    'Server=localhost\\SQLEXPRESS;'
    'Database=data_warehouse;'
    'Trusted_Connection=yes;'
)

DATA = os.path.join(os.path.dirname(__file__), '..', 'data', 'sample-data')

# ---------------------------------------------------------------------
# Extract + transform
# ---------------------------------------------------------------------
customer_df    = pd.read_csv(f'{DATA}/olist_customers_dataset.csv')
geolocation_df = pd.read_csv(f'{DATA}/olist_geolocation_dataset.csv')

geolocation_df = geolocation_df.drop_duplicates(subset=['geolocation_zip_code_prefix'])
customer_df    = customer_df.drop_duplicates(subset=['customer_id'])

# LEFT join: geolocation is enrichment; unmatched zips -> NULL coords
dim_customer = customer_df.merge(
    geolocation_df,
    left_on='customer_zip_code_prefix',
    right_on='geolocation_zip_code_prefix',
    how='left'
)

missing_geo = dim_customer['geolocation_lat'].isna().sum()
print(f"Customers: {len(dim_customer)} | missing geolocation: {missing_geo}")

# ---------------------------------------------------------------------
# SCD Type 2 load
# ---------------------------------------------------------------------
conn = pyodbc.connect(CONN_STR)
cursor = conn.cursor()
cursor.fast_executemany = True

today = datetime.now().date()

existing = pd.read_sql(
    "SELECT customer_id, customer_city, customer_state "
    "FROM dbo.dim_customer WHERE is_current = 1",
    conn
)

merged = dim_customer.merge(existing, on='customer_id', how='left',
                            suffixes=('_new', '_old'))

# 1. NEW customers: no current version in the dimension
new_customers = merged[merged['customer_city_old'].isna()].copy()

# 2. CHANGED customers: city or state differs from current version
existing_in_merged = merged[merged['customer_city_old'].notna()].copy()
changed_mask = (
    (existing_in_merged['customer_city_new']  != existing_in_merged['customer_city_old']) |
    (existing_in_merged['customer_state_new'] != existing_in_merged['customer_state_old'])
)
changed_customers = existing_in_merged[changed_mask].copy()

INSERT_SQL = """
    INSERT INTO dbo.dim_customer
    (customer_id, customer_zip_code_prefix, customer_city,
     customer_state, geolocation_lat, geolocation_lng, geolocation_city,
     geolocation_state, start_date, is_current)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
"""

INSERT_COLS = [
    'customer_id', 'customer_zip_code_prefix', 'customer_city_new',
    'customer_state_new', 'geolocation_lat', 'geolocation_lng',
    'geolocation_city', 'geolocation_state'
]

# --- 3. Insert NEW customers (batch) ---------------------------------
new_ordered = new_customers[INSERT_COLS].copy()
new_ordered['start_date'] = today
new_ordered = new_ordered.astype(object).where(pd.notna(new_ordered), None)

if len(new_ordered) > 0:
    print(f"Inserting {len(new_ordered)} new customers...")
    cursor.executemany(INSERT_SQL, new_ordered.values.tolist())
else:
    print("No new customers.")

# --- 4. Handle CHANGED customers (close old, insert new version) -----
print(f"Updating {len(changed_customers)} changed customers...")
changed_ordered = changed_customers[INSERT_COLS].copy()
changed_ordered = changed_ordered.astype(object).where(pd.notna(changed_ordered), None)

for row in changed_ordered.itertuples(index=False):
    cursor.execute("""
        UPDATE dbo.dim_customer
        SET end_date = ?, is_current = 0
        WHERE customer_id = ? AND is_current = 1
    """, (today, row.customer_id))

    cursor.execute(INSERT_SQL, tuple(row) + (today,))

conn.commit()
cursor.close()
conn.close()
print("✓ dim_customer SCD Type 2 load complete!")
