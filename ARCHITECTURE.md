# Data Warehouse Architecture & Design Decisions

## Dimensional Modeling Overview

Dimensional modeling organizes data into:
- **Dimensions:** WHO, WHAT, WHERE, WHEN (descriptive attributes)
- **Facts:** Measurements and events (quantitative)

**Why Star Schema?**
- ✅ Fast analytical queries (minimal joins)
- ✅ Reusable dimensions across facts
- ✅ Intuitive for business users
- ✅ Natural for OLAP (online analytical processing)

---

## Star Schema Design

### Visual Architecture

```
                    dim_date (634 rows)
                    Calendar dimension
                          │
        dim_customer       │       dim_products
        (SCD Type 2)       │       (32,951)
        (99,441)           │
              │            │            │
              └────────────┼────────────┘
                           │
                 fact_order_items (1.1M)
                 Grain: one row per order_item
                 Clustered: (date_key, product_key)
                           │
               ┌───────────┼───────────┐
               │           │           │
          dim_sellers   fact_reviews
          (3,088)       (98,410 reviews)
```

---

## Dimension Tables

### dim_date (Time Dimension)

**Purpose:** Enable time-based analysis without coupling dates to transactions

**Key Features:**
- **Continuous calendar** (2016-2019): No gaps → Foreign keys never fail
- **YYYYMMDD format** (20260718): Human-readable, sortable
- **Pre-calculated attributes:** quarter, day_of_week, is_weekend, is_holiday (Brazil)
- **634 rows**

**Why Separate?**
- Consistent date keys across all facts
- Pre-computed time calculations (month, quarter, fiscal year)
- Time-based drill-down capability

---

### dim_customer (SCD Type 2)

**Purpose:** Track customer attributes AND their changes over time

**Why SCD Type 2?**
- Historical analysis: "What was this customer's city on date X?"
- Change detection: Close old record, insert new version when attributes change
- Enforced via UNIQUE(customer_id, end_date)

**Example:**
```
Customer moves from São Paulo to Rio de Janeiro:

BEFORE:
customer_key=1, customer_id='C001', city='São Paulo'
start_date=2020-01-01, end_date=NULL, is_current=1

AFTER MOVE:
customer_key=1, customer_id='C001', city='São Paulo'
start_date=2020-01-01, end_date=2020-06-30, is_current=0

customer_key=2, customer_id='C001', city='Rio de Janeiro'
start_date=2020-07-01, end_date=NULL, is_current=1
```

**Queries:**
```sql
-- Get current customer info
WHERE is_current = 1

-- Get customer as of historical date
WHERE start_date <= @date AND (end_date IS NULL OR end_date >= @date)
```

**Implementation in ETL:**
```python
# Merge new with existing current records
merged = new_data.merge(existing_current, on='customer_id', how='left', suffixes=('_new', '_old'))

# Detect changes
changed = merged[(merged['city_new'] != merged['city_old']) | (merged['state_new'] != merged['state_old'])]

# For each changed customer:
# 1. UPDATE dim_customer SET end_date=today, is_current=0 WHERE customer_id='C001' AND is_current=1
# 2. INSERT new version with start_date=today, is_current=1
```

**Row Count:** 99,441 (includes SCD Type 2 history versions)

---

### dim_products (32,951 rows)

