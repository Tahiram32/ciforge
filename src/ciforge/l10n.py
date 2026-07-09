import os
import json
from typing import List
from .scanner import Finding

def analyze() -> List[Finding]:
    findings = []
    
    # Scan repo for localization files. Pick en.json as base.
    for root, _, files in os.walk('.'):
        if '.git' in root:
            continue
            
        if 'en.json' in files:
            en_path = os.path.join(root, 'en.json')
            try:
                with open(en_path, 'r', encoding='utf-8') as f:
                    en_data = json.load(f)
                    en_keys = set(en_data.keys())
                    
                for file in files:
                    if file.endswith('.json') and file != 'en.json':
                        file_path = os.path.join(root, file)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            keys = set(data.keys())
                            
                        missing = en_keys - keys
                        for key in missing:
                            findings.append(Finding(
                                file=file_path,
                                line=0,
                                message=f"Missing translation key: '{key}'",
                                severity="medium"
                            ))
            except Exception:
                pass
                
    return findings
