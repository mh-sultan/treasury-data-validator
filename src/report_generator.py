# report_generator.py
# Produces the final validation report
# This is the deliverable the team acts on

import json
from datetime import datetime

def generate_report(validation_results):
    """
    Combine all validation results into a structured report.
    
    Business reason: The report is audit-ready output.
    It must show overall status, what passed, what failed,
    and exactly which records need attention.
    """
    passed = [r for r in validation_results if r['status'] == 'PASS']
    failed = [r for r in validation_results if r['status'] == 'FAIL']
    overall = 'PASS' if len(failed) == 0 else 'FAIL'

    report = {
        'report_metadata': {
            'generated_at': datetime.now().isoformat(),
            'overall_status': overall,
            'total_rules_run': len(validation_results),
            'rules_passed': len(passed),
            'rules_failed': len(failed)
        },
        'validation_results': {
            'by_category': {
                'COMPLETENESS': [r for r in validation_results 
                                 if r['category'] == 'COMPLETENESS'],
                'FINANCIAL_LOGIC': [r for r in validation_results 
                                    if r['category'] == 'FINANCIAL_LOGIC'],
                'LIMIT_MONITORING': [r for r in validation_results 
                                     if r['category'] == 'LIMIT_MONITORING'],
                'REGULATORY': [r for r in validation_results 
                               if r['category'] == 'REGULATORY']
            },
            'failures_only': failed
        },
        'recommendation': (
            'Data approved for downstream use.'
            if overall == 'PASS'
            else f'Data NOT approved. {len(failed)} rule(s) failed. '
                 f'Review failures before use.'
        )
    }
    return report

def save_report(report, output_path='outputs/validation_report.json'):
    """Save the report to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"Report saved to: {output_path}")

if __name__ == "__main__":
    import pandas as pd
    from src.validators import run_all_validations

    df = pd.read_csv('data/raw_transactions.csv')
    limits_df = pd.read_csv('data/counterparty_limits.csv')

    results = run_all_validations(df, limits_df)
    report = generate_report(results)
    save_report(report)

    print()
    print('=== VALIDATION SUMMARY ===')
    print(f"Overall status: {report['report_metadata']['overall_status']}")
    print(f"Rules passed: {report['report_metadata']['rules_passed']}")
    print(f"Rules failed: {report['report_metadata']['rules_failed']}")
    print()
    print(report['recommendation'])