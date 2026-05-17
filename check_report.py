import pandas as pd
from src.validators import run_all_validations
from src.report_generator import generate_report

df = pd.read_csv('data/raw_transactions.csv')
limits_df = pd.read_csv('data/counterparty_limits.csv')

results = run_all_validations(df, limits_df)
report = generate_report(results)

print('OVERALL STATUS:', report['report_metadata']['overall_status'])
print('Rules passed:', report['report_metadata']['rules_passed'])
print('Rules failed:', report['report_metadata']['rules_failed'])
print()

for r in results:
    print(f"Rule {r['rule_id']} | {r['category']} | {r['status']} | Failed records: {r['failed']}")
    print(f"  Description: {r['description']}")
    print()

print('RECOMMENDATION:', report['recommendation'])