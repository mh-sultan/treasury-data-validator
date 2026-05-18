# Test Execution Results — CR-2025-TVF-001

## Test Environment

| Item | Value |
|------|-------|
| Execution Date | 17 May 2026 |
| Python Version | 3.14.5 |
| OS | Windows 11 |
| Test Framework | pytest |
| Dataset Size | 103 transactions, 5 counterparties |

## Test Results Summary

| Total Tests | Passed | Failed | Skipped |
|-------------|--------|--------|---------|
| 10 | 10 | 0 | 0 |

## Detailed Test Results

| Test ID | Rule | Description | Expected | Actual | Status |
|---------|------|-------------|----------|--------|--------|
| TC-001 | V1 | Completeness passes on clean data | PASS | PASS | ✅ PASS |
| TC-002 | V1 | Completeness fails on null trade_id | FAIL | FAIL | ✅ PASS |
| TC-003 | V4 | Date logic fails when value_date < trade_date | FAIL | FAIL | ✅ PASS |
| TC-004 | V4 | Date logic passes on clean data | PASS | PASS | ✅ PASS |
| TC-005 | V6 | Positive notional fails on negative value | FAIL | FAIL | ✅ PASS |
| TC-006 | V10 | Limit breach detected correctly | FAIL | FAIL | ✅ PASS |
| TC-007 | V10 | Limit check passes when within limit | PASS | PASS | ✅ PASS |
| TC-008 | V13 | EMIR check flags missing trade repository ref | FAIL | FAIL | ✅ PASS |
| TC-009 | V15 | Duplicate trade_id detected | FAIL | FAIL | ✅ PASS |
| TC-010 | V15 | No duplicates passes on clean data | PASS | PASS | ✅ PASS |

## Defect Found During Testing

**Defect ID:** DEF-001
**Description:** validate_counterparty_limits failed on records with non-numeric notional_amount values. The pd.to_numeric conversion was not applied before the aggregation step.
**Root Cause:** Missing type coercion before SUM operation in the validation function.
**Fix Applied:** Added `pd.to_numeric(df_active['notional_amount'], errors='coerce')` before the groupby operation.
**Retest Result:** PASS after fix applied.

## Sign-Off

Testing completed by: Muhammad Hussain Sultan
Date: 17 May 2026
All 10 test cases passed. One defect found and resolved during development. Ready for CAB review.