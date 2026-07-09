import argparse
import sys
from . import scanner, code_quality, secrets, config_validator, coverage

SEVERITY_LEVELS = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}

def main():
    parser = argparse.ArgumentParser(description="ciforge CLI")
    parser.add_argument('--fail-on', type=str, default='high', choices=['low', 'medium', 'high', 'critical', 'none'], help='Exit non-zero if findings of this severity or higher are found')
    args = parser.parse_args()

    files = scanner.git_changed_files()
    all_findings = []

    for f in files:
        diff_text = scanner.git_diff(f)
        all_findings.extend(code_quality.analyze(f, diff_text))
        all_findings.extend(secrets.analyze(f, diff_text))
        all_findings.extend(config_validator.analyze(f, diff_text))

    all_findings.extend(coverage.analyze())

    if not all_findings:
        print("No issues found. Great job!")
        sys.exit(0)

    print("# ciforge Report\n")
    max_severity_found = -1
    
    for finding in all_findings:
        sev_val = SEVERITY_LEVELS.get(finding.severity, 0)
        max_severity_found = max(max_severity_found, sev_val)
        line_info = f":{finding.line}" if finding.line > 0 else ""
        print(f"- **[{finding.severity.upper()}]** `{finding.file}{line_info}`: {finding.message}")

    if args.fail_on != 'none':
        fail_threshold = SEVERITY_LEVELS.get(args.fail_on, 3)
        if max_severity_found >= fail_threshold:
            print(f"\nFailed: Found issues with severity '{args.fail_on}' or higher.")
            sys.exit(1)

    sys.exit(0)

if __name__ == '__main__':
    main()
