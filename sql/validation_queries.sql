-- validation_queries.sql
-- These queries find data quality problems in the transactions table
-- Each query maps to a specific validation rule

-- V1: Find records with null values in mandatory fields
SELECT trade_id, 'NULL_MANDATORY_FIELD' as failure_type
FROM transactions
WHERE trade_id IS NULL
   OR trade_date IS NULL
   OR counterparty_id IS NULL
   OR notional_amount IS NULL
   OR instrument_type IS NULL;

-- V4+V5: Find records with impossible date sequences
SELECT trade_id, trade_date, value_date, maturity_date,
       'VALUE_DATE_BEFORE_TRADE_DATE' as failure_type
FROM transactions
WHERE value_date < trade_date
UNION ALL
SELECT trade_id, trade_date, value_date, maturity_date,
       'MATURITY_DATE_BEFORE_VALUE_DATE' as failure_type
FROM transactions
WHERE instrument_type IN ('FX_FORWARD','INTEREST_RATE_SWAP','COMMODITY_FORWARD')
  AND maturity_date <= value_date;

-- V6: Find records with negative or zero notional amount
SELECT trade_id, notional_amount, 'NEGATIVE_NOTIONAL' as failure_type
FROM transactions
WHERE notional_amount <= 0;

-- V10: Find counterparties where total exposure exceeds credit limit
SELECT t.counterparty_id,
       cl.counterparty_name,
       SUM(t.notional_amount) as total_exposure_eur,
       cl.credit_limit_eur,
       SUM(t.notional_amount) - cl.credit_limit_eur as breach_amount_eur
FROM transactions t
JOIN counterparty_limits cl ON t.counterparty_id = cl.counterparty_id
WHERE t.status = 'ACTIVE'
GROUP BY t.counterparty_id, cl.counterparty_name, cl.credit_limit_eur
HAVING SUM(t.notional_amount) > cl.credit_limit_eur
ORDER BY breach_amount_eur DESC;

-- V13: Find active trades missing EMIR trade repository reference
SELECT trade_id, trade_date, instrument_type,
       'MISSING_EMIR_REFERENCE' as failure_type
FROM transactions
WHERE status = 'ACTIVE'
  AND (trade_repository_ref IS NULL OR trade_repository_ref = '');

-- V15: Find duplicate trade IDs
SELECT trade_id, COUNT(*) as occurrence_count
FROM transactions
GROUP BY trade_id
HAVING COUNT(*) > 1;