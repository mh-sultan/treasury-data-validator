# CHANGE REQUEST — Treasury Data Validation Pipeline

---

## Change Identification

| Field | Value |
|-------|-------|
| Change ID | CR-2025-001 |
| Change Type | Normal |
| Priority | Medium |
| Status | Approved |
| Submission Date | 2025-12-01 |
| Target Implementation Date | 2025-12-15 |

---

## Change Description

**Title:** Implementation of Automated Treasury Transaction Data Quality Pipeline

**Summary:** Deploy a Python-based automated validation pipeline to replace manual spot-checking of treasury transaction data exports. The pipeline applies 15 business rules across 5 validation categories, produces a structured JSON quality report, and flags compliance gaps before data reaches downstream reporting systems.

**Systems Affected:**
- Treasury transaction data export files (raw_transactions.csv)
- Counterparty reference data (counterparty_limits.csv)
- Downstream reporting layer (Power BI financial dashboard)

**Change Scope:** New tooling addition. No modifications to source systems (Murex export format unchanged). No changes to SAP integration. No changes to EMIR submission process.

---

## Business Justification

Manual review of treasury transaction exports cannot reliably detect:
- Duplicate trade IDs causing double-counting in risk reports
- Active trades missing EMIR trade repository references (regulatory breach)
- Counterparty exposures exceeding board-approved credit limits
- Invalid instrument types not supported by the validation framework
- Impossible date sequences (value date before trade date)

This pipeline automates detection of all five problem categories. The JSON output is machine-readable and can feed ServiceNow alerts or monitoring dashboards without manual intervention.

**Regulatory relevance:** Under EMIR Article 9, every active OTC derivative must be reported to a trade repository by the daily deadline. An active trade missing a trade_repository_ref is a direct reporting breach. This pipeline detects all such gaps before the compliance submission window.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Pipeline produces false positives (valid records flagged) | Low | Medium | 15 validation rules independently tested with 10 pytest test cases before deployment |
| Pipeline fails to run (environment error) | Low | Low | Manual review process remains in place as fallback; pipeline failure does not affect source data |
| Rule logic incorrectly implemented | Low | High | Each rule validated against known dirty data with confirmed expected output; TEST_RESULTS.md documents all results |
| Performance impact on downstream systems | None | None | Pipeline reads CSVs only; does not connect to or modify any live system |

**Overall Risk Rating:** Low

---

## Test Plan

All testing completed in non-production environment prior to this submission.

| Test ID | Description | Expected Result | Actual Result | Status |
|---------|-------------|-----------------|---------------|--------|
| T-001 | Duplicate trade ID detection | 3 duplicates flagged, latest timestamp retained | 3 duplicates detected, deduplication applied | PASS |
| T-002 | Null counterparty ID detection | Records with null CP flagged under V1 | Flagged correctly | PASS |
| T-003 | Impossible value date detection | value_date before trade_date flagged under V4/V5 | 3 records flagged | PASS |
| T-004 | Negative notional detection | Negative amounts flagged under V6 | 1 record flagged | PASS |
| T-005 | Invalid instrument type rejection | FX_SPOT and BOND rejected at cleaning stage | 2 records rejected | PASS |
| T-006 | EMIR reference gap detection | Active trades with null trade_repository_ref flagged | 8 gaps detected | PASS |
| T-007 | Credit limit breach detection | Counterparty exposure vs approved limit calculated correctly | V10 PASS with current limits | PASS |
| T-008 | Deduplication before V15 | V15 passes because duplicates removed in cleaning stage | V15 PASS | PASS |
| T-009 | JSON report generation | Structured report saved to outputs/ | Report generated correctly | PASS |
| T-010 | Full pipeline execution | 103 rows in, 98 rows clean, 5 rejected | Confirmed | PASS |

**Test Result:** 10/10 PASS. Pipeline approved for deployment.

---

## Rollback Plan

This pipeline adds new tooling only. It does not modify any source data, source systems, or existing downstream processes.

**Rollback procedure:** Deactivate pipeline script. Resume manual review process. Zero risk of data loss or system impact.

**Rollback time estimate:** Immediate — no configuration changes required to revert.

---

## Implementation Steps

1. Deploy pipeline scripts to designated execution environment
2. Confirm counterparty_limits.csv reference data is current and accurate
3. Execute pipeline against current raw transaction export: `python etl_pipeline.py`
4. Review JSON output — confirm rule pass/fail counts match expected baseline
5. Confirm Power BI dashboard refreshes correctly from regenerated CSVs
6. Confirm EMIR gaps table on Data Quality page reflects current export
7. Hand over to operations team with DATA_DICTIONARY.md and TEST_RESULTS.md

---

## Change Advisory Board (CAB) Review

| Field | Value |
|-------|-------|
| CAB Meeting Date | 2025-12-10 |
| Decision | Approved |
| Conditions | None |
| Next Review | Post-implementation review scheduled 2025-12-22 |

---

## Post-Implementation Review

**Implementation Date:** 2025-12-15
**Outcome:** Successful
**Issues encountered:** None
**Sign-off:** Operations team confirmed pipeline running as expected. Validation report output matches pre-deployment test results. EMIR gap detection confirmed active.