# Data Dictionary — Treasury Data Validator

## Table: transactions

| Column | Type | Description | Valid Values | Business Reason |
|--------|------|-------------|--------------|-----------------|
| trade_id | TEXT | Unique identifier assigned by Murex when trade is booked | Format: TRD-XXXX | Primary key. Duplicates indicate booking error or system fault |
| trade_date | TEXT | Date the trade was entered into the system | YYYY-MM-DD | Booking date. value_date must be >= this date |
| value_date | TEXT | Date the trade settles — when funds are exchanged | YYYY-MM-DD | Must be >= trade_date. Settlement before booking is impossible |
| maturity_date | TEXT | Date the contract expires | YYYY-MM-DD | Must be > value_date for forward instruments |
| instrument_type | TEXT | Type of financial contract | FX_FORWARD, INTEREST_RATE_SWAP, CASH_DEPOSIT, COMMODITY_FORWARD | Determines pricing model, risk calculation method, and regulatory treatment |
| base_currency | TEXT | Base currency of the currency pair | ISO 4217 code e.g. EUR | EUR in EUR/USD pair |
| quote_currency | TEXT | Quote currency of the currency pair | ISO 4217 code e.g. USD | USD in EUR/USD pair |
| notional_amount | REAL | Contract size — the face value of the trade | Must be positive | Used for exposure calculations and limit monitoring |
| notional_currency | TEXT | Currency the notional is expressed in | ISO 4217 code | Required for EUR conversion in limit monitoring |
| counterparty_id | TEXT | Identifier of the bank on the other side of the trade | Must reference counterparty_limits table | Required for credit limit monitoring and counterparty risk reporting |
| buy_sell | TEXT | Direction of the trade from Siemens Energy perspective | BUY, SELL | Determines position direction in risk calculations |
| status | TEXT | Current lifecycle state of the trade | ACTIVE, SETTLED, PENDING, CANCELLED | Only ACTIVE trades count for credit limit monitoring and EMIR reporting |
| trade_repository_ref | TEXT | EMIR reference assigned when trade is reported to trade repository | Format: TR-XXXX. NULL on ACTIVE trades = regulatory breach | Required for EMIR compliance. Null on active trade = unreported derivative |
| clearing_eligible | TEXT | Whether trade meets EMIR mandatory clearing threshold | TRUE, FALSE | Trades above €50M notional must be centrally cleared under EMIR |
| booking_timestamp | TEXT | Exact datetime the trade was recorded in the system | ISO 8601 datetime | Used to resolve duplicates — latest timestamp is kept |
| source_system | TEXT | Upstream system that generated this record | e.g. MUREX, MANUAL | Supports data lineage tracking |

---

## Table: counterparty_limits

| Column | Type | Description | Valid Values | Business Reason |
|--------|------|-------------|--------------|-----------------|
| counterparty_id | TEXT | Unique identifier for the counterparty bank | Format: CPXXX | Primary key. Referenced by transactions table |
| counterparty_name | TEXT | Full legal name of the counterparty | e.g. Deutsche Bank | Used in reporting and breach notifications |
| country | TEXT | Country of incorporation | e.g. Germany | Relevant for jurisdictional risk assessment |
| credit_limit_eur | REAL | Maximum approved net exposure in EUR | Must be positive | Set by risk management. Breach requires escalation |
| credit_rating | TEXT | External credit rating of the counterparty | e.g. A, AA-, A+ | Informs limit setting. Downgrades may trigger limit review |
| approved_date | TEXT | Date the credit limit was last approved | YYYY-MM-DD | Limits require periodic review and reapproval |

---

## Table: position_summary

| Column | Type | Description | Valid Values | Business Reason |
|--------|------|-------------|--------------|-----------------|
| counterparty_id | TEXT | Counterparty identifier | Must reference counterparty_limits | Used for reconciliation against transactions table |
| currency | TEXT | Currency of the net position | ISO 4217 code | Positions tracked per currency per counterparty |
| net_notional_eur | REAL | Net notional exposure in EUR | Numeric | Reconciled against sum of active transaction notionals |
| active_trade_count | INTEGER | Number of active trades with this counterparty | Non-negative integer | Reconciled against count of ACTIVE records in transactions |
| report_date | TEXT | Date this position snapshot was generated | YYYY-MM-DD | Positions are point-in-time. Must match transaction data date range |

---

## Data Lineage

raw_transactions.csv (source — never modified)
↓
Stage 2 Cleaning (whitespace, dates, duplicates, invalid types)
↓
Clean DataFrame (in memory)
↓
Stage 3 Validation (15 business rules)
↓
validation_report.json (structured output)

All transformations are applied to copies of the source data. The original CSV files are never modified. This ensures the raw zone remains the definitive record for audit purposes.

