import os
import re
import json
import urllib.request
from .scanner import Finding

def check_osv(pkg: str, ver: str, ecosystem: str) -> bool:
    url = "https://api.osv.dev/v1/query"
    data = json.dumps({"version": ver, "package": {"name": pkg, "ecosystem": ecosystem}}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            if 'vulns' in result and result['vulns']:
                return True
    except Exception:
        pass
    return False

def clean_version(v_str: str) -> str:
    m = re.search(r'(\d+\.\d+(?:\.\d+)?)', v_str)
    if m:
        return m.group(1)
    return v_str.replace('^', '').replace('~', '').replace('=', '').replace('>', '').replace('<', '').strip()

def analyze() -> list[Finding]:
    findings = []
    if os.path.exists('requirements.txt'):
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                m = re.match(r'^([a-zA-Z0-9_\-]+)[=!<>~]+(.*)$', line.strip())
                if m:
                    pkg = m.group(1)
                    ver = clean_version(m.group(2))
                    if check_osv(pkg, ver, "PyPI"):
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
                clean_ver = clean_version(ver)
                if check_osv(pkg, clean_ver, "npm"):
                    findings.append(Finding(
                        file='package.json',
                        line=1,
                        message=f"🚨 Security Risk: '{pkg}' has a known vulnerability. Tip: Update this package in package.json to keep your users safe!",
                        severity='high'
                    ))
        except Exception:
            pass
            
    return findings
