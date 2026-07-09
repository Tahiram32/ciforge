import os
from .scanner import Finding

def analyze():
    findings = []
    for root, dirs, files in os.walk("."):
        for fname in files:
            if fname.endswith(".sql"):
                filepath = os.path.join(root, fname)
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for i, line in enumerate(f):
                        line_upper = line.upper()
                        if "DROP TABLE" in line_upper or "DROP COLUMN" in line_upper or ("ALTER TABLE" in line_upper and "DROP" in line_upper):
                            findings.append(Finding(filepath, i + 1, f"Breaking Schema Change detected: {line.strip()}", "high"))
    return findings
