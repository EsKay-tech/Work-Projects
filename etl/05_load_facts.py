"""
Load dim_orders -> fact_order_items -> fact_reviews.

Run AFTER 01-04 (all other dimensions must be populated: facts look up
surrogate keys, and dim_date must cover every order date).

Idempotency:
- dim_orders:       filter on order_id      (natural key, from CSV)
- fact_order_items: filter on (order_key, order_item_id)  — key only
                    exists after the order_mapping merge, so the filter
                    sits after the merges
- fact_reviews:     filter on review_id     (natural key, from CSV)

Merge diagnostics print the row count after each inner join — a big
unexpected drop tells you which dimension is missing members.
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

conn = pyodbc.connect(CONN_STR)
cursor = conn.cursor()
cursor.fast_executemany = True

# =====================================================================
# STEP 1: dim_orders (idempotent)
# =====================================================================
df_orders = pd.read_csv(f'{DATA}/olist_orders_dataset.csv')
df_orders = df_orders.drop_duplicates(subset=['order_id'])

existing_orders = pd.read_sql("SELECT order_id FROM dbo.dim_orders", conn)
new_orders = df_orders[~df_orders['order_id'].isin(existing_orders['order_id'])]

dim_orders = new_orders[['order_id', 'order_status', 'order_purchase_timestamp']].copy()
dim_orders = dim_orders.astype(object).where(pd.notna(dim_orders), None)

if len(dim_orders) > 0:
    print(f"Inserting {len(dim_orders)} new orders...")
    cursor.executemany("""
        INSERT INTO dbo.dim_orders (order_id, order_status, order_purchase_timestamp)
        VALUES (?, ?, ?)
    """, dim_orders.values.tolist())
    conn.commit()
else:
    print("dim_orders: nothing new.")

# =====================================================================
# STEP 2: fetch dimension mappings (AFTER dim_orders is loaded)
# =====================================================================
order_mapping = pd.read_sql("SELECT order_key, order_id FROM dbo.dim_orders", conn)
products      = pd.read_sql("SELECT product_key, product_id FROM dbo.dim_products", conn)
sellers       = pd.read_sql("SELECT seller_key, seller_id FROM dbo.dim_sellers", conn)
customers     = pd.read_sql(
    "SELECT customer_key, customer_id FROM dbo.dim_customer WHERE is_current = 1", conn)
dates         = pd.read_sql("SELECT date_key FROM dbo.dim_date", conn)

# =====================================================================
# STEP 3: fact_order_items
# =====================================================================
df_order_items = pd.read_csv(f'{DATA}/olist_order_items_dataset.csv')
df_order_items = df_order_items.drop_duplicates(subset=['order_id', 'order_item_id'])
print(f"\nfact_order_items merge chain — start: {len(df_order_items)}")

fact = df_order_items.merge(order_mapping, on='order_id', how='inner')
print(f"  after orders:    {len(fact)}")

fact = fact.merge(products, on='product_id', how='inner')
print(f"  after products:  {len(fact)}")

fact = fact.merge(sellers, on='seller_id', how='inner')
print(f"  after sellers:   {len(fact)}")

fact = fact.merge(
    df_orders[['order_id', 'order_purchase_timestamp', 'customer_id']],
    on='order_id', how='inner'
)
fact = fact.merge(customers, on='customer_id', how='inner')
print(f"  after customers: {len(fact)}")

fact['date_key'] = pd.to_datetime(fact['order_purchase_timestamp']).dt.strftime('%Y%m%d')
fact = fact.merge(dates, on='date_key', how='inner')   # validates dim_date coverage
print(f"  after dates:     {len(fact)}")

# --- idempotency: composite key exists only after merges -------------
existing_items = pd.read_sql(
    "SELECT order_key, order_item_id FROM dbo.fact_order_items", conn)
if len(existing_items) > 0:
    fact = fact.merge(existing_items, on=['order_key', 'order_item_id'],
                      how='left', indicator=True)
    fact = fact[fact['_merge'] == 'left_only'].drop(columns=['_merge'])

fact_final = fact[[
    'order_key', 'order_item_id', 'customer_key', 'product_key',
    'seller_key', 'date_key', 'price', 'freight_value'
]].copy()
fact_final = fact_final.astype(object).where(pd.notna(fact_final), None)

if len(fact_final) > 0:
    print(f"Inserting {len(fact_final)} order items...")
    cursor.executemany("""
        INSERT INTO dbo.fact_order_items
        (order_key, order_item_id, customer_key, product_key,
         seller_key, date_key, price, freight_value)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, fact_final.values.tolist())
    conn.commit()
else:
    print("fact_order_items: nothing new.")

# =====================================================================
# STEP 4: fact_reviews
# =====================================================================
df_reviews = pd.read_csv(f'{DATA}/olist_order_reviews_dataset.csv')
df_reviews = df_reviews.drop_duplicates(subset=['review_id'])

existing_reviews = pd.read_sql("SELECT review_id FROM dbo.fact_reviews", conn)
df_reviews = df_reviews[~df_reviews['review_id'].isin(existing_reviews['review_id'])]

fact_reviews = df_reviews.merge(order_mapping, on='order_id', how='inner')
fact_reviews = fact_reviews[[
    'review_id', 'order_key', 'review_score',
    'review_comment_message', 'review_creation_date'
]].copy()
fact_reviews = fact_reviews.astype(object).where(pd.notna(fact_reviews), None)

if len(fact_reviews) > 0:
    print(f"Inserting {len(fact_reviews)} reviews...")
    cursor.executemany("""
        INSERT INTO dbo.fact_reviews
        (review_id, order_key, review_score, review_comment_message, review_creation_date)
        VALUES (?, ?, ?, ?, ?)
    """, fact_reviews.values.tolist())
    conn.commit()
else:
    print("fact_reviews: nothing new.")

cursor.close()
conn.close()
print("\n✓ Facts load complete!")
