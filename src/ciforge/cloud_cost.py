import re
import glob
from .scanner import Finding

RESOURCE_COSTS = {
    'aws_instance': 50,
    'aws_db_instance': 150,
    'aws_eks_cluster': 73,
}

def analyze() -> list[Finding]:
    findings = []
    total_cost = 0
    for tf_file in glob.glob('**/*.tf', recursive=True):
        try:
            with open(tf_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for res, cost in RESOURCE_COSTS.items():
                count = len(re.findall(rf'resource\s+"{res}"', content))
                total_cost += count * cost
                if count > 0:
                    findings.append(Finding(
                        file=tf_file,
                        line=1,
                        message=f"Cloud Cost: detected {count} {res}, estimated increase ${count * cost}/mo.",
                        severity="low"
                    ))
        except Exception:
            pass
            
    if total_cost > 0:
        findings.append(Finding(
            file="total",
            line=0,
            message=f"Total estimated cloud cost increase: ${total_cost}/mo.",
            severity="low"
        ))
        
    return findings
