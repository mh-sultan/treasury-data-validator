import csv
import random
from datetime import datetime, timedelta

random.seed(42)

# --- COUNTERPARTY LIMITS (clean reference data) ---
counterparties = [
    ["CP001", "Deutsche Bank", "Germany", 500000000, "A", "2024-01-15"],
    ["CP002", "HSBC", "United Kingdom", 400000000, "A+", "2024-01-15"],
    ["CP003", "JPMorgan", "United States", 450000000, "AA-", "2024-01-15"],
    ["CP004", "BNP Paribas", "France", 350000000, "A", "2024-01-15"],
    ["CP005", "Goldman Sachs", "United States", 300000000, "A+", "2024-01-15"],
]

with open("data/counterparty_limits.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["counterparty_id", "counterparty_name", "country",
                     "credit_limit_eur", "credit_rating", "approved_date"])
    writer.writerows(counterparties)

print("counterparty_limits.csv created")

# --- TRANSACTION DATA (dirty) ---
instrument_types = ["FX_FORWARD", "INTEREST_RATE_SWAP", 
                    "CASH_DEPOSIT", "COMMODITY_FORWARD"]
currencies = ["EUR", "USD", "GBP", "CHF", "JPY"]
cp_ids = ["CP001", "CP002", "CP003", "CP004", "CP005"]
statuses = ["ACTIVE", "SETTLED", "PENDING", "CANCELLED"]
source_systems = ["MUREX", "SAP", "MANUAL"]

def random_date(start_year=2024):
    start = datetime(start_year, 1, 1)
    return start + timedelta(days=random.randint(0, 365))

rows = []
for i in range(1, 101):
    trade_date = random_date()
    value_date = trade_date + timedelta(days=random.randint(2, 5))
    maturity_date = value_date + timedelta(days=random.randint(30, 365))
    notional = round(random.uniform(1000000, 100000000), 2)
    cp = random.choice(cp_ids)
    instrument = random.choice(instrument_types)
    status = random.choice(statuses)
    tr_ref = f"EMIR-{i:05d}" if status == "ACTIVE" else ""
    
    rows.append([
        f"TRD-{i:04d}",
        trade_date.strftime("%Y-%m-%d"),
        value_date.strftime("%Y-%m-%d"),
        maturity_date.strftime("%Y-%m-%d"),
        instrument,
        random.choice(currencies),
        random.choice(currencies),
        notional,
        "EUR",
        cp,
        random.choice(["BUY", "SELL"]),
        status,
        tr_ref,
        random.choice(["TRUE", "FALSE"]),
        trade_date.strftime("%Y-%m-%dT%H:%M:%S"),
        random.choice(source_systems)
    ])

# --- EMBED DIRTY DATA ---

# 1. Duplicate trade IDs (3 duplicates)
for idx in [10, 25, 40]:
    duplicate = rows[idx].copy()
    duplicate[14] = (datetime.strptime(rows[idx][14], 
                     "%Y-%m-%dT%H:%M:%S") + 
                     timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S")
    rows.append(duplicate)

# 2. Null counterparty_id (4 records)
for idx in [5, 15, 30, 50]:
    rows[idx][9] = ""

# 3. value_date before trade_date (2 records)
for idx in [7, 20]:
    td = datetime.strptime(rows[idx][1], "%Y-%m-%d")
    rows[idx][2] = (td - timedelta(days=3)).strftime("%Y-%m-%d")

# 4. maturity_date before value_date (1 record)
idx = 35
vd = datetime.strptime(rows[idx][2], "%Y-%m-%d")
rows[idx][3] = (vd - timedelta(days=10)).strftime("%Y-%m-%d")

# 5. Negative notional (2 records)
rows[12][7] = -5000000.00
rows[45][7] = -1200000.00

# 6. Invalid instrument type (2 records)
rows[8][4] = "FX_SPOT"
rows[22][4] = "BOND"

# 7. ACTIVE trades missing EMIR reference (5 records)
active_indices = [i for i, r in enumerate(rows) if r[11] == "ACTIVE"][:5]
for idx in active_indices:
    rows[idx][12] = ""

# 8. Whitespace in some fields
rows[3][4] = "  FX_FORWARD  "
rows[18][9] = " CP002 "

# 9. Force 3 counterparties over credit limit
for idx in range(0, 15):
    rows[idx][9] = "CP001"
    rows[idx][7] = 45000000.00

with open("data/raw_transactions.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "trade_id", "trade_date", "value_date", "maturity_date",
        "instrument_type", "base_currency", "quote_currency",
        "notional_amount", "notional_currency", "counterparty_id",
        "buy_sell", "status", "trade_repository_ref",
        "clearing_eligible", "booking_timestamp", "source_system"
    ])
    writer.writerows(rows)

print("raw_transactions.csv created")

# --- POSITION SUMMARY (slightly wrong for reconciliation testing) ---
position_summary = [
    ["CP001", "EUR", 485000000, 12, "2025-03-31"],
    ["CP002", "USD", 398000000, 8, "2025-03-31"],
    ["CP003", "EUR", 441000000, 10, "2025-03-31"],
    ["CP004", "GBP", 348000000, 7, "2025-03-31"],
    ["CP005", "USD", 298000000, 6, "2025-03-31"],
]

with open("data/position_summary.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["counterparty_id", "currency", "net_notional_eur",
                     "active_trade_count", "report_date"])
    writer.writerows(position_summary)

print("position_summary.csv created")
print("All data files generated successfully.")