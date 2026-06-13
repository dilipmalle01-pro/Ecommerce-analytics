import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import warnings
import os

warnings.filterwarnings("ignore")

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({
    "figure.dpi":        130,
    "figure.facecolor":  "white",
    "axes.facecolor":    "white",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "font.size":         11
})

os.makedirs("charts", exist_ok=True)
CLEAN = "clean_data/"

# ---- Load data ----
print("Loading data...")
orders    = pd.read_csv(CLEAN + "orders_clean.csv",
                        parse_dates=["order_purchase_timestamp"])
items     = pd.read_csv(CLEAN + "order_items_clean.csv")
products  = pd.read_csv(CLEAN + "products_clean.csv")
payments  = pd.read_csv(CLEAN + "payments_clean.csv")
reviews   = pd.read_csv(CLEAN + "reviews_clean.csv")
customers = pd.read_csv(CLEAN + "customers_clean.csv")

# Calculate order value from items
order_values = items.groupby("order_id").agg(
    total_order_value   = ("price",         "sum"),
    total_freight_value = ("freight_value", "sum"),
    total_items         = ("order_item_id", "count")
).reset_index()

# Merge into orders
orders = orders.merge(order_values, on="order_id", how="left")

# Only delivered orders
delivered = orders[orders["order_status"] == "delivered"].copy()
print(f"Delivered orders: {len(delivered):,}\n")

# ============================================================
# CHART 1 — Monthly Revenue Trend
# ============================================================
print("Creating Chart 1 — Monthly Revenue Trend...")

monthly = delivered.groupby(
    ["purchase_year","purchase_month"]
).agg(
    revenue = ("total_order_value", "sum"),
    orders  = ("order_id",          "count")
).reset_index()

monthly["period"] = pd.to_datetime(
    monthly["purchase_year"].astype(str) + "-" +
    monthly["purchase_month"].astype(str).str.zfill(2)
)
monthly = monthly.sort_values("period")

fig, ax1 = plt.subplots(figsize=(14, 5))
ax1.fill_between(monthly["period"], monthly["revenue"],
                 alpha=0.3, color="#378ADD")
ax1.plot(monthly["period"], monthly["revenue"],
         color="#378ADD", linewidth=2.5, label="Revenue (R$)")
ax1.set_ylabel("Total Revenue (R$)", color="#378ADD")
ax1.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"R${x/1e3:.0f}K"))

ax2 = ax1.twinx()
ax2.plot(monthly["period"], monthly["orders"],
         color="#D85A30", linewidth=2,
         linestyle="--", label="Orders")
ax2.set_ylabel("Total Orders", color="#D85A30")

ax1.set_title("Monthly Revenue & Order Volume (2016–2018)",
              fontsize=14, fontweight="bold", pad=15)
fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.88))
plt.tight_layout()
plt.savefig("charts/01_monthly_revenue.png")
plt.show()
print("  Saved!\n")

# ============================================================
# CHART 2 — Top 15 Categories by Revenue
# ============================================================
print("Creating Chart 2 — Category Revenue...")

items_products = items.merge(
    products[["product_id","product_category_name_english"]],
    on="product_id", how="left"
)
cat_revenue = items_products.groupby(
    "product_category_name_english"
).agg(
    revenue = ("price",    "sum"),
    orders  = ("order_id", "count")
).reset_index().sort_values("revenue", ascending=False).head(15)

fig, ax = plt.subplots(figsize=(12, 7))
bars = ax.barh(
    cat_revenue["product_category_name_english"],
    cat_revenue["revenue"],
    color=sns.color_palette("Blues_r", 15)
)
for bar, val in zip(bars, cat_revenue["revenue"]):
    ax.text(bar.get_width() + 20000,
            bar.get_y() + bar.get_height()/2,
            f"R${val/1e6:.2f}M", va="center", fontsize=9)

ax.set_title("Top 15 Product Categories by Revenue",
             fontsize=14, fontweight="bold")
ax.set_xlabel("Total Revenue (R$)")
ax.xaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"R${x/1e6:.1f}M"))
ax.invert_yaxis()
plt.tight_layout()
plt.savefig("charts/02_category_revenue.png")
plt.show()
print("  Saved!\n")

# ============================================================
# CHART 3 — Delivery Performance
# ============================================================
print("Creating Chart 3 — Delivery Performance...")

