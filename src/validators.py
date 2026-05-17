# validators.py
# Contains all validation rule functions
# Each function checks one business rule and returns a structured result

import pandas as pd

def validate_completeness(df):
    """
    Rule V1: No null values in mandatory fields.
    
    Business reason: Incomplete records cannot be used for
    risk reporting or regulatory submissions.
    """
    mandatory = ['trade_id', 'trade_date', 'counterparty_id',
                 'notional_amount', 'instrument_type']
    failures = df[df[mandatory].isna().any(axis=1)]
    return {
        'rule_id': 'V1',
        'category': 'COMPLETENESS',
        'description': 'No null values in mandatory fields',
        'passed': len(df) - len(failures),
        'failed': len(failures),
        'status': 'PASS' if len(failures) == 0 else 'FAIL',
        'failing_records': failures[['trade_id']].to_dict('records')
    }

def validate_instrument_types(df):
    """
    Rule V2: All instrument types from permitted list.
    
    Business reason: Unknown instrument types cannot be priced,
    risk-calculated, or correctly reported to regulators.
    """
    permitted = ['FX_FORWARD', 'INTEREST_RATE_SWAP',
                 'CASH_DEPOSIT', 'COMMODITY_FORWARD']
    df_clean = df.copy()
    df_clean['instrument_type'] = df_clean['instrument_type'].str.strip()
    failures = df_clean[~df_clean['instrument_type'].isin(permitted)]
    return {
        'rule_id': 'V2',
        'category': 'COMPLETENESS',
        'description': 'All instrument types from permitted list',
        'passed': len(df) - len(failures),
        'failed': len(failures),
        'status': 'PASS' if len(failures) == 0 else 'FAIL',
        'failing_records': failures[['trade_id', 
                          'instrument_type']].to_dict('records')
    }

def validate_known_counterparties(df, limits_df):
    """
    Rule V3: All counterparty IDs reference a known counterparty.
    
    Business reason: Unknown counterparties cannot be credit-checked
    or included in counterparty risk reports.
    """
    known_ids = set(limits_df['counterparty_id'].unique())
    failures = df[~df['counterparty_id'].isin(known_ids)]
    return {
        'rule_id': 'V3',
        'category': 'COMPLETENESS',
        'description': 'All counterparty IDs reference a known counterparty',
        'passed': len(df) - len(failures),
        'failed': len(failures),
        'status': 'PASS' if len(failures) == 0 else 'FAIL',
        'failing_records': failures[['trade_id', 
                          'counterparty_id']].to_dict('records')
    }

def validate_date_logic(df):
    """
    Rules V4+V5: value_date >= trade_date, maturity_date > value_date.
    
    Business reason: Settlement cannot happen before booking.
    A contract cannot expire before it settles.
    """
    df_dates = df.copy()
    for col in ['trade_date', 'value_date', 'maturity_date']:
        df_dates[col] = pd.to_datetime(df_dates[col], errors='coerce')

    fail_value = df_dates[df_dates['value_date'] < df_dates['trade_date']]
    
    forward_types = ['FX_FORWARD', 'INTEREST_RATE_SWAP', 'COMMODITY_FORWARD']
    forwards = df_dates[df_dates['instrument_type'].isin(forward_types)]
    fail_maturity = forwards[forwards['maturity_date'] <= forwards['value_date']]

    all_failures = pd.concat([fail_value, fail_maturity]).drop_duplicates('trade_id')
    return {
        'rule_id': 'V4_V5',
        'category': 'FINANCIAL_LOGIC',
        'description': 'value_date >= trade_date AND maturity_date > value_date',
        'passed': len(df) - len(all_failures),
        'failed': len(all_failures),
        'status': 'PASS' if len(all_failures) == 0 else 'FAIL',
        'failing_records': all_failures[['trade_id', 'trade_date',
                           'value_date', 'maturity_date']].to_dict('records')
    }

