# test_validators.py
# Automated tests for all validation rules
# Run with: python -m pytest tests/ -v

import pytest
import pandas as pd
from src.validators import (
    validate_completeness,
    validate_instrument_types,
    validate_date_logic,
    validate_positive_notional,
    validate_counterparty_limits,
    validate_emir_reporting,
    validate_no_duplicates
)

@pytest.fixture
def clean_df():
    return pd.DataFrame({
        'trade_id': ['T001', 'T002', 'T003'],
        'trade_date': ['2025-01-15', '2025-01-16', '2025-01-17'],
        'value_date': ['2025-01-17', '2025-01-18', '2025-01-20'],
        'maturity_date': ['2025-06-15', '2025-07-16', '2025-08-17'],
        'instrument_type': ['FX_FORWARD', 'INTEREST_RATE_SWAP', 'FX_FORWARD'],
        'notional_amount': [10000000.0, 25000000.0, 15000000.0],
        'counterparty_id': ['CP001', 'CP002', 'CP001'],
        'status': ['ACTIVE', 'ACTIVE', 'ACTIVE'],
        'trade_repository_ref': ['TR001', 'TR002', 'TR003'],
        'booking_timestamp': ['2025-01-15T09:00:00',
                              '2025-01-16T10:00:00',
                              '2025-01-17T11:00:00']
    })

@pytest.fixture
def limits_df():
    return pd.DataFrame({
        'counterparty_id': ['CP001', 'CP002', 'CP003'],
        'counterparty_name': ['Deutsche Bank', 'HSBC', 'JPMorgan'],
        'credit_limit_eur': [500000000.0, 400000000.0, 450000000.0]
    })

# V1 Tests
def test_completeness_passes_on_clean_data(clean_df):
    result = validate_completeness(clean_df)
    assert result['status'] == 'PASS'
    assert result['failed'] == 0

def test_completeness_fails_on_null_counterparty(clean_df):
    df = clean_df.copy()
    df.loc[0, 'counterparty_id'] = None
    result = validate_completeness(df)
    assert result['status'] == 'FAIL'
    assert result['failed'] == 1

# V2 Tests
def test_instrument_type_fails_on_invalid(clean_df):
    df = clean_df.copy()
    df.loc[0, 'instrument_type'] = 'FX_SPOT'
    result = validate_instrument_types(df)
    assert result['status'] == 'FAIL'
    assert result['failed'] == 1

def test_instrument_type_passes_on_clean_data(clean_df):
    result = validate_instrument_types(clean_df)
    assert result['status'] == 'PASS'

# V4+V5 Tests
def test_date_logic_fails_when_value_before_trade(clean_df):
    df = clean_df.copy()
    df.loc[0, 'value_date'] = '2025-01-10'
    result = validate_date_logic(df)
    assert result['status'] == 'FAIL'

def test_date_logic_passes_on_clean_data(clean_df):
    result = validate_date_logic(clean_df)
    assert result['status'] == 'PASS'

# V6 Tests
def test_positive_notional_fails_on_negative(clean_df):
    df = clean_df.copy()
    df.loc[0, 'notional_amount'] = -1000000.0
    result = validate_positive_notional(df)
    assert result['status'] == 'FAIL'

# V10 Tests
def test_limit_monitoring_detects_breach(limits_df):
    df = pd.DataFrame({
        'counterparty_id': ['CP001', 'CP001'],
        'notional_amount': [300000000.0, 250000000.0],
        'status': ['ACTIVE', 'ACTIVE']
    })
    result = validate_counterparty_limits(df, limits_df)
    assert result['status'] == 'FAIL'
    assert result['failing_records'][0]['counterparty_id'] == 'CP001'

# V13 Tests
def test_emir_flags_missing_reference(clean_df):
    df = clean_df.copy()
    df.loc[0, 'trade_repository_ref'] = None
    result = validate_emir_reporting(df)
    assert result['status'] == 'FAIL'
    assert result['failed'] == 1

# V15 Tests
def test_duplicate_detection_works(clean_df):
    df = pd.concat([clean_df, clean_df.iloc[[0]]], ignore_index=True)
    result = validate_no_duplicates(df)
    assert result['status'] == 'FAIL'