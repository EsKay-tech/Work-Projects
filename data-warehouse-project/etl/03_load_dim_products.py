"""
Load dim_products.

Fixes vs previous version:
- Idempotent: filters out product_ids already in the dimension, so a
  re-run inserts nothing instead of dying on UQ_dim_products_product_id.
- executemany + fast_executemany instead of row-by-row.
- (Schema side, see 01_create_schema.sql: name-length columns are INT,
  measures are DECIMAL(10,2), category name is nullable and NOT unique.)
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
df             = pd.read_csv(f'{DATA}/olist_products_dataset.csv')
df_translation = pd.read_csv(f'{DATA}/product_category_name_translation.csv')

df = df.drop_duplicates(subset=['product_id'])

# LEFT join: keep products whose category has no English translation
dim_products = df.merge(df_translation, on='product_category_name', how='left')

# Nullable integer types preserve NULLs (1.9% of rows) — standard
# practice: NULL means "not available", don't fabricate 0s.
for col in ['product_name_lenght', 'product_description_lenght', 'product_photos_qty']:
    dim_products[col] = dim_products[col].astype('Int64')

COLS = [
    'product_id', 'product_category_name', 'product_name_lenght',
    'product_description_lenght', 'product_photos_qty', 'product_weight_g',
    'product_length_cm', 'product_height_cm', 'product_width_cm',
    'product_category_name_english'
]
dim_products = dim_products[COLS].copy()

# ---------------------------------------------------------------------
# Idempotent load
# ---------------------------------------------------------------------
conn = pyodbc.connect(CONN_STR)
cursor = conn.cursor()
cursor.fast_executemany = True

existing = pd.read_sql("SELECT product_id FROM dbo.dim_products", conn)
new_rows = dim_products[~dim_products['product_id'].isin(existing['product_id'])].copy()

# NaN / pd.NA -> None so pyodbc sends SQL NULL
new_rows = new_rows.astype(object).where(pd.notna(new_rows), None)

if len(new_rows) > 0:
    print(f"Inserting {len(new_rows)} new products...")
    cursor.executemany("""
        INSERT INTO dbo.dim_products
        (product_id, product_category_name, product_name_lenght,
         product_description_lenght, product_photos_qty, product_weight_g,
         product_length_cm, product_height_cm, product_width_cm,
         product_category_name_english)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, new_rows.values.tolist())
    conn.commit()
else:
    print("dim_products: nothing new.")

cursor.close()
conn.close()
print("✓ dim_products load complete!")
