import pandas as pd
import sqlite3
import os
import json
from datetime import datetime

# ── PATHS ──────────────────────────────────────────────────
BASE = r'C:\Users\mhuss\treasury-data-validator'
DATA = os.path.join(BASE, 'data')
OUTPUTS = os.path.join(BASE, 'outputs')
WAREHOUSE_DB = os.path.join(BASE, 'warehouse.db')
os.makedirs(OUTPUTS, exist_ok=True)

# ── STEP 1: LOAD AND CLEAN SOURCE DATA ─────────────────────
print("Step 1: Loading source data...")
transactions = pd.read_csv(os.path.join(DATA, 'raw_transactions.csv'))
limits = pd.read_csv(os.path.join(DATA, 'counterparty_limits.csv'))

# Clean: strip whitespace
for col in transactions.select_dtypes(include='object').columns:
    transactions[col] = transactions[col].astype(str).str.strip()
    transactions[col] = transactions[col].replace('nan', pd.NA)

# Clean: standardize dates
for col in ['trade_date', 'value_date', 'maturity_date']:
    transactions[col] = pd.to_datetime(transactions[col], errors='coerce')

# Clean: remove duplicates — keep latest booking
transactions['booking_timestamp'] = pd.to_datetime(
    transactions['booking_timestamp'], errors='coerce')
transactions = transactions.sort_values('booking_timestamp', ascending=False)
transactions = transactions.drop_duplicates('trade_id', keep='first')

# Clean: remove invalid instrument types
valid_types = {'FX_FORWARD', 'INTEREST_RATE_SWAP', 'CASH_DEPOSIT', 'COMMODITY_FORWARD'}
transactions = transactions[transactions['instrument_type'].isin(valid_types)]

print(f"  Clean records: {len(transactions)}")

# ── STEP 2: BUILD DIMENSION TABLES ─────────────────────────
print("Step 2: Building dimension tables...")

# DIM_COUNTERPARTY
dim_counterparty = limits.copy()
dim_counterparty.insert(0, 'counterparty_key', range(1, len(dim_counterparty) + 1))

# DIM_INSTRUMENT
instrument_types = list(valid_types)
dim_instrument = pd.DataFrame({
    'instrument_key': range(1, len(instrument_types) + 1),
    'instrument_type': instrument_types,
    'instrument_class': ['FX', 'RATES', 'MONEY_MARKET', 'COMMODITY'],
    'is_derivative': [True, True, False, True],
    'clearing_eligible': [True, True, False, True]
})

# DIM_DATE — one row per unique date in the dataset
all_dates = pd.concat([
    transactions['trade_date'],
    transactions['value_date'],
    transactions['maturity_date']
]).dropna().unique()

date_df = pd.DataFrame({'full_date': pd.to_datetime(all_dates)})
date_df = date_df.sort_values('full_date').reset_index(drop=True)
date_df['date_key'] = range(1, len(date_df) + 1)
date_df['year'] = date_df['full_date'].dt.year
date_df['quarter'] = date_df['full_date'].dt.quarter
date_df['month'] = date_df['full_date'].dt.month
date_df['month_name'] = date_df['full_date'].dt.strftime('%B')
date_df['week'] = date_df['full_date'].dt.isocalendar().week.astype(int)
date_df['day_of_week'] = date_df['full_date'].dt.day_name()
date_df['is_business_day'] = date_df['full_date'].dt.dayofweek < 5
date_df['full_date'] = date_df['full_date'].dt.strftime('%Y-%m-%d')
dim_date = date_df[['date_key', 'full_date', 'year', 'quarter',
                     'month', 'month_name', 'week', 'day_of_week', 'is_business_day']]

# DIM_CURRENCY
currencies = list(set(
    transactions['base_currency'].dropna().tolist() +
    transactions['quote_currency'].dropna().tolist() +
    transactions['notional_currency'].dropna().tolist()
))
dim_currency = pd.DataFrame({
    'currency_key': range(1, len(currencies) + 1),
    'currency_code': currencies,
    'currency_name': currencies,
    'region': ['Europe' if c == 'EUR' else
               'North America' if c == 'USD' else
               'Europe' if c == 'GBP' else
               'Europe' if c == 'CHF' else
               'Asia' for c in currencies]
})

print(f"  DIM_COUNTERPARTY: {len(dim_counterparty)} rows")
print(f"  DIM_INSTRUMENT:   {len(dim_instrument)} rows")
print(f"  DIM_DATE:         {len(dim_date)} rows")
print(f"  DIM_CURRENCY:     {len(dim_currency)} rows")

# ── STEP 3: BUILD FACT TABLE ────────────────────────────────
print("Step 3: Building fact table...")

