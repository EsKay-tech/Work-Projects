"""
Load dim_date — continuous calendar (no gaps), idempotent, batch insert.

Fixes vs previous version:
- Continuous pd.date_range instead of only dates that appear in orders
  (gap-free calendar: FKs never fail on quiet days, time-series can
  show zero-sales days).
- No DELETE FROM (would be blocked by the fact FK anyway) — inserts
  only date_keys not already present.
- executemany + fast_executemany instead of row-by-row.
"""

import pandas as pd
import numpy as np
import holidays
import pyodbc

CONN_STR = (
    'Driver={ODBC Driver 17 for SQL Server};'
    'Server=localhost\\SQLEXPRESS;'
    'Database=data_warehouse;'
    'Trusted_Connection=yes;'
)

# Cover the Olist data range with margin on both sides.
CALENDAR_START = '2016-01-01'
CALENDAR_END   = '2019-12-31'

# ---------------------------------------------------------------------
# Build the calendar
# ---------------------------------------------------------------------
dates = pd.date_range(start=CALENDAR_START, end=CALENDAR_END, freq='D')
df = pd.DataFrame({'d': dates})

df['date_key']         = df['d'].dt.strftime('%Y%m%d')
df['full_date']        = df['d'].dt.date
df['day_of_week']      = df['d'].dt.dayofweek + 1          # 1 = Monday
df['day_of_week_name'] = df['d'].dt.day_name()
df['day_of_month']     = df['d'].dt.day
df['month']            = df['d'].dt.month
df['month_name']       = df['d'].dt.month_name()
df['quarter']          = df['d'].dt.quarter
df['fiscal_year']      = df['d'].dt.year                    # Brazil: calendar year
df['is_weekend']       = np.where(df['d'].dt.dayofweek >= 5, 1, 0)

br_holidays = holidays.Brazil()
df['is_holiday'] = df['full_date'].apply(lambda x: 1 if x in br_holidays else 0)

dim_date = df[[
    'date_key', 'full_date', 'day_of_week', 'day_of_week_name',
    'day_of_month', 'month', 'month_name', 'quarter',
    'fiscal_year', 'is_weekend', 'is_holiday'
]].copy()

# ---------------------------------------------------------------------
# Idempotent load
# ---------------------------------------------------------------------
conn = pyodbc.connect(CONN_STR)
cursor = conn.cursor()
cursor.fast_executemany = True

existing = pd.read_sql("SELECT date_key FROM dbo.dim_date", conn)
new_rows = dim_date[~dim_date['date_key'].isin(existing['date_key'])]

if len(new_rows) > 0:
    print(f"Inserting {len(new_rows)} new dates...")
    cursor.executemany("""
        INSERT INTO dbo.dim_date
        (date_key, full_date, day_of_week, day_of_week_name, day_of_month,
         month, month_name, quarter, fiscal_year, is_weekend, is_holiday)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, new_rows.values.tolist())
    conn.commit()
else:
    print("dim_date: nothing new.")

cursor.close()
conn.close()
print(f"✓ dim_date complete ({len(dim_date)} calendar days, {len(new_rows)} inserted).")
