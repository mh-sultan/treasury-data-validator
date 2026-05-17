# Change Request — CR-2025-TVF-001
# Treasury Data Validation Framework — Initial Deployment

| Field | Value |
|-------|-------|
| Change Title | Treasury Transaction Data Quality Validation Framework |
| Change Reference | CR-2025-TVF-001 |
| Change Type | Normal Change (requires CAB review) |
| Requestor | Muhammad Hussain Sultan |
| Technical Approver | Thomas Koch, IT Consultant — Financial Services |
| Service Owner Approver | René Schulze, Head of IT — Treasury & Corporate Finance |
| Target Implementation | Week of 20 May 2026 |
| Maintenance Window | Saturday 21:00–23:00 (non-trading hours) |

## Business Justification

Treasury transaction data flows from multiple source systems into downstream risk reports and regulatory submissions. Currently, data quality issues — including duplicate trade records, missing EMIR references, and impossible date sequences — are not systematically detected before they reach those outputs.

This framework introduces an automated validation layer that runs 15 business rules against every transaction dataset before it is approved for downstream use. It replaces manual spot-checking with a repeatable, documented, auditable process. The structured JSON output can feed monitoring dashboards and trigger ServiceNow alerts when failures are detected.

## Scope

**Systems affected:**
- Treasury transaction data files (source — read only)
- Validation framework scripts (new component)
- Output reports directory (new artefact)

**Systems NOT affected:**
- Murex MX.3 (no connection — operates on exported data files only)
- SAP General Ledger
- EMIR trade repository submissions
- Any production treasury system

**Dependencies:** Python 3.10+, pandas library, counterparty_limits reference table

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Validation rule produces false positives | Low | Medium | Tested against known-good data before deployment. All rejections logged and reviewable. |
| Performance impact on data processing | Low | Low | Operates on copies of exported files. No direct connection to source systems. |
| Incorrect rejection of valid records | Low | High | Original raw data preserved unchanged. Every rejection logged with reason code. Reviewable before any action is taken. |
| Tool unavailability | Low | Low | Additive component only. Existing workflows unaffected if tool is unavailable. |

## Testing Approach

- **Unit tests:** pytest test suite covering 8 validation rules (see TEST_RESULTS.md)
- **Integration test:** end-to-end pipeline run on full 100-row test dataset with embedded quality issues
- **Regression test:** verified clean data passes all rules without false positives
- **UAT:** Treasury IT Analyst reviews output reports against known dataset before sign-off

## Rollback Plan

1. Stop the validation framework process
2. Raw data preserved unchanged in source directory — no data loss possible
3. Revert to previous version: `git checkout [previous_commit_hash]`
4. Existing data processing workflows unaffected — this framework is additive only

## Approvals

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Technical Approver | Thomas Koch | [pending] | |
| Service Owner | René Schulze | [pending] | |