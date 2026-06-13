import pandas as pd
import numpy as np
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import os

load_dotenv()

CLEAN = "clean_data/"

# ---- Database connection ----
def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

# ---- Safe bulk insert ----
def bulk_insert(conn, table, df, cols):
    df = df[cols].copy()
    df = df.drop_duplicates()
    df = df.where(pd.notnull(df), None)
    rows = [tuple(r) for r in df.itertuples(index=False)]
    if not rows:
        print(f"  No rows to insert into {table}")
        return
    sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES %s ON CONFLICT DO NOTHING"
    with conn.cursor() as cur:
        execute_values(cur, sql, rows)
    conn.commit()
    print(f"  Loaded {len(rows):,} rows into {table}")

# ---- 1. Customers ----
def load_customers(conn):
    print("Loading customers...")
    df = pd.read_csv(CLEAN + "customers_clean.csv")
    df = df.rename(columns={
        "customer_zip_code_prefix": "zip_code",
        "customer_city":            "city",
        "customer_state":           "state"
    })
    bulk_insert(conn, "dim_customers",
                df, ["customer_id","customer_unique_id",
                     "zip_code","city","state"])

# ---- 2. Products ----
def load_products(conn):
    print("Loading products...")
    df = pd.read_csv(CLEAN + "products_clean.csv")
    df = df.rename(columns={
        "product_name_lenght":        "product_name_length",
        "product_description_lenght": "product_description_length"
    })
    bulk_insert(conn, "dim_products", df, [
        "product_id","product_category_name",
        "product_category_name_english",
        "product_name_length","product_description_length",
        "product_photos_qty","product_weight_g",
        "product_length_cm","product_height_cm","product_width_cm"
    ])

# ---- 3. Sellers ----
def load_sellers(conn):
    print("Loading sellers...")
    df = pd.read_csv(CLEAN + "sellers_clean.csv")
    df.columns = ["seller_id","zip_code","city","state"]
    bulk_insert(conn, "dim_sellers",
                df, ["seller_id","zip_code","city","state"])

# ---- 4. Dates ----
def load_dates(conn):
    print("Loading dates...")
    orders = pd.read_csv(CLEAN + "orders_clean.csv",
                         parse_dates=["order_purchase_timestamp"])
    min_date = orders["order_purchase_timestamp"].min().date()
    max_date = orders["order_purchase_timestamp"].max().date()
    dates = pd.date_range(min_date, max_date, freq="D")
    df = pd.DataFrame({
        "date_id":     [d.date() for d in dates],
        "year":        dates.year,
        "quarter":     dates.quarter,
        "month":       dates.month,
        "month_name":  dates.strftime("%b"),
        "day":         dates.day,
        "day_of_week": dates.day_name(),
        "is_weekend":  dates.dayofweek >= 5
    })
    bulk_insert(conn, "dim_dates", df,
                ["date_id","year","quarter","month",
                 "month_name","day","day_of_week","is_weekend"])

# ---- 5. Payments ----
def load_payments(conn):
    print("Loading payments...")
    df = pd.read_csv(CLEAN + "payments_clean.csv")
    bulk_insert(conn, "dim_payments", df, [
        "order_id","payment_sequential",
        "payment_type","payment_installments","payment_value"
    ])

# ---- 6. Order Items ----
def load_order_items(conn):
    print("Loading order items...")
    df = pd.read_csv(CLEAN + "order_items_clean.csv")
    bulk_insert(conn, "dim_order_items", df, [
        "order_id","order_item_id","product_id",
        "seller_id","price","freight_value","item_total_value"
    ])

# ---- 7. Fact Orders ----
def load_fact_orders(conn):
    print("Loading fact orders...")
    orders  = pd.read_csv(CLEAN + "orders_clean.csv",
                          parse_dates=["order_purchase_timestamp"])
    items   = pd.read_csv(CLEAN + "order_items_clean.csv")
    reviews = pd.read_csv(CLEAN + "reviews_clean.csv")

    # Aggregate items per order
    items_agg = items.groupby("order_id").agg(
        total_order_value   = ("price",         "sum"),
        total_freight_value = ("freight_value", "sum"),
        total_items         = ("order_item_id", "count")
    ).reset_index()

    # Latest review per order
    reviews_agg = reviews.sort_values("review_answer_timestamp") \
                         .groupby("order_id") \
                         .agg(review_score=("review_score","last"),
                              sentiment   =("sentiment",   "last")) \
                         .reset_index()

    # Merge all together
    fact = orders.merge(items_agg,  on="order_id", how="left")
    fact = fact.merge(reviews_agg,  on="order_id", how="left")

    fact = fact[[
        "order_id","customer_id","order_status",
        "order_purchase_timestamp","order_approved_at",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
        "is_delivered","is_late","delivery_delay_days",
        "purchase_year","purchase_month","purchase_month_name",
        "purchase_quarter","purchase_dayofweek","purchase_hour",
        "total_order_value","total_freight_value","total_items",
        "review_score","sentiment"
    ]].copy()

    fact.columns = [
        "order_id","customer_id","order_status",
        "purchase_date","approved_date",
        "delivered_date","estimated_delivery_date",
        "is_delivered","is_late","delivery_delay_days",
        "purchase_year","purchase_month","purchase_month_name",
        "purchase_quarter","purchase_dayofweek","purchase_hour",
        "total_order_value","total_freight_value","total_items",
        "review_score","sentiment"
    ]

    # Convert dates
    for col in ["purchase_date","approved_date",
                "delivered_date","estimated_delivery_date"]:
        fact[col] = pd.to_datetime(fact[col], errors="coerce").dt.date

    # Fix numeric columns
    fact["total_order_value"]   = pd.to_numeric(fact["total_order_value"],   errors="coerce").round(2)
    fact["total_freight_value"] = pd.to_numeric(fact["total_freight_value"], errors="coerce").round(2)
    fact["delivery_delay_days"] = pd.to_numeric(fact["delivery_delay_days"], errors="coerce").round(1)
    fact["review_score"]        = pd.to_numeric(fact["review_score"],        errors="coerce").round(1)

    # Fix integer columns
    for col in ["purchase_year","purchase_month","purchase_quarter",
                "purchase_hour","total_items"]:
        fact[col] = pd.to_numeric(fact[col], errors="coerce").fillna(0).astype(int)

    # Fix boolean columns
    fact["is_delivered"] = fact["is_delivered"].fillna(False).astype(bool)
    fact["is_late"]      = fact["is_late"].fillna(False).astype(bool)

    bulk_insert(conn, "fact_orders", fact, list(fact.columns))

# ---- Run everything ----
print("Connecting to PostgreSQL...")
conn = get_conn()
print("Connected!\n")

load_customers(conn)
load_products(conn)
load_sellers(conn)
load_dates(conn)
load_payments(conn)
load_order_items(conn)
load_fact_orders(conn)

conn.close()

print("\n" + "="*45)
print("All tables loaded into PostgreSQL!")
print("="*45)