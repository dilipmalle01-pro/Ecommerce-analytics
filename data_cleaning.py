import pandas as pd
import numpy as np
import os

# ---- Paths ----
RAW  = "raw_data/"
CLEAN = "clean_data/"
os.makedirs(CLEAN, exist_ok=True)

# ---- Load all tables ----
print("Loading raw data...")
orders      = pd.read_csv(RAW + "olist_orders_dataset.csv")
customers   = pd.read_csv(RAW + "olist_customers_dataset.csv")
order_items = pd.read_csv(RAW + "olist_order_items_dataset.csv")
payments    = pd.read_csv(RAW + "olist_order_payments_dataset.csv")
reviews     = pd.read_csv(RAW + "olist_order_reviews_dataset.csv")
products    = pd.read_csv(RAW + "olist_products_dataset.csv")
sellers     = pd.read_csv(RAW + "olist_sellers_dataset.csv")
cat_trans   = pd.read_csv(RAW + "product_category_name_translation.csv")

print("All tables loaded!\n")

# ==============================
# CLEAN ORDERS
# ==============================
print("Cleaning orders...")

# Fix date columns
date_cols = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date"
]
for col in date_cols:
    orders[col] = pd.to_datetime(orders[col])

# Drop rows where approval date is missing (only ~160 rows)
orders = orders.dropna(subset=["order_approved_at"])

# Add helpful flag columns
orders["is_delivered"] = orders["order_delivered_customer_date"].notna()
orders["is_late"] = (
    orders["order_delivered_customer_date"] >
    orders["order_estimated_delivery_date"]
)
orders["delivery_delay_days"] = (
    orders["order_delivered_customer_date"] -
    orders["order_estimated_delivery_date"]
).dt.days

# Extract time parts
orders["purchase_year"]       = orders["order_purchase_timestamp"].dt.year
orders["purchase_month"]      = orders["order_purchase_timestamp"].dt.month
orders["purchase_month_name"] = orders["order_purchase_timestamp"].dt.strftime("%b")
orders["purchase_dayofweek"]  = orders["order_purchase_timestamp"].dt.day_name()
orders["purchase_hour"]       = orders["order_purchase_timestamp"].dt.hour
orders["purchase_quarter"]    = orders["order_purchase_timestamp"].dt.quarter

# Separate cancelled orders
cancelled = orders[orders["order_status"].isin(["canceled","unavailable"])]
orders_clean = orders[~orders["order_status"].isin(["canceled","unavailable"])]

print(f"  Orders clean     : {len(orders_clean):,} rows")
print(f"  Cancelled orders : {len(cancelled):,} rows")

# ==============================
# CLEAN PRODUCTS
# ==============================
print("Cleaning products...")

# Merge English category names
products = products.merge(cat_trans, on="product_category_name", how="left")
products["product_category_name"] = products["product_category_name"].fillna("unknown")
products["product_category_name_english"] = products["product_category_name_english"].fillna("unknown")

# Fill missing dimensions with median
dim_cols = [
    "product_weight_g","product_length_cm",
    "product_height_cm","product_width_cm",
    "product_name_lenght","product_description_lenght",
    "product_photos_qty"
]
for col in dim_cols:
    products[col] = products[col].fillna(products[col].median())

print(f"  Products clean : {len(products):,} rows")

# ==============================
# CLEAN REVIEWS
# ==============================
print("Cleaning reviews...")

reviews["review_comment_title"]   = reviews["review_comment_title"].fillna("")
reviews["review_comment_message"] = reviews["review_comment_message"].fillna("")
reviews["review_creation_date"]   = pd.to_datetime(reviews["review_creation_date"])
reviews["review_answer_timestamp"]= pd.to_datetime(reviews["review_answer_timestamp"])

def label_sentiment(score):
    if score >= 4:   return "positive"
    elif score == 3: return "neutral"
    else:            return "negative"

reviews["sentiment"] = reviews["review_score"].apply(label_sentiment)

print(f"  Reviews clean : {len(reviews):,} rows")

# ==============================
# CLEAN ORDER ITEMS
# ==============================
print("Cleaning order items...")

order_items["shipping_limit_date"] = pd.to_datetime(order_items["shipping_limit_date"])
order_items["item_total_value"]    = order_items["price"] + order_items["freight_value"]
order_items = order_items[order_items["price"] > 0]

print(f"  Order items clean : {len(order_items):,} rows")

# ==============================
# CLEAN PAYMENTS
# ==============================
print("Cleaning payments...")

payments = payments[payments["payment_type"] != "not_defined"]
payments = payments[payments["payment_value"] > 0]

print(f"  Payments clean : {len(payments):,} rows")

# ==============================
# REMOVE DUPLICATES
# ==============================
print("Removing duplicates...")

orders_clean = orders_clean.drop_duplicates()
customers    = customers.drop_duplicates()
order_items  = order_items.drop_duplicates()
payments     = payments.drop_duplicates()
reviews      = reviews.drop_duplicates()
products     = products.drop_duplicates()
sellers      = sellers.drop_duplicates()

# ==============================
# SAVE ALL CLEAN FILES
# ==============================
print("\nSaving clean files...")

orders_clean.to_csv(CLEAN + "orders_clean.csv",      index=False)
customers.to_csv(CLEAN +    "customers_clean.csv",   index=False)
order_items.to_csv(CLEAN +  "order_items_clean.csv", index=False)
payments.to_csv(CLEAN +     "payments_clean.csv",    index=False)
reviews.to_csv(CLEAN +      "reviews_clean.csv",     index=False)
products.to_csv(CLEAN +     "products_clean.csv",    index=False)
sellers.to_csv(CLEAN +      "sellers_clean.csv",     index=False)
cancelled.to_csv(CLEAN +    "cancelled_orders.csv",  index=False)

# ==============================
# FINAL SUMMARY
# ==============================
print("\n" + "="*50)
print("DATA CLEANING COMPLETE")
print("="*50)
print(f"orders_clean      → {len(orders_clean):>7,} rows")
print(f"customers         → {len(customers):>7,} rows")
print(f"order_items       → {len(order_items):>7,} rows")
print(f"payments          → {len(payments):>7,} rows")
print(f"reviews           → {len(reviews):>7,} rows")
print(f"products          → {len(products):>7,} rows")
print(f"sellers           → {len(sellers):>7,} rows")
print("="*50)
print("All files saved to clean_data/ folder!")