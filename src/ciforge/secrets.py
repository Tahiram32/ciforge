import re
from typing import List
from .scanner import Finding, _extract_diff_sections, git_diff

PATTERNS = {
    'aws_key': re.compile(r'(?i)AKIA[0-9A-Z]{16}'),
    'github_token': re.compile(r'(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36}'),
    'generic_secret': re.compile(r'(?i)(password|secret|api[_-]?key|token)\s*[:=]\s*[\'\"][A-Za-z0-9_\-]{8,}[\'\"]')
}

def analyze(file_path: str, diff_text: str = None) -> List[Finding]:
    if diff_text is None:
        diff_text = git_diff(file_path)
        
    findings = []
    added_lines = _extract_diff_sections(diff_text)
    from .ignore import rules as ignore_rules
    
    for line_num, line_content in added_lines:
        if ignore_rules.is_ignored_secret(line_content):
            continue
        for secret_type, pattern in PATTERNS.items():
            if pattern.search(line_content):
                findings.append(Finding(file_path, line_num, f"Leaked secret detected ({secret_type})", "critical"))
                
    return findings
