import argparse
import sys
import os
import stat
from . import scanner, code_quality, secrets, config_validator, coverage, ai_reviewer, assets, l10n, metrics, badges, community

SEVERITY_LEVELS = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}

def install_git_hook():
    if not os.path.isdir('.git'):
        print("No .git directory found. Cannot install hook.")
        sys.exit(0)
    hook_path = os.path.join('.git', 'hooks', 'pre-commit')
    hooks_dir = os.path.dirname(hook_path)
    if not os.path.exists(hooks_dir):
        os.makedirs(hooks_dir)
    with open(hook_path, 'w') as f:
        f.write("#!/bin/bash\nciforge --repo .\n")
    st = os.stat(hook_path)
    os.chmod(hook_path, st.st_mode | stat.S_IEXEC)
    print("Git pre-commit hook installed successfully.")
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="ciforge CLI")
    parser.add_argument('--fail-on', type=str, default='high', choices=['low', 'medium', 'high', 'critical', 'none'], help='Exit non-zero if findings of this severity or higher are found')
    parser.add_argument('--repo', type=str, default='.', help='Path to repository')
    parser.add_argument('--base-ref', type=str, default='origin/main', help='Base reference branch')
    parser.add_argument('--format', type=str, default='markdown', choices=['markdown', 'html'], help='Output format')
    parser.add_argument('--badge', action='store_true', help='Generate badge')
    parser.add_argument('--install-hook', action='store_true', help='Install git pre-commit hook')
    args = parser.parse_args()

    if args.install_hook:
        install_git_hook()

    if args.repo != '.':
        os.chdir(args.repo)

    files = scanner.git_changed_files()
    all_findings = []

    for f in files:
        diff_text = scanner.git_diff(f)
        all_findings.extend(code_quality.analyze(f, diff_text))
        all_findings.extend(secrets.analyze(f, diff_text))
        all_findings.extend(config_validator.analyze(f, diff_text))

    all_findings.extend(coverage.analyze())
    all_findings.extend(ai_reviewer.analyze())
    all_findings.extend(assets.analyze())
    all_findings.extend(l10n.analyze())
    all_findings.extend(metrics.analyze())

    if args.badge:
        badges.generate_badge(all_findings)

    welcome_msg = community.get_welcome_message()
    
    if not all_findings:
        if args.format == 'html':
            html_content = "<html><body style='background-color:#1e1e1e; color:#fff; font-family:sans-serif;'><h1>ciforge Report</h1>"
            if welcome_msg:
                html_content += f"<p><b>{welcome_msg}</b></p>"
            html_content += "<p>No issues found. Great job!</p></body></html>"
            with open("ciforge-report.html", "w") as f:
                f.write(html_content)
            print("HTML report written to ciforge-report.html")
        else:
            if welcome_msg:
                print(welcome_msg + "\n")
            print("No issues found. Great job!")
        sys.exit(0)

    max_severity_found = -1

    if args.format == 'html':
        html_content = "<html><head><style>"
        html_content += "body { background-color: #1e1e1e; color: #d4d4d4; font-family: sans-serif; padding: 20px; }"
        html_content += "table { border-collapse: collapse; width: 100%; margin-top: 20px; }"
        html_content += "th, td { border: 1px solid #444; padding: 8px; text-align: left; }"
        html_content += "th { background-color: #333; }"
        html_content += ".sev-low { color: #4CAF50; } .sev-medium { color: #FFEB3B; } .sev-high { color: #FF9800; } .sev-critical { color: #F44336; }"
        html_content += "</style></head><body>"
        html_content += "<h1>ciforge Report</h1>"
        if welcome_msg:
            html_content += f"<p><b>{welcome_msg}</b></p>"
        html_content += "<table><tr><th>Severity</th><th>File</th><th>Message</th></tr>"
        
        for finding in all_findings:
            sev_val = SEVERITY_LEVELS.get(finding.severity, 0)
            max_severity_found = max(max_severity_found, sev_val)
            line_info = f":{finding.line}" if finding.line > 0 else ""
            html_content += f"<tr><td class='sev-{finding.severity}'>{finding.severity.upper()}</td><td>{finding.file}{line_info}</td><td>{finding.message}</td></tr>"
            
        html_content += "</table></body></html>"
        with open("ciforge-report.html", "w") as f:
            f.write(html_content)
        
        print("HTML report written to ciforge-report.html")

    else:
        if welcome_msg:
            print(welcome_msg + "\n")
        print("# ciforge Report\n")
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
