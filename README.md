# Sean Karabo Nkosi — Data & Analytics Portfolio

**Business Intelligence & Data Analyst** · SQL Server · BigQuery · Python

A collection of my data projects spanning data wrangling, exploratory analysis,
statistical inference, and predictive modelling. My SQL / data-warehousing work is
highlighted first; the applied projects below demonstrate Python analysis and statistics.

📍 Johannesburg, South Africa  ·  [LinkedIn](https://linkedin.com/in/ADD-HANDLE)  ·  karabo.mn33@gmail.com

---

## 🛠️ Tech Stack

`Python` · `pandas` · `NumPy` · `statsmodels` · `scikit-learn` · `scipy` ·
`seaborn` / `matplotlib` · `GeoPandas` · `SQL Server` · `T-SQL` · `BigQuery` · `dbt` · `pyodbc`

---

## ⭐ Featured Build — Olist E-Commerce Data Warehouse

> _If this lives in another repo, link it here — it's the strongest piece for data-modelling roles._

A star-schema data warehouse over the Olist Brazilian e-commerce dataset:
fact and dimension tables with **surrogate keys** and **Slowly Changing Dimensions (SCD Type 2)**,
a Python ETL pipeline, and loading of dimension and fact tables into **SQL Server** via `pyodbc`.

**Demonstrates:** dimensional modelling · ETL design · SQL Server · Python data engineering
**Repo / notebook:** _[add link]_

---

## 📊 Applied Projects

### Statistical Thinking
Applied probability and statistics: distributions, exploratory data analysis,
hypothesis testing, and confidence intervals — the inference foundations behind sound analysis.
**Techniques:** EDA · probability · hypothesis testing
**Stack:** Python, pandas, NumPy
`→ statistical-thinking/`

### Credit Card Approval Prediction
Predicts whether a credit card application is approved. Covers data cleaning, missing-value
handling, categorical encoding, and training and evaluating a classification model.
**Techniques:** preprocessing · classification · model evaluation
**Stack:** Python, pandas, scikit-learn
`→ credit-card-approval-prediction/`  ·  _[add key result, e.g. model accuracy]_

### Cross-Validation & Simple Linear Regression
Fits a simple linear regression and evaluates it properly using cross-validation
to gauge how well the model generalises beyond the training data.
**Techniques:** linear regression · k-fold cross-validation · train/test evaluation
**Stack:** Python, pandas, scikit-learn
`→ cross-validation-linear-regression/`

### Financial Services Access in Tanzania (Finscope 2017)
Cleaned and validated a ~10,000-record survey dataset against a data dictionary,
separated continuous vs. categorical descriptive statistics, and explored the
demographic drivers of financial-service usage.
**Techniques:** data validation · descriptive statistics · EDA
**Stack:** Python, pandas, seaborn, GeoPandas
`→ financial-services-tanzania/`

### Data Wrangling
Turning messy, real-world data into analysis-ready tables: deduplication, null handling,
column normalisation, and integrity checks to guarantee consistency across joins.
**Techniques:** data cleaning · reshaping · integrity assertions
**Stack:** Python, pandas
`→ data-wrangling/`

---

## 📁 Repository Structure

```
.
├── olist-data-warehouse/                 # ⭐ featured — dimensional model (or link out)
├── statistical-thinking/
├── credit-card-approval-prediction/
├── cross-validation-linear-regression/
├── financial-services-tanzania/
└── data-wrangling/
```

## ▶️ Running the Notebooks

```bash
# clone, then create an environment
python -m venv .venv && source .venv/bin/activate
pip install pandas numpy scikit-learn statsmodels scipy seaborn geopandas jupyter
jupyter notebook
```

---

_Applied projects began as guided exercises and were extended/annotated as I built out my
analysis and statistics foundations. Featured builds are original end-to-end work._
