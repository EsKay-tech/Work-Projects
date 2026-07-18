"""
Load dim_sellers.

Fixes vs previous version:
- LEFT join to geolocation (enrichment): sellers with unmatched zip
  prefixes are kept with NULL coordinates instead of dropped.
- NaN -> None conversion added (was missing entirely).
- Idempotent: filters out seller_ids already loaded.
- executemany + fast_executemany instead of row-by-row.
- Fixed the "Inserting ... products" copy-paste prints.
- (Schema side: seller_zip_code_prefix is NVARCHAR to preserve leading
  zeros; lng is DECIMAL(11,8).)
"""

import os
import pandas as pd
import pyodbc

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
df             = pd.read_csv(f'{DATA}/olist_sellers_dataset.csv')
df_geolocation = pd.read_csv(f'{DATA}/olist_geolocation_dataset.csv')

df             = df.drop_duplicates(subset=['seller_id'])
df_geolocation = df_geolocation.drop_duplicates(subset=['geolocation_zip_code_prefix'])

# LEFT join: keep every seller; missing zips -> NULL coordinates
df_merged = df.merge(
    df_geolocation,
    left_on='seller_zip_code_prefix',
    right_on='geolocation_zip_code_prefix',
    how='left'
)

missing_geo = df_merged['geolocation_lat'].isna().sum()
print(f"Sellers: {len(df_merged)} | missing geolocation: {missing_geo}")

dim_sellers = df_merged[[
    'seller_id', 'seller_zip_code_prefix', 'seller_city',
    'seller_state', 'geolocation_lat', 'geolocation_lng'
]].copy()

# ---------------------------------------------------------------------
# Idempotent load
# ---------------------------------------------------------------------
conn = pyodbc.connect(CONN_STR)
cursor = conn.cursor()
cursor.fast_executemany = True

existing = pd.read_sql("SELECT seller_id FROM dbo.dim_sellers", conn)
new_rows = dim_sellers[~dim_sellers['seller_id'].isin(existing['seller_id'])].copy()

new_rows = new_rows.astype(object).where(pd.notna(new_rows), None)

if len(new_rows) > 0:
    print(f"Inserting {len(new_rows)} new sellers...")
    cursor.executemany("""
        INSERT INTO dbo.dim_sellers
        (seller_id, seller_zip_code_prefix, seller_city, seller_state,
         geolocation_lat, geolocation_lng)
        VALUES (?, ?, ?, ?, ?, ?)
    """, new_rows.values.tolist())
    conn.commit()
else:
    print("dim_sellers: nothing new.")

cursor.close()
conn.close()
print("✓ dim_sellers load complete!")
