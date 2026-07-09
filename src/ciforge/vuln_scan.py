import os
import re
import json
from .scanner import Finding

KNOWN_VULNS = {
    'requests': (2, 31, 0),
    'django': (4, 2, 0),
    'lodash': (4, 17, 21),
}

def parse_version(v_str):
    m = re.search(r'(\d+)\.(\d+)(?:\.(\d+))?', v_str)
    if m:
        return tuple(int(x) if x else 0 for x in m.groups())
    return (999, 999, 999)

def analyze() -> list[Finding]:
    findings = []
    if os.path.exists('requirements.txt'):
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                m = re.match(r'^([a-zA-Z0-9_\-]+)[=!<>~]+(.*)$', line.strip())
                if m:
                    pkg = m.group(1).lower()
                    ver = m.group(2)
                    if pkg in KNOWN_VULNS and parse_version(ver) < KNOWN_VULNS[pkg]:
                        findings.append(Finding(
                            file='requirements.txt',
                            line=i,
                            message=f"🚨 Security Risk: '{pkg}' has a known vulnerability. Tip: Update this package in requirements.txt to keep your users safe!",
                            severity='high'
                        ))

    if os.path.exists('package.json'):
        try:
            with open('package.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
            for pkg, ver in deps.items():
                p = pkg.lower()
                if p in KNOWN_VULNS and parse_version(ver) < KNOWN_VULNS[p]:
                    findings.append(Finding(
                        file='package.json',
                        line=1,
                        message=f"🚨 Security Risk: '{pkg}' has a known vulnerability. Tip: Update this package in package.json to keep your users safe!",
                        severity='high'
                    ))
        except Exception:
            pass
            
    return findings
