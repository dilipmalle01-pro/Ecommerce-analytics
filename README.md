# 🛒 E-Commerce Sales Analytics Pipeline

An end-to-end real-time data analytics project built to answer
critical business questions for an e-commerce company losing
revenue without knowing where, when, or why.

---

## 📌 Problem Statement

> "An e-commerce company is losing revenue but doesn't know
> where, when, or why."

This project builds a complete analytics system that identifies:
- Underperforming product categories
- High late delivery rates by region
- Low-rated seller segments
- Customer payment behaviour patterns
- Geographic revenue concentration

---

## 🏗️ Architecture
REST API (Fake Store) ──┐

├──► Python Ingestion ──► PostgreSQL (Star Schema)

Olist Dataset (100K+) ──┘         │                      │

Airflow DAGs            dbt Models

│

Power BI Dashboard
---

## 📊 Dashboard Pages

| Page | Description |
|---|---|
| Revenue Overview | Monthly trends, top categories, KPI cards |
| Delivery Analysis | Late orders, delay by state, trends |
| Customer & Payments | City revenue, payment methods, trends |
| Seller Performance | Top sellers, ratings, state revenue |

---

## 🔍 Key Findings

| Finding | Insight |
|---|---|
| 📈 Peak Revenue | November 2017 — R$987,765 |
| 🚚 Late Deliveries | 8.1% of orders arrive late by avg 9 days |
| 🏆 Top Category | Health & Beauty — R$3.69M revenue |
| 💳 Payment | Credit card = 78% of all transactions |
| 🌆 Top City | São Paulo — R$1.85M (2x nearest competitor) |
| ⭐ Avg Rating | 4.09 / 5.0 across all orders |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Ingestion | Python, requests, Apache Airflow |
| Storage | PostgreSQL, AWS S3 |
| Transformation | SQL, dbt Core |
| Analysis | pandas, numpy, matplotlib, seaborn |
| Visualization | Power BI Desktop |
| Deployment | AWS EC2, Docker |
| Version Control | Git, GitHub |

---

## 📁 Project Structure
ecommerce-analytics/

├── raw_data/              # Raw CSV files (not tracked)

├── clean_data/            # Cleaned CSV files

├── charts/                # EDA chart outputs

├── data_cleaning.py       # Data cleaning script

├── load_to_postgres.py    # PostgreSQL loader

├── eda.py                 # Exploratory data analysis

├── .env                   # DB credentials (not tracked)

└── README.md
---

## 🚀 How to Run

**1. Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/ecommerce-analytics.git
cd ecommerce-analytics
```

**2. Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**3. Set up environment variables**
```bash
# Create .env file with your PostgreSQL credentials
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ecommerce_db
DB_USER=postgres
DB_PASSWORD=your_password
```

**4. Run data cleaning**
```bash
python data_cleaning.py
```

**5. Load to PostgreSQL**
```bash
python load_to_postgres.py
```

**6. Run EDA**
```bash
python eda.py
```

---

## 📦 Dataset

- **Olist Brazilian E-Commerce** — 100,000+ real orders (2016-2018)
- **Fake Store API** — Live product and order data
- Source: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

---

## 👤 Author

**Dilip Kumar Malle**
- LinkedIn: [linkedin.com/in/dilipmalle]
- Email: [dilipmalle01@gmail.com]