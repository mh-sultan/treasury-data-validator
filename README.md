# Treasury Data Quality Validation Framework

## 1. Business Context

Treasury operations manage cash, financial risk, and banking relationships across global markets. The data underpinning these operations flows from multiple source systems — trade booking platforms, risk engines, and settlement systems — each producing records that must be accurate, complete, and consistent before they reach downstream risk reports or regulatory submissions.

In a regulated environment, data quality failures have direct consequences. An incorrect EMIR submission is a regulatory breach. A duplicate trade record causes double-counting in risk reports. A missing counterparty reference means a trade cannot be credit-checked. These are not technical problems — they are operational and compliance risks.

This framework provides systematic, documented, repeatable data quality validation for treasury transaction data before it reaches downstream systems.

## 2. Problem Statement

Treasury IT teams need a structured validation layer between raw transaction data and downstream risk systems. Manual checks are not scalable, not auditable, and not repeatable. This tool automates 15 business validation rules across five categories, produces structured outputs for every run, and preserves a complete audit trail from raw input to validation report.

## 3. Solution Overview

The pipeline runs in three stages:

**Stage 1 — Raw Ingestion:** Source files are read and preserved without modification. Original data is never altered. This is the foundation of data lineage at source level.

**Stage 2 — Cleaning:** Structural problems are resolved — whitespace, date standardization, duplicate removal, invalid instrument types. Every action is logged.

**Stage 3 — Validation:** 15 business rules run against the clean dataset. Each rule returns a structured result with pass/fail status, record counts, and the specific failing records.

A JSON validation report is produced at the end of every run.

## 4. User Stories

**US-1 — Completeness Check**
As a Treasury IT Analyst, I want the validation tool to identify transaction records with null values in mandatory fields, so that incomplete data is flagged before it reaches downstream risk systems or regulatory submissions.
- Given: a set of transaction records
- When: the validation tool runs
- Then: all records with null values in trade_id, trade_date, counterparty_id, notional_amount, or instrument_type appear in the validation report with status FAIL and the specific null field identified

**US-2 — Counterparty Limit Monitoring**
As a Treasury Risk Manager, I want the system to flag counterparties where total net exposure exceeds the approved credit limit, so that limit breaches are escalated before end-of-day risk reporting.
- Given: transaction dataset and counterparty_limits reference table
- When: validation tool runs
- Then: counterparties where net exposure > credit_limit_eur appear in report with counterparty name, total exposure, approved limit, and breach amount

**US-3 — EMIR Compliance**
As a Compliance Officer, I want the system to identify all ACTIVE trades missing a trade repository reference, so that EMIR reporting gaps can be resolved before the daily submission deadline.
- Given: set of ACTIVE transaction records
- When: validation tool runs
- Then: records with null trade_repository_ref appear with count of affected records

**US-4 — Date Logic Integrity**
As a Treasury IT Analyst, I want the system to flag records where trade dates, value dates, and maturity dates are logically inconsistent, so that date-sequencing errors do not produce incorrect settlement or risk calculations.
- Given: transaction records
- When: validation tool runs
- Then: records where value_date < trade_date or maturity_date < value_date appear with the specific failing date fields

**US-5 — Duplicate Detection**
As a Treasury IT Analyst, I want the system to identify duplicate trade IDs, so that double-counting in risk reports and duplicate regulatory submissions are prevented.
- Given: transaction records
- When: validation tool runs
- Then: duplicate trade_id values are flagged with their booking timestamps

## 5. Validation Rules

| Rule ID | Category | Description | Business Reason |
|---------|----------|-------------|-----------------|
| V1 | COMPLETENESS | No nulls in mandatory fields | Incomplete records cannot be used for risk reporting |
| V2 | COMPLETENESS | All instrument types from permitted list | Unknown types cannot be priced or reported |
| V3 | COMPLETENESS | All counterparty IDs reference known counterparty | Unknown counterparties cannot be credit-checked |
| V4 | FINANCIAL_LOGIC | value_date >= trade_date | Settlement cannot happen before booking |
| V5 | FINANCIAL_LOGIC | maturity_date > value_date for forwards | Contract cannot expire before settlement |
| V6 | FINANCIAL_LOGIC | notional_amount > 0 | Negative notional produces meaningless risk calculations |
| V7 | RECONCILIATION | Net exposure matches position_summary within 0.01% | Discrepancy indicates data integrity failure |
| V8 | RECONCILIATION | Active trade count matches position_summary | Count mismatch means systems disagree |
| V9 | RECONCILIATION | Total notional reconciles between tables | Portfolio size must agree across systems |
| V10 | LIMIT_MONITORING | Net exposure per counterparty <= credit limit | Breach means more default risk than approved |
| V11 | LIMIT_MONITORING | Individual trades > €100M flagged | Large trades require additional scrutiny |
| V12 | LIMIT_MONITORING | PENDING trades > 30 days flagged | May indicate settlement failures |
| V13 | REGULATORY | All ACTIVE trades have trade_repository_ref | Null = EMIR reporting gap = regulatory breach |
| V14 | REGULATORY | Trades > €50M have clearing_eligible = TRUE | Mandatory clearing threshold under EMIR |
| V15 | REGULATORY | No duplicate trade_id values | Duplicates cause double-counting in regulatory submissions |

## 6. Technical Implementation

- **Language:** Python 3.10+
- **Database:** SQLite (same SQL logic as Oracle/SAP HANA — portable)
- **Libraries:** pandas, sqlite3, pytest, json
- **Setup:** `pip install -r requirements.txt`
- **Run pipeline:** `python -m src.report_generator`
- **Run tests:** `python -m pytest tests/ -v`
- **Run notebook:** `python -m jupyter notebook`

## 7. Project Structure

treasury-data-validator/
├── README.md
├── CHANGE_REQUEST.md
├── TEST_RESULTS.md
├── DATA_DICTIONARY.md
├── requirements.txt
├── data/
│   ├── raw_transactions.csv
│   ├── counterparty_limits.csv
│   └── position_summary.csv
├── sql/
│   ├── schema.sql
│   └── validation_queries.sql
├── src/
│   ├── db_connector.py
│   ├── data_loader.py
│   ├── validators.py
│   └── report_generator.py
├── tests/
│   └── test_validators.py
├── notebooks/
│   └── treasury_validation_demo.ipynb
└── outputs/
└── validation_report.json



## 8. Change Management Context

In an IT service management environment, this tool would be deployed through a formal change management process. Any modification to validation rules, data models, or output formats requires a change request, impact assessment, testing documentation, and CAB approval before production deployment. See CHANGE_REQUEST.md for the simulated change request for this deployment.

## 9. Limitations and Next Steps

This is a proof-of-concept implementation using SQLite. A production implementation would:
- Connect to Oracle (Murex database) or SAP HANA using enterprise drivers
- Run on a scheduled orchestration platform such as Apache Airflow or Azure Data Factory
- Store outputs in a centralized data warehouse layer
- Include automated alerting via ServiceNow when validation failures are detected
- Integrate with the team's existing CI/CD pipeline for automated testing on deployment