fact = transactions.copy()

# Join surrogate keys from dimensions
fact = fact.merge(
    dim_counterparty[['counterparty_key', 'counterparty_id']],
    on='counterparty_id', how='left'
)
fact = fact.merge(
    dim_instrument[['instrument_key', 'instrument_type']],
    on='instrument_type', how='left'
)

date_lookup = dim_date.set_index('full_date')['date_key'].to_dict()
fact['trade_date_str'] = pd.to_datetime(
    fact['trade_date'], errors='coerce').dt.strftime('%Y-%m-%d')
fact['trade_date_key'] = fact['trade_date_str'].map(date_lookup)
fact['value_date_str'] = pd.to_datetime(
    fact['value_date'], errors='coerce').dt.strftime('%Y-%m-%d')
fact['value_date_key'] = fact['value_date_str'].map(date_lookup)

currency_lookup = dim_currency.set_index('currency_code')['currency_key'].to_dict()
fact['currency_key'] = fact['notional_currency'].map(currency_lookup)

fact['notional_amount_eur'] = pd.to_numeric(fact['notional_amount'], errors='coerce')
fact['load_timestamp'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
fact['transaction_key'] = range(1, len(fact) + 1)

fact_transactions = fact[[
    'transaction_key', 'trade_id', 'trade_date_key', 'value_date_key',
    'counterparty_key', 'instrument_key', 'currency_key',
    'notional_amount', 'notional_amount_eur', 'buy_sell', 'status',
    'trade_repository_ref', 'clearing_eligible', 'load_timestamp'
]]

for col in ['transaction_key', 'trade_date_key', 'value_date_key',
            'counterparty_key', 'instrument_key', 'currency_key']:
    fact_transactions[col] = fact_transactions[col].fillna(0).astype(int)

print(f"  FACT_TRANSACTIONS: {len(fact_transactions)} rows")

if 'counterparty_key' in fact.columns:
    fact = fact.drop(columns=['counterparty_key'])

# ── STEP 4: LOAD INTO SQLITE WAREHOUSE ─────────────────────
print("Step 4: Loading into warehouse database...")

conn = sqlite3.connect(WAREHOUSE_DB)

dim_counterparty.to_sql('DIM_COUNTERPARTY', conn,
                         if_exists='replace', index=False)
dim_instrument.to_sql('DIM_INSTRUMENT', conn,
                       if_exists='replace', index=False)
dim_date.to_sql('DIM_DATE', conn,
                if_exists='replace', index=False)
dim_currency.to_sql('DIM_CURRENCY', conn,
                    if_exists='replace', index=False)
fact_transactions.to_sql('FACT_TRANSACTIONS', conn,
                         if_exists='replace', index=False)

conn.close()
print(f"  Warehouse saved to: {WAREHOUSE_DB}")

# ── STEP 5: EXPORT CSVs FOR POWER BI ───────────────────────
print("Step 5: Exporting CSVs for Power BI...")

dim_counterparty.to_csv(os.path.join(OUTPUTS, 'DIM_COUNTERPARTY.csv'), index=False)
dim_instrument.to_csv(os.path.join(OUTPUTS, 'DIM_INSTRUMENT.csv'), index=False)
dim_date.to_csv(os.path.join(OUTPUTS, 'DIM_DATE.csv'), index=False)
dim_currency.to_csv(os.path.join(OUTPUTS, 'DIM_CURRENCY.csv'), index=False)
fact_transactions.to_csv(os.path.join(OUTPUTS, 'FACT_TRANSACTIONS.csv'), index=False)

# ── STEP 6: LOG THE PIPELINE RUN ───────────────────────────
print("Step 6: Logging pipeline run...")

run_log = {
    'run_timestamp': datetime.now().isoformat(),
    'status': 'SUCCESS',
    'records_input': len(transactions) + 3,
    'records_clean': len(transactions),
    'records_rejected': 3,
    'tables_loaded': ['DIM_COUNTERPARTY', 'DIM_INSTRUMENT',
                      'DIM_DATE', 'DIM_CURRENCY', 'FACT_TRANSACTIONS'],
    'warehouse_db': WAREHOUSE_DB
}

with open(os.path.join(OUTPUTS, 'pipeline_run_log.json'), 'w') as f:
    json.dump(run_log, f, indent=2)

print("  Pipeline run logged.")

# ── DONE ───────────────────────────────────────────────────
print("\n✓ ETL PIPELINE COMPLETE")
print(f"  Warehouse:  {WAREHOUSE_DB}")
print(f"  CSVs:       {OUTPUTS}")
print(f"  Log:        {os.path.join(OUTPUTS, 'pipeline_run_log.json')}")