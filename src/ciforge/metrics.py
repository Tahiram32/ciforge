import subprocess
from typing import List
from .scanner import Finding

def analyze() -> List[Finding]:
    findings = []
    try:
        # Get commit timestamps
        result = subprocess.run(["git", "log", "--format=%ct", "--reverse"], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.splitlines()
            if len(lines) >= 2:
                first_commit = int(lines[0])
                last_commit = int(lines[-1])
                diff_seconds = last_commit - first_commit
                hours = diff_seconds / 3600
                findings.append(Finding(
                    file="Git Metrics",
                    line=0,
                    message=f"Velocity Report: Branch active for {hours:.1f} hours over {len(lines)} commits.",
                    severity="low"
                ))
    except Exception:
        pass
        
    return findings
