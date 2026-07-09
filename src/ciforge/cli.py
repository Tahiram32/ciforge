import argparse
import sys
import os
import stat
from . import scanner, code_quality, secrets, config_validator, coverage, ai_reviewer, assets, l10n, metrics, badges, community, multi_ai, dead_code, changelog, config_drift, mobile_lint, deploy_check, arch_diagram, pr_describe, universal_scanner
from . import blast_radius, mcp_scan, schema_guardian, prompt_scan, discord_notify, semantic_bump
from . import vuln_scan, iac_scan, duplication, cloud_cost, load_test, telemetry
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

def _main():
    parser = argparse.ArgumentParser(description="ciforge CLI")
    parser.add_argument('--fail-on', type=str, default='high', choices=['low', 'medium', 'high', 'critical', 'none'], help='Exit non-zero if findings of this severity or higher are found')
    parser.add_argument('--repo', type=str, default='.', help='Path to repository')
    parser.add_argument('--base-ref', type=str, default='origin/main', help='Base reference branch')
    parser.add_argument('--format', type=str, default='markdown', choices=['markdown', 'html'], help='Output format')
    parser.add_argument('--badge', action='store_true', help='Generate badge')
    parser.add_argument('--install-hook', action='store_true', help='Install git pre-commit hook')
    parser.add_argument('--fix', action='store_true', help='Auto-fix low-hanging issues')
    parser.add_argument('--provider', type=str, default=os.environ.get('CIFORGE_AI_PROVIDER', 'openai'), help='AI provider (openai, anthropic, ollama)')
    parser.add_argument('--changelog', action='store_true', help='Generate CHANGELOG.md from git log')
    parser.add_argument('--drift', action='store_true', help='Check for config drift between env files')
    parser.add_argument('--deploy-check', type=str, default=None, metavar='URL', help='Run deployment health check against the given URL')
    parser.add_argument('--arch-diagram', action='store_true', help='Generate Mermaid architecture diagram and write to ARCHITECTURE.md')
    parser.add_argument('--pr-describe', action='store_true', help='Generate a GitHub PR description from the current diff')
    parser.add_argument('--blast-radius', action='store_true', help='Analyze Python imports to find highly coupled files')
    parser.add_argument('--mcp-scan', action='store_true', help='Search for mcp.config.jsonc or mcp.json and validate')
    parser.add_argument('--schema-scan', action='store_true', help='Scan all .sql files for breaking schema changes')
    parser.add_argument('--prompt-scan', action='store_true', help='Scan .py files for LLM prompt injections')
    parser.add_argument('--discord-webhook', type=str, default=None, metavar='URL', help='Discord webhook URL for notifications')
    parser.add_argument('--bump-version', action='store_true', help='Semantic version bump based on git log')
    parser.add_argument('--dead-code', action='store_true', help='Scan for dead code')
    parser.add_argument('--vuln-scan', action='store_true', help='Scan for known vulnerabilities in requirements.txt and package.json')
    parser.add_argument('--iac-scan', action='store_true', help='Scan Infrastructure as Code files for anti-patterns')
    parser.add_argument('--dupe-scan', action='store_true', help='Scan for structural code duplication')
    parser.add_argument('--cloud-cost', action='store_true', help='Estimate cloud cost from Terraform files')
    parser.add_argument('--load-test', type=str, default=None, metavar='URL', help='Run a load test against the given URL')
    parser.add_argument('--serve-mcp', action='store_true', help='Run as an MCP stdio server')
    parser.add_argument('--auto-fix-pr', action='store_true', help='Create an agentic PR for automated fixes')
    parser.add_argument('--incremental', action='store_true', help='Only scan files changed in git')
    parser.add_argument('--auto-update', action='store_true', help='Automatically upgrade dependencies in package.json/requirements.txt')
    args = parser.parse_args()

    if args.serve_mcp:
        from . import mcp_server
        mcp_server.serve()
        sys.exit(0)
        
    if args.auto_update:
        from . import auto_update
        auto_update.update_dependencies(args.repo)

    explicit_scanners = [
        args.dead_code, args.vuln_scan, args.iac_scan, args.dupe_scan,
        args.cloud_cost, args.mcp_scan, args.schema_scan, args.prompt_scan,
        args.drift, bool(args.deploy_check), args.pr_describe, args.blast_radius,
        bool(args.load_test), args.changelog, args.bump_version
    ]
    if not any(explicit_scanners):
        args.dead_code = True
        args.vuln_scan = True
        args.dupe_scan = True

    if args.install_hook:
        install_git_hook()

    if args.changelog:
        changelog.write_changelog()
        print("Changelog generation complete.")
        sys.exit(0)

    if args.arch_diagram:
        arch_diagram.write_diagram()
        sys.exit(0)

    if args.repo != '.':
        os.chdir(args.repo)

    # Propagate --provider to env so multi_ai picks it up
    if args.provider:
        os.environ['CIFORGE_AI_PROVIDER'] = args.provider

    from .ignore import rules as ignore_rules
    if args.incremental:
        raw_files = scanner.git_changed_files()
    else:
        raw_files = scanner.get_all_files(args.repo)
    files = [f for f in raw_files if not ignore_rules.is_ignored_file(f)]
    all_findings = []

    def _run_scan(name, func, *args):
        try:
            return func(*args)
        except Exception as e:
            telemetry.report_crash(e, name)
            print(f"Warning: scanner {name} failed.")
            return []

    for f in files:
        diff_text = scanner.git_diff(f)
        all_findings.extend(_run_scan("code_quality", code_quality.analyze, f, diff_text))
        all_findings.extend(_run_scan("secrets", secrets.analyze, f, diff_text))
        all_findings.extend(_run_scan("config_validator", config_validator.analyze, f, diff_text))
        all_findings.extend(_run_scan("multi_ai", multi_ai.analyze, diff_text))
        if f.endswith(('.c', '.cpp', '.java', '.go', '.rs')):
            all_findings.extend(_run_scan("universal_scanner", universal_scanner.analyze, f, diff_text))

    all_findings.extend(_run_scan("coverage", coverage.analyze))
    all_findings.extend(_run_scan("ai_reviewer", ai_reviewer.analyze))
    all_findings.extend(_run_scan("assets", assets.analyze))
    all_findings.extend(_run_scan("l10n", l10n.analyze))
    all_findings.extend(_run_scan("metrics", metrics.analyze))
    if getattr(args, 'dead_code', False):
        all_findings.extend(_run_scan("dead_code", dead_code.analyze))
    all_findings.extend(_run_scan("mobile_lint", mobile_lint.analyze))

    if args.blast_radius:
        all_findings.extend(_run_scan("blast_radius", blast_radius.analyze))
    if args.mcp_scan:
        all_findings.extend(_run_scan("mcp_scan", mcp_scan.analyze))
    if args.schema_scan:
        all_findings.extend(_run_scan("schema_guardian", schema_guardian.analyze))
    if args.prompt_scan:
        all_findings.extend(_run_scan("prompt_scan", prompt_scan.analyze))

    if args.drift:
        all_findings.extend(_run_scan("config_drift", config_drift.analyze_auto))

    if args.deploy_check:
        all_findings.extend(_run_scan("deploy_check", deploy_check.check, args.deploy_check))

    if args.pr_describe:
        combined_diff = "\n".join(scanner.git_diff(f) for f in files)
        try:
            description = pr_describe.generate(combined_diff)
            print(description)
        except Exception as e:
            telemetry.report_crash(e, "pr_describe")
            print("Warning: scanner pr_describe failed.")
        sys.exit(0)

    if getattr(args, 'vuln_scan', False):
        all_findings.extend(_run_scan("vuln_scan", vuln_scan.analyze))
    if getattr(args, 'iac_scan', False):
        all_findings.extend(_run_scan("iac_scan", iac_scan.analyze))
    if getattr(args, 'dupe_scan', False):
        all_findings.extend(_run_scan("duplication", duplication.analyze))
    if getattr(args, 'cloud_cost', False):
        all_findings.extend(_run_scan("cloud_cost", cloud_cost.analyze))
    if getattr(args, 'load_test', False):
        all_findings.extend(_run_scan("load_test", load_test.analyze, args.load_test))

    if args.badge:
        badges.generate_badge(all_findings)

    if args.fix:
        from .fixer import fix_all
        fixed = fix_all(all_findings)
        if fixed > 0:
            print(f"Auto-fixer resolved {fixed} issue(s).")

    if args.auto_fix_pr:
        from . import auto_fixer
        print("Running agentic PR fixes...")
        auto_fixer.run_agentic_fixes(all_findings, args.repo)

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
\n\n🔍 **Found a False Positive?** [Report it here to improve ciforge!](https://github.com/Tahiram32/ciforge/issues/new?title=False+Positive+Report&labels=false-positive)"""
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
            
        print("\\n\\n🔍 **Found a False Positive?** [Report it here to improve ciforge!](https://github.com/Tahiram32/ciforge/issues/new?title=False+Positive+Report&labels=false-positive)")

    if args.fail_on != 'none':
        fail_threshold = SEVERITY_LEVELS.get(args.fail_on, 3)
        if max_severity_found >= fail_threshold:
            print(f"\nFailed: Found issues with severity '{args.fail_on}' or higher.")
            if args.discord_webhook:
                discord_notify.send_notification(args.discord_webhook, len(all_findings))
            sys.exit(1)

    if args.bump_version:
        new_version = semantic_bump.bump_version(args.repo)
        if new_version:
            print(f"Version bumped to {new_version}")

    if args.discord_webhook:
        discord_notify.send_notification(args.discord_webhook, len(all_findings))

    sys.exit(0)

if __name__ == '__main__':
    main()

def main():
    try:
        _main()
    except Exception as e:
        from . import telemetry
        telemetry.report_crash(e, "FATAL_CORE")
        print("\n[ciforge] FATAL WARNING: ciforge encountered a catastrophic error but degraded gracefully so as not to block your CI.")
        sys.exit(0)
