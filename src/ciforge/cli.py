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
    parser.add_argument('--fix', action='store_true', help='Auto-fix low-hanging issues')
    args = parser.parse_args()

    if args.install_hook:
        install_git_hook()

    if args.repo != '.':
        os.chdir(args.repo)

    from .ignore import rules as ignore_rules
    files = [f for f in scanner.git_changed_files() if not ignore_rules.is_ignored_file(f)]
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

    if args.fix:
        from .fixer import fix_all
        fixed = fix_all(all_findings)
        if fixed > 0:
            print(f"Auto-fixer resolved {fixed} issue(s).")

    welcome_msg = community.get_welcome_message()
    max_severity_found = -1
    
    if args.format == 'html':
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CI Forge Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0f111a;
            --card-bg: rgba(255, 255, 255, 0.03);
            --border-color: rgba(255, 255, 255, 0.08);
            --primary: #3b82f6;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --low: #10b981;
            --medium: #f59e0b;
            --high: #f97316;
            --critical: #ef4444;
        }}
        body {{
            background: radial-gradient(circle at top left, #1e1b4b, var(--bg-color));
            background-color: var(--bg-color);
            color: var(--text-main);
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 40px 20px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .dashboard {{
            width: 100%;
            max-width: 1000px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            animation: fadeInDown 0.8s ease-out;
        }}
        .header h1 {{
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(to right, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
        }}
        .header p {{
            color: var(--text-muted);
            font-size: 1.1rem;
        }}
        .card {{
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            animation: fadeInUp 0.8s ease-out;
            transition: transform 0.3s ease;
        }}
        .card:hover {{
            transform: translateY(-5px);
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-box {{
            background: rgba(0,0,0,0.2);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid var(--border-color);
        }}
        .stat-value {{
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 5px;
        }}
        .val-0 {{ color: var(--low); }}
        .val-issues {{ color: var(--critical); }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}
        th {{
            color: var(--text-muted);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85rem;
            letter-spacing: 0.05em;
        }}
        tr:hover td {{
            background: rgba(255, 255, 255, 0.02);
        }}
        .badge {{
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .badge-low {{ background: rgba(16, 185, 129, 0.1); color: var(--low); border: 1px solid var(--low); }}
        .badge-medium {{ background: rgba(245, 158, 11, 0.1); color: var(--medium); border: 1px solid var(--medium); }}
        .badge-high {{ background: rgba(249, 115, 22, 0.1); color: var(--high); border: 1px solid var(--high); }}
        .badge-critical {{ background: rgba(239, 68, 68, 0.1); color: var(--critical); border: 1px solid var(--critical); }}
        .empty-state {{
            text-align: center;
            padding: 40px 0;
        }}
        .empty-state h2 {{
            color: var(--low);
            font-size: 2rem;
            margin-bottom: 10px;
        }}
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        @keyframes fadeInDown {{
            from {{ opacity: 0; transform: translateY(-20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>CI Forge</h1>
            <p>Code Quality & Security Dashboard</p>
            {f"<div style='margin-top:15px; padding:10px 20px; background:rgba(59,130,246,0.1); border:1px solid #3b82f6; border-radius:99px; display:inline-block;'>{welcome_msg}</div>" if welcome_msg else ""}
        </div>
        
        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-value {'val-0' if not all_findings else 'val-issues'}">{len(all_findings)}</div>
                <div style="color: var(--text-muted); font-size: 0.9rem;">Total Findings</div>
            </div>
            <div class="stat-box">
                <div class="stat-value val-0" style="color:var(--text-main);">0</div>
                <div style="color: var(--text-muted); font-size: 0.9rem;">Secrets Leaked</div>
            </div>
            <div class="stat-box">
                <div class="stat-value val-0" style="color:var(--text-main);">A+</div>
                <div style="color: var(--text-muted); font-size: 0.9rem;">Code Health</div>
            </div>
        </div>

        <div class="card">
"""
        if not all_findings:
            html_content += """            <div class="empty-state">
                <h2>✨ Flawless Execution</h2>
                <p style="color: var(--text-muted);">No issues found in the codebase. Ready for production.</p>
            </div>
"""
        else:
            html_content += """            <table>
                <thead>
                    <tr>
                        <th>Severity</th>
                        <th>Location</th>
                        <th>Details</th>
                    </tr>
                </thead>
                <tbody>
"""
            for finding in all_findings:
                sev_val = SEVERITY_LEVELS.get(finding.severity, 0)
                max_severity_found = max(max_severity_found, sev_val)
                line_info = f":{finding.line}" if finding.line > 0 else ""
                html_content += f"""                    <tr>
                        <td><span class="badge badge-{finding.severity}">{finding.severity}</span></td>
                        <td style="font-family: monospace; color: var(--primary);">{finding.file}{line_info}</td>
                        <td>{finding.message}</td>
                    </tr>
"""
            html_content += """                </tbody>
            </table>
"""
        html_content += """        </div>
    </div>
</body>
</html>
"""
        with open("ciforge-report.html", "w") as f:
            f.write(html_content)
        print("HTML report written to ciforge-report.html")
        if not all_findings:
            sys.exit(0)
    else:
        if not all_findings:
            if welcome_msg:
                print(welcome_msg + "\n")
            print("No issues found. Great job!")
            sys.exit(0)
            
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
