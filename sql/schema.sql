-- schema.sql
-- Defines the database tables for the treasury validation pipeline
-- SQLite is used for portability -- the SQL logic is identical to Oracle/SAP HANA

CREATE TABLE IF NOT EXISTS transactions (
    trade_id TEXT,
    trade_date TEXT,
    value_date TEXT,
    maturity_date TEXT,
    instrument_type TEXT,
    base_currency TEXT,
    quote_currency TEXT,
    notional_amount REAL,
    notional_currency TEXT,
    counterparty_id TEXT,
    buy_sell TEXT,
    status TEXT,
    trade_repository_ref TEXT,
    clearing_eligible TEXT,
    booking_timestamp TEXT,
    source_system TEXT
);

CREATE TABLE IF NOT EXISTS counterparty_limits (
    counterparty_id TEXT PRIMARY KEY,
    counterparty_name TEXT,
    country TEXT,
    credit_limit_eur REAL,
    credit_rating TEXT,
    approved_date TEXT
);

CREATE TABLE IF NOT EXISTS position_summary (
    counterparty_id TEXT,
    currency TEXT,
    net_notional_eur REAL,
    active_trade_count INTEGER,
    report_date TEXT
);
