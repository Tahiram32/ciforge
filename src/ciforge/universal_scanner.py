import re
from typing import List
from .scanner import Finding, git_diff, _extract_diff_sections

DANGEROUS_PATTERNS = [
    (r'\bstrcpy\s*\(', "Avoid using strcpy(), which is susceptible to buffer overflows. Use strncpy() instead."),
    (r'\bgets\s*\(', "Never use gets(), which is highly susceptible to buffer overflows. Use fgets() instead."),
    (r'\beval\s*\(', "Avoid using eval(). It can lead to arbitrary code execution if user input is passed."),
    (r'(?i)password\s*=\s*["\'][^"\']+["\']', "Hardcoded secret detected. Use environment variables or a secrets manager."),
    (r'(?i)secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret detected. Use environment variables or a secrets manager."),
]

def analyze(file_path: str, diff_text: str = None) -> List[Finding]:
    if diff_text is None:
        diff_text = git_diff(file_path)
        
    findings = []
    added_lines = _extract_diff_sections(diff_text)
    
    for line_num, line_content in added_lines:
        for pattern, msg in DANGEROUS_PATTERNS:
            if re.search(pattern, line_content):
                findings.append(Finding(file_path, line_num, msg, "high"))
                
    return findings
