import re
from typing import List
from .scanner import Finding, _extract_diff_sections, git_diff

def analyze(file_path: str, diff_text: str = None) -> List[Finding]:
    if diff_text is None:
        diff_text = git_diff(file_path)
        
    findings = []
    added_lines = _extract_diff_sections(diff_text)
    
    contiguous_count = 0
    contiguous_start_line = 0
    
    for line_num, line_content in added_lines:
        # Check for TODO / FIXME / HACK
        match = re.search(r'\b(TODO|FIXME|HACK)\b', line_content)
        if match:
            findings.append(Finding(file_path, line_num, f"Found {match.group(1)}", "medium"))
            
        # Check for console.log, print(), debugger
        if re.search(r'\b(console\.log|print\s*\(|debugger\b)', line_content):
            findings.append(Finding(file_path, line_num, "Found debug statement", "medium"))
            
        # Very large function primitive check
        if line_content.strip() == '':
            contiguous_count = 0
        else:
            if contiguous_count == 0:
                contiguous_start_line = line_num
            contiguous_count += 1
            
            if contiguous_count == 51:
                findings.append(Finding(file_path, contiguous_start_line, "Very large function/block detected (>50 lines)", "low"))
                
    return findings
