# Brazilian E-Commerce Data Warehouse

> A production-grade dimensional data warehouse built from scratch, demonstrating end-to-end data engineering skills: dimensional modeling, ETL pipeline design, data quality validation, and idempotent transformations.

---

## 📊 Overview

This project implements a **star schema data warehouse** for the [Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbrazil/brazilian-ecommerce) (Olist). It transforms raw transactional data into an OLAP-optimized schema supporting analytical queries on customer behavior, product performance, and sales trends.

**Key achievements:**
- ✅ Designed 5-dimension star schema with 2 fact tables
- ✅ Implemented SCD Type 2 (slowly changing dimensions) for dim_customer
- ✅ Built idempotent ETL pipeline (~150K rows, 4 joins per fact)
- ✅ Clustered indexes optimized for OLAP time-series queries
- ✅ Data quality validation (deduplication, NULL handling, referential integrity)

---

## 🏗️ Architecture

### Star Schema Design

<img width="3060" height="2160" alt="olist_star_schema" src="https://github.com/user-attachments/assets/389f0def-bb7a-46c9-8739-596a179cbe41" />

### Design Decisions

**Grain:** One row per order_item (finest transactional grain)

**Surrogate Keys:** All FKs use surrogate keys (INT), not natural keys (strings)
- ✅ Faster joins (4-byte INT vs 255-byte NVARCHAR)
- ✅ Cleaner fact table structure
- ✅ Mapping happens during ETL, not at query time

**SCD Type 2 (dim_customer):** Tracks customer attribute changes
- Customer moves → close old record (end_date), insert new version
- Historical analysis: "What was this customer's profile on date X?"
- UNIQUE(customer_id, end_date) enforces one current version

**Separate Fact Tables:**
- `fact_order_items`: One row per item sold
- `fact_reviews`: One row per review (~90% sparse)
- Prevents duplicates when customers use multiple payment methods

**Clustered Index:** (date_key, product_key) for OLAP
- Time-series queries dominate ("last 30 days", "Q4 trends")
- Product analysis is common ("revenue by category")

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Database | SQL Server 2019 |
| ETL | Python 3.9+ |
| Data Manipulation | Pandas, NumPy |
| Batch Inserts | PyODBC |
| Date Logic | holidays (Brazil) |
| Testing | pytest |

---

## 📈 Data Flow

```
Source CSVs (Olist)
    ↓
Python ETL (etl/ directory)
    ├─ 01_load_dim_date.py       → 634 continuous calendar dates
    ├─ 02_load_dim_customer.py   → 99K customers (SCD Type 2)
    ├─ 03_load_dim_products.py   → 32,951 products
    ├─ 04_load_dim_sellers.py    → 3,088 sellers
    └─ 05_load_facts.py          → 1.1M items + 98K reviews
    ↓
SQL Server Warehouse (STAR SCHEMA)
    ↓
Analytics Queries
```

---

## 🚀 Quick Start

### Prerequisites
- SQL Server Express (local or Azure)
- Python 3.9+
- Git

### Setup (5 minutes)

```bash
# 1. Clone repo
git clone https://github.com/YOUR_USERNAME/data-warehouse-project.git
cd data-warehouse-project

# 2. Create database
sqlcmd -S localhost\SQLEXPRESS -E -Q "CREATE DATABASE data_warehouse"

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create schema
sqlcmd -S localhost\SQLEXPRESS -d data_warehouse -i sql/schema/01_create_schema.sql

# 5. Run ETL (in order!)
python etl/01_load_dim_date.py
python etl/02_load_dim_customer.py
python etl/03_load_dim_products.py
python etl/04_load_dim_sellers.py
python etl/05_load_facts.py

# ✅ Done!
```

See [docs/SETUP.md](docs/SETUP.md) for detailed instructions.

---

## 📁 Project Structure

```
data-warehouse-project/
├── sql/schema/
│   └── 01_create_schema.sql         # Star schema (re-runnable)
├── etl/
│   ├── 01_load_dim_date.py          # Continuous calendar
│   ├── 02_load_dim_customer.py      # SCD Type 2 logic
│   ├── 03_load_dim_products.py      # Product dimension
│   ├── 04_load_dim_sellers.py       # Seller dimension
│   └── 05_load_facts.py             # Fact table loading
├── docs/
│   ├── ARCHITECTURE.md              # Data model & design
│   ├── SETUP.md                     # Setup guide
│   └── PIPELINE.md                  # ETL explained
├── requirements.txt
└── README.md
```

---

## 🎯 Key Features

### ✅ Idempotent ETL
- Run twice → same result (no duplicates)
- Safe for production re-runs
- Filters before insert

### ✅ Data Quality Validation
- Deduplication on natural keys
- NULL handling (NaN → None)
- Referential integrity checks
- UNIQUE constraints as guardrails

### ✅ Best Practices
- Surrogate keys only in facts
- SCD Type 2 change tracking
- Batch inserts (100x faster)
- OLAP-optimized clustering

---

## 📚 What I Learned

**Dimensional Modeling** — Star schemas, SCD Type 2, grain definition  
**ETL Design** — Idempotency, data quality, batch operations  
**SQL Server** — Clustered indexes for OLAP, constraints as guardrails  
**Python Data Engineering** — Pandas merges, NULL handling, PyODBC batching  

---

## 📊 Sample Queries

```sql
-- Revenue by customer city
SELECT c.customer_city, SUM(f.payment_value)
FROM fact_order_items f
JOIN dim_customer c ON f.customer_key = c.customer_key
WHERE c.is_current = 1
GROUP BY c.customer_city;
```

---

## 🚦 Status

✅ Phase 1-3: Complete  
🔨 Phase 5: Documentation  

---

## 👤 Author

Built as a comprehensive data engineering portfolio project.

**Connect:** [LinkedIn](#) | [GitHub](#)
