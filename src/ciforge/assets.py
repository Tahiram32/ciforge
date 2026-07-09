import os
from typing import List
from .scanner import Finding

def analyze() -> List[Finding]:
    findings = []
    # Analyze the repository files for large images
    for root, _, files in os.walk('.'):
        if '.git' in root:
            continue
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                file_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(file_path)
                    if size > 500 * 1024:
                        findings.append(Finding(
                            file=file_path,
                            line=0,
                            message=f"Unoptimized asset: {file} is {size / (1024 * 1024):.2f}MB. Compress it.",
                            severity="high"
                        ))
                except Exception:
                    pass
    return findings