- **Surrogate key:** product_key (INT IDENTITY)
- **Natural key:** product_id (UNIQUE)
- **Attributes:** category (English translated), dimensions, weight, photos
- **SCD Type 1:** Overwrite on change (products don't change often)

---

### dim_sellers (3,088 rows)

**Challenge:** Geolocation CSV had multiple coordinates per zip code (different neighborhoods)

**Solution:**
```python
# Deduplicate geolocation FIRST (keep first per zip)
geo_dedup = df_geo.drop_duplicates(subset=['zip_code'], keep='first')

# Then LEFT JOIN sellers
sellers = sellers.merge(geo_dedup, how='left')
```

---

## Fact Tables

### fact_order_items (1.1M rows) - Primary Fact

**Grain:** One row per order_item

**Why This Grain?**
- Order 'O001' contains 3 items (products A, B, C):
  ```
  order_key  order_item_id  product_key  price   freight
  1          1              10           100.00  10.00
  1          2              11           50.00   5.00
  1          3              12           75.00   7.50
  ```
- **Benefits:** Clean product mapping, freight allocation per item, revenue by product analysis easy

**Clustered Index:** (date_key, product_key)

**Why NOT cluster on grain (order_key, order_item_id)?**
- OLAP queries filter by DATE + PRODUCT, not order_id
- Typical query: "Sales by product, this month?" → date_key + product_key
- Analytical use never starts with "give me order #12345"
- (date_key, product_key) supports most analytical patterns

---

### fact_reviews (98,410 rows) - Secondary Fact

**Grain:** One row per review (different grain from order_items!)

**Why Separate?**
- Reviews are **sparse:** ~90% of orders never get reviewed
- If stored in fact_order_items: 1.1M rows with 90% NULLs in review columns
- Separate table: 98K dense rows + INNER/LEFT JOIN when needed

**Analysis with Both Facts:**
```sql
SELECT 
    oi.order_key,
    SUM(oi.payment_value) as total_spent,
    AVG(r.review_score) as avg_rating
FROM fact_order_items oi
LEFT JOIN fact_reviews r ON oi.order_key = r.order_key
GROUP BY oi.order_key
```

---

## Design Decisions

### 1. Surrogate Keys (INT) vs Natural Keys (VARCHAR)

**Decision:** Fact tables store ONLY surrogate keys (INT)

| Aspect | Surrogate (INT) | Natural (VARCHAR) |
|--------|-----------------|------------------|
| Storage | 4 bytes | 255 bytes |
| Join Performance | Fast (int comparison) | Slow (string comparison) |
| Index Size | Small | Large |
| Human Readable | No | Yes |

**Example:**
```sql
-- ✅ Good: Surrogate key in fact
fact_order_items (
    customer_key INT,       -- 4 bytes
)

-- ❌ Bad: Natural key in fact  
fact_order_items (
    customer_id VARCHAR(255),  -- 255 bytes
)
```

**Mapping Happens in ETL:**
```python
# During transformation, lookup customer_key from natural key
fact = fact.merge(
    dim_customer[['customer_key', 'customer_id']],
    on='customer_id'
)
```

### 2. Idempotent ETL

**Requirement:** Pipeline can run multiple times → same result (no duplicates)

**Why?**
- Production requirement (safety)
- Enables re-runs after failures
- Supports scheduled/automated execution

**Implementation:**
```python
existing = pd.read_sql("SELECT customer_id FROM dim_customer WHERE is_current=1", conn)
new_customers = df[~df['customer_id'].isin(existing['customer_id'])]

if len(new_customers) > 0:
    cursor.executemany(INSERT_SQL, new_customers.values.tolist())
```

**Guards:**
- Existence checks before insert
- UNIQUE constraints prevent duplicates
- UNIQUE(order_key, order_item_id) for facts
- UNIQUE(customer_id, end_date) for SCD Type 2

---

## Example Queries

### Revenue by Customer City (Last 30 Days)

```sql
SELECT TOP 10
    c.customer_city,
    COUNT(DISTINCT f.order_key) as orders,
    SUM(f.payment_value) as revenue
FROM fact_order_items f
INNER JOIN dim_customer c ON f.customer_key = c.customer_key
INNER JOIN dim_date d ON f.date_key = d.date_key
WHERE c.is_current = 1
  AND d.full_date >= DATEADD(day, -30, GETDATE())
GROUP BY c.customer_city
ORDER BY revenue DESC;
```

### Product Category Performance by Quarter

```sql
SELECT 
    d.fiscal_year,
    d.quarter,
    p.product_category_name_english,
    COUNT(*) as items_sold,
    SUM(f.price) as revenue
FROM fact_order_items f
INNER JOIN dim_products p ON f.product_key = p.product_key
INNER JOIN dim_date d ON f.date_key = d.date_key
WHERE d.fiscal_year = 2018
GROUP BY d.fiscal_year, d.quarter, p.product_category_name_english
ORDER BY d.quarter, revenue DESC;
```

### Review Scores vs Order Value

```sql
SELECT 
    CASE WHEN r.review_score >= 4 THEN 'Satisfied' ELSE 'Unsatisfied' END as satisfaction,
    COUNT(*) as orders,
    AVG(f.payment_value) as avg_order_value,
    AVG(CAST(r.review_score as FLOAT)) as avg_rating
FROM fact_order_items f
LEFT JOIN fact_reviews r ON f.order_key = r.order_key
GROUP BY CASE WHEN r.review_score >= 4 THEN 'Satisfied' ELSE 'Unsatisfied' END
ORDER BY orders DESC;
```

---

## Performance & Scalability

### Current Optimization
- ✅ Clustered index on (date_key, product_key) for range scans
- ✅ Batch inserts (executemany) instead of row-by-row
- ✅ Surrogate key joins (4-byte INT vs strings)
- ✅ UNIQUE constraints prevent index bloat from duplicates

### If Growing 10x (11M facts)
1. **Partitioning:** Partition by date ranges (year/quarter)
2. **Aggregation tables:** Pre-aggregate daily/weekly summaries
3. **Column store:** CLUSTERED COLUMNSTORE for better compression

---

## Summary

**This architecture optimizes for OLAP:**
- ✅ Fast dimensional queries (filter by customer, product, date)
- ✅ Reusable dimensions (shared across facts)
- ✅ Historical analysis (SCD Type 2)
- ✅ Data quality guardrails (UNIQUE, idempotency)
- ✅ Performance (INT FKs, clustered on analytical access patterns)

Perfect for **business intelligence and analytics on dimensional data.**