total    = len(delivered)
late     = delivered["is_late"].sum()
on_time  = total - late
late_pct = late / total * 100

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].pie(
    [on_time, late],
    labels=[f"On Time\n{100-late_pct:.1f}%",
            f"Late\n{late_pct:.1f}%"],
    colors=["#1D9E75","#E24B4A"],
    startangle=90,
    wedgeprops={"edgecolor":"white","linewidth":2}
)
axes[0].set_title("Delivery On-Time Rate", fontweight="bold")

late_orders = delivered[
    (delivered["is_late"] == True) &
    (delivered["delivery_delay_days"].notna())
]
axes[1].hist(
    late_orders["delivery_delay_days"].clip(upper=60),
    bins=30, color="#E24B4A", alpha=0.8, edgecolor="white"
)
axes[1].set_title("How Many Days Late?", fontweight="bold")
axes[1].set_xlabel("Days Late")
axes[1].set_ylabel("Number of Orders")
axes[1].axvline(
    x=late_orders["delivery_delay_days"].mean(),
    color="black", linestyle="--",
    label=f"Avg: {late_orders['delivery_delay_days'].mean():.1f} days"
)
axes[1].legend()

plt.suptitle("Delivery Performance Analysis",
             fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig("charts/03_delivery_performance.png")
plt.show()
print("  Saved!\n")

# ============================================================
# CHART 4 — Late Delivery by State
# ============================================================
print("Creating Chart 4 — Late Delivery by State...")

state_data = delivered.merge(
    customers[["customer_id","customer_state"]],
    on="customer_id", how="left"
)
state_late = state_data.groupby("customer_state").agg(
    total = ("order_id", "count"),
    late  = ("is_late",  "sum")
).reset_index()
state_late["late_pct"] = state_late["late"] / state_late["total"] * 100
state_late = state_late[state_late["total"] >= 100]\
             .sort_values("late_pct", ascending=False).head(10)

fig, ax = plt.subplots(figsize=(12, 5))
bars = ax.bar(
    state_late["customer_state"],
    state_late["late_pct"],
    color=sns.color_palette("Reds_r", 10),
    edgecolor="white"
)
for bar, val in zip(bars, state_late["late_pct"]):
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + 0.3,
            f"{val:.1f}%", ha="center", fontsize=9)

ax.set_title("Top 10 States — Highest Late Delivery Rate",
             fontsize=14, fontweight="bold")
ax.set_ylabel("Late Delivery %")
ax.set_xlabel("State")
plt.tight_layout()
plt.savefig("charts/04_late_by_state.png")
plt.show()
print("  Saved!\n")

# ============================================================
# CHART 5 — Payment Patterns
# ============================================================
print("Creating Chart 5 — Payment Patterns...")

pay_summary = payments.groupby("payment_type").agg(
    transactions = ("order_id",      "count"),
    total_value  = ("payment_value", "sum"),
    avg_value    = ("payment_value", "mean")
).reset_index().sort_values("total_value", ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
colors = ["#378ADD","#1D9E75","#EF9F27","#E24B4A"]

axes[0].pie(
    pay_summary["total_value"],
    labels=pay_summary["payment_type"],
    autopct="%1.1f%%",
    colors=colors,
    startangle=90,
    wedgeprops={"edgecolor":"white","linewidth":2}
)
axes[0].set_title("Revenue Share by Payment Type",
                  fontweight="bold")

axes[1].bar(
    pay_summary["payment_type"],
    pay_summary["avg_value"],
    color=colors, edgecolor="white"
)
axes[1].set_title("Average Order Value by Payment Type",
                  fontweight="bold")
axes[1].set_ylabel("Avg Order Value (R$)")
for i, val in enumerate(pay_summary["avg_value"]):
    axes[1].text(i, val + 1, f"R${val:.0f}",
                 ha="center", fontsize=10)

plt.suptitle("Payment Behaviour Analysis",
             fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig("charts/05_payment_patterns.png")
plt.show()
print("  Saved!\n")

# ============================================================
# CHART 6 — Top 10 Cities by Revenue
# ============================================================
print("Creating Chart 6 — Top Cities by Revenue...")

city_data = delivered.merge(
    customers[["customer_id","customer_city","customer_state"]],
    on="customer_id", how="left"
)
top_cities = city_data.groupby(
    ["customer_city","customer_state"]
).agg(
    revenue = ("total_order_value","sum"),
    orders  = ("order_id",         "count")
).reset_index().sort_values("revenue", ascending=False).head(10)

top_cities["label"] = (
    top_cities["customer_city"].str.title() +
    "\n(" + top_cities["customer_state"] + ")"
)

fig, ax = plt.subplots(figsize=(13, 6))
colors_list = ["#0C447C" if i == 0 else "#378ADD"
               for i in range(len(top_cities))]
bars = ax.bar(top_cities["label"], top_cities["revenue"],
              color=colors_list, edgecolor="white")

for bar, val in zip(bars, top_cities["revenue"]):
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + 5000,
            f"R${val/1e6:.2f}M",
            ha="center", fontsize=9)

ax.set_title("Top 10 Cities by Revenue",
             fontsize=14, fontweight="bold")
ax.set_ylabel("Total Revenue (R$)")
ax.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"R${x/1e6:.1f}M"))
plt.xticks(rotation=15, ha="right")
plt.tight_layout()
plt.savefig("charts/06_top_cities.png")
plt.show()
print("  Saved!\n")

