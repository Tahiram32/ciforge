import json
import os
from typing import List
from .scanner import Finding

def analyze(repo_root: str = ".") -> List[Finding]:
    findings = []
    coverage_file = os.path.join(repo_root, ".ciforge-coverage.json")
    
    if os.path.exists(coverage_file):
        try:
            with open(coverage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cov = data.get('coverage', 100.0)
                if cov < 80.0:
                    findings.append(Finding(coverage_file, 0, f"Code coverage too low: {cov}% (< 80%)", "medium"))
        except (json.JSONDecodeError, ValueError):
            findings.append(Finding(coverage_file, 0, "Invalid coverage file format", "medium"))
            
    return findings
