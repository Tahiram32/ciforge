import os
import re
from .scanner import Finding

def fix_all(findings: list[Finding]) -> int:
    fixed_count = 0
    findings_by_file = {}
    for f in findings:
        if f.line > 0:  # Only attempt fixes on specific lines
            findings_by_file.setdefault(f.file, []).append(f)
            
    for file_path, file_findings in findings_by_file.items():
        if not os.path.exists(file_path):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            continue
            
        modified = False
        
        # Sort descending to avoid shifting indices if we delete lines
        file_findings.sort(key=lambda x: x.line, reverse=True)
        
        for finding in file_findings:
            line_idx = finding.line - 1
            if not (0 <= line_idx < len(lines)):
                continue
                
            if "YAML file indented with tabs" in finding.message:
                lines[line_idx] = lines[line_idx].replace('\t', '  ')
                finding.message += " [AUTO-FIXED]"
                modified = True
                fixed_count += 1
                
            elif "Found debug statement" in finding.message:
                line_str = lines[line_idx]
                indent = line_str[:len(line_str) - len(line_str.lstrip())]
                if file_path.endswith('.py'):
                    lines[line_idx] = f"{indent}# {line_str.lstrip()}"
                elif file_path.endswith(('.js', '.ts', '.jsx', '.tsx')):
                    lines[line_idx] = f"{indent}// {line_str.lstrip()}"
                else:
                    lines[line_idx] = "" # Delete for unknown extensions
                finding.message += " [AUTO-FIXED]"
                modified = True
                fixed_count += 1

        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
                
    return fixed_count
