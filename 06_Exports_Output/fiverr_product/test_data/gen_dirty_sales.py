"""Generate a synthetic dirty sales dataset for Fiverr pipeline testing."""
import csv
import random
from pathlib import Path

random.seed(42)

REPS = ["john smith", "JOHN SMITH", "John Smith", "sara lee", "Sara Lee", None, "mike chen", "MIKE CHEN"]
REGIONS = ["North", "north", "NORTH", "South", "South", "East", "east", "WEST", "West", None]
PRODUCTS = ["Widget A", "widget a", "Widget B", "WIDGET C", "Service X", "Service Y", None, "Widget A"]
STATUSES = ["Closed", "closed", "CLOSED", "Pending", "pending", "Cancelled", None, "Closed"]
DEAL_AMTS = [1250, None, 890, 3400, -50, 0, 75000, 2100, None, "N/A", 1500]

rows = []
for i in range(1, 501):
    rows.append({
        "id": i,
        "sales_rep": random.choice(REPS),
        "region": random.choice(REGIONS),
        "product": random.choice(PRODUCTS),
        "deal_amount": random.choice(DEAL_AMTS),
        "close_date": random.choice([
            "2026-01-15", "01/15/2026", "Jan 15, 2026", "15-01-2026", None, ""
        ]),
        "status": random.choice(STATUSES),
        "commission_pct": random.choice([0.05, 0.1, 0.15, None, "10%", "0.05", "N/A"]),
        "notes": random.choice(["", "", "Urgent deal", "Follow up", None, "  whitespace  "]),
    })

# Add some exact duplicates
for _ in range(15):
    rows.append(random.choice(rows[:100]))

random.shuffle(rows)

out = Path(__file__).parent / "dirty_sales_500.csv"
with out.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["id","sales_rep","region","product","deal_amount","close_date","status","commission_pct","notes"])
    w.writeheader()
    w.writerows(rows)

print(f"Generated {len(rows)} rows → {out}")
print(f"  Expected issues:")
print(f"  - NULL sales_rep: ~60 rows")
print(f"  - NULL region: ~50 rows")
print(f"  - NULL product: ~60 rows")
print(f"  - NULL deal_amount: ~60 rows (including None + 'N/A')")
print(f"  - Mixed date formats: ~120 rows")
print(f"  - Inconsistent casing: throughout")
print(f"  - Exact duplicates: 15 rows")
print(f"  - Negative/outlier amounts: 2 rows (-50, 75000)")
print(f"  - Bad commission_pct: '10%' string in numeric field")