# ============================================================
# CHART 7 — Review Score Distribution
# ============================================================
print("Creating Chart 7 — Review Scores...")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

score_counts = reviews["review_score"].value_counts().sort_index()
colors_score = ["#E24B4A","#D85A30","#EF9F27","#1D9E75","#0C447C"]
axes[0].bar(score_counts.index, score_counts.values,
            color=colors_score, edgecolor="white", width=0.6)
axes[0].set_title("Review Score Distribution",
                  fontweight="bold")
axes[0].set_xlabel("Review Score (1-5)")
axes[0].set_ylabel("Number of Reviews")
for i, (score, count) in enumerate(score_counts.items()):
    axes[0].text(score, count + 200,
                 f"{count:,}", ha="center", fontsize=9)

sentiment_counts = reviews["sentiment"].value_counts()
axes[1].pie(
    sentiment_counts,
    labels=sentiment_counts.index,
    autopct="%1.1f%%",
    colors=["#1D9E75","#EF9F27","#E24B4A"],
    startangle=90,
    wedgeprops={"edgecolor":"white","linewidth":2}
)
axes[1].set_title("Customer Sentiment Breakdown",
                  fontweight="bold")

plt.suptitle("Customer Review Analysis",
             fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig("charts/07_review_scores.png")
plt.show()
print("  Saved!\n")

# ============================================================
# CHART 8 — Orders by Day & Hour
# ============================================================
print("Creating Chart 8 — Order Patterns...")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

day_order = ["Monday","Tuesday","Wednesday",
             "Thursday","Friday","Saturday","Sunday"]
day_counts = delivered["purchase_dayofweek"]\
             .value_counts().reindex(day_order)

axes[0].bar(
    day_counts.index, day_counts.values,
    color=["#E24B4A" if d in ["Saturday","Sunday"]
           else "#378ADD" for d in day_order],
    edgecolor="white"
)
axes[0].set_title("Orders by Day of Week", fontweight="bold")
axes[0].set_ylabel("Number of Orders")
plt.setp(axes[0].xaxis.get_majorticklabels(), rotation=30)

hour_counts = delivered["purchase_hour"].value_counts().sort_index()
axes[1].plot(hour_counts.index, hour_counts.values,
             color="#378ADD", linewidth=2.5,
             marker="o", markersize=4)
axes[1].fill_between(hour_counts.index, hour_counts.values,
                     alpha=0.2, color="#378ADD")
axes[1].set_title("Orders by Hour of Day", fontweight="bold")
axes[1].set_xlabel("Hour")
axes[1].set_ylabel("Number of Orders")
axes[1].set_xticks(range(0, 24, 2))

plt.suptitle("When Do Customers Shop?",
             fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig("charts/08_order_patterns.png")
plt.show()
print("  Saved!\n")

# ============================================================
# SUMMARY
# ============================================================
print("=" * 55)
print("ALL 8 CHARTS SAVED TO charts/ FOLDER")
print("=" * 55)
peak = monthly.loc[monthly["revenue"].idxmax()]
print(f"\nKey Findings:")
print(f"  Peak month   : {peak['period'].strftime('%B %Y')}"
      f" — R${peak['revenue']:,.0f}")
print(f"  Late orders  : {late:,} ({late_pct:.1f}%)")
print(f"  Top category : "
      f"{cat_revenue.iloc[0]['product_category_name_english']}"
      f" — R${cat_revenue.iloc[0]['revenue']:,.0f}")
print(f"  Top city     : "
      f"{top_cities.iloc[0]['customer_city'].title()}"
      f" — R${top_cities.iloc[0]['revenue']:,.0f}")
print("=" * 55)