def validate_positive_notional(df):
    """
    Rule V6: notional_amount must be positive.
    
    Business reason: Negative or zero notional produces
    meaningless risk calculations.
    """
    failures = df[pd.to_numeric(df['notional_amount'], 
                  errors='coerce') <= 0]
    return {
        'rule_id': 'V6',
        'category': 'FINANCIAL_LOGIC',
        'description': 'notional_amount must be positive',
        'passed': len(df) - len(failures),
        'failed': len(failures),
        'status': 'PASS' if len(failures) == 0 else 'FAIL',
        'failing_records': failures[['trade_id', 
                           'notional_amount']].to_dict('records')
    }

def validate_counterparty_limits(df, limits_df):
    """
    Rule V10: Net exposure per counterparty must not exceed credit limit.
    
    Business reason: Credit limit breach means the company is exposed
    to more default risk than approved by risk management.
    """
    df_active = df[df['status'] == 'ACTIVE'].copy()
    df_active['notional_eur'] = pd.to_numeric(
        df_active['notional_amount'], errors='coerce')

    exposure = df_active.groupby('counterparty_id')['notional_eur']\
                        .sum().reset_index()
    exposure.columns = ['counterparty_id', 'total_exposure_eur']

    merged = exposure.merge(
        limits_df[['counterparty_id', 'counterparty_name', 'credit_limit_eur']],
        on='counterparty_id', how='left')
    merged['credit_limit_eur'] = pd.to_numeric(
        merged['credit_limit_eur'], errors='coerce')

    breaches = merged[merged['total_exposure_eur'] > 
                      merged['credit_limit_eur']].copy()
    breaches['breach_amount_eur'] = (breaches['total_exposure_eur'] - 
                                     breaches['credit_limit_eur'])
    return {
        'rule_id': 'V10',
        'category': 'LIMIT_MONITORING',
        'description': 'Net exposure per counterparty does not exceed credit limit',
        'passed': len(merged) - len(breaches),
        'failed': len(breaches),
        'status': 'PASS' if len(breaches) == 0 else 'FAIL',
        'failing_records': breaches[['counterparty_id', 'counterparty_name',
                           'total_exposure_eur', 'credit_limit_eur',
                           'breach_amount_eur']].to_dict('records')
    }

def validate_emir_reporting(df):
    """
    Rule V13: All ACTIVE trades must have a trade_repository_ref.
    
    Business reason: Null trade_repository_ref on an active trade
    means EMIR reporting is incomplete. This is a regulatory breach.
    """
    active = df[df['status'] == 'ACTIVE']
    failures = active[active['trade_repository_ref'].isna()]
    return {
        'rule_id': 'V13',
        'category': 'REGULATORY',
        'description': 'All ACTIVE trades must have a trade_repository_ref',
        'passed': len(active) - len(failures),
        'failed': len(failures),
        'status': 'PASS' if len(failures) == 0 else 'FAIL',
        'failing_records': failures[['trade_id', 'trade_date',
                           'instrument_type']].to_dict('records'),
        'regulatory_note': 'Null trade_repository_ref = EMIR reporting gap'
    }

def validate_no_duplicates(df):
    """
    Rule V15: No duplicate trade_id values.
    
    Business reason: Duplicate trades cause double-counting in
    risk reports and duplicate regulatory submissions.
    """
    dupes = df[df.duplicated('trade_id', keep=False)]
    return {
        'rule_id': 'V15',
        'category': 'REGULATORY',
        'description': 'No duplicate trade_id values',
        'passed': len(df) - len(dupes),
        'failed': len(dupes),
        'status': 'PASS' if len(dupes) == 0 else 'FAIL',
        'failing_records': dupes[['trade_id', 
                          'booking_timestamp']].to_dict('records')
    }

def run_all_validations(df, limits_df):
    """Run all validation rules and return combined results."""
    results = [
        validate_completeness(df),
        validate_instrument_types(df),
        validate_known_counterparties(df, limits_df),
        validate_date_logic(df),
        validate_positive_notional(df),
        validate_counterparty_limits(df, limits_df),
        validate_emir_reporting(df),
        validate_no_duplicates(df),
    ]
    return results