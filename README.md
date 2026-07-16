# Sean Karabo Nkosi — Data Analysis & Statistics Portfolio

**Business Intelligence Analyst** · SQL Server · BigQuery · Python

This repository collects my Python projects across data wrangling, exploratory data
analysis, statistical inference, and predictive modelling. My SQL Server, BigQuery, and
data-warehousing work sits in my professional experience — this repo focuses on the
Python analysis and statistics side.

📍 Johannesburg, South Africa  ·  [LinkedIn](https://linkedin.com/in/ADD-HANDLE)  ·  karabo.mn33@gmail.com

---

## 🛠️ Tech Stack

`Python` · `pandas` · `NumPy` · `statsmodels` · `scikit-learn` · `scipy` · `seaborn` / `matplotlib` · `GeoPandas`

---

## 📊 Projects

### Credit Card Approval Prediction
Predicts whether a credit card application is approved: data cleaning, missing-value
imputation, categorical encoding, and training and evaluating a classification model.
**Demonstrates:** preprocessing · classification · model evaluation
**Stack:** Python, pandas, scikit-learn
📁 `Credit Card Approvals/`  ·  _[add key result, e.g. model accuracy]_

### Employee Salary Regression Analysis
A simple linear regression (statsmodels OLS) quantifying how years of experience predict
salary — with IQR-based outlier removal, train/test split, R² and p-value significance
interpretation, Pearson correlation with hypothesis testing, and RMSE-based overfitting
evaluation.
**Demonstrates:** linear regression · hypothesis testing · model evaluation
**Stack:** Python, statsmodels, scipy, seaborn
📁 `Employee Salary Regression Analysis/`

### Statistical Thinking
Applied probability and statistics: distributions, exploratory data analysis, hypothesis
testing, and confidence-interval estimation — the inference foundations behind sound analysis.
**Demonstrates:** probability · hypothesis testing · EDA
**Stack:** Python, pandas, NumPy
📁 `Statistical Thinking/`

### Financial Services Access in Tanzania (Finscope 2017)
Cleaned and validated a ~10,000-record survey dataset against a data dictionary, separated
continuous vs. categorical descriptive statistics, and explored the demographic drivers of
financial-service usage.
**Demonstrates:** data validation · descriptive statistics · EDA
**Stack:** Python, pandas, seaborn, GeoPandas
📁 `Financial Services Access in Tanzania/`

### Recruit Personality Scoring
Wrangled questionnaire data (deduplication, null handling, column normalisation) and computed
Big-Five subscale scores, with integrity assertions guaranteeing row and column consistency
across joins.
**Demonstrates:** data wrangling · integrity checks · feature construction
**Stack:** Python, pandas
📁 `Recruit Personality Scoring/`

---

## 📁 Repository Structure

```
.
├── Credit Card Approvals/
├── Employee Salary Regression Analysis/
├── Financial Services Access in Tanzania/
├── Recruit Personality Scoring/
├── Statistical Thinking/
└── README.md
```

## ▶️ Running the Notebooks

```bash
# clone, then create an environment
python -m venv .venv && source .venv/bin/activate
pip install pandas numpy scikit-learn statsmodels scipy seaborn geopandas jupyter
jupyter notebook
```

---

_These began as guided projects and were extended and annotated as I built out my data
analysis and statistics foundations._
