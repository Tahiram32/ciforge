import re
import ast
import os
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
                
    # AST analysis for python files
    if file_path.endswith('.py') and os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=file_path)
                
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Cyclomatic complexity
                    complexity = 1
                    for child in ast.walk(node):
                        if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.ExceptHandler, ast.With, ast.AsyncFor, ast.AsyncWith)):
                            complexity += 1
                        elif isinstance(child, ast.BoolOp):
                            complexity += len(child.values) - 1
                            
                    if complexity > 10:
                        findings.append(Finding(file_path, getattr(node, 'lineno', 0), f"High cyclomatic complexity: {complexity} (>10)", "high"))
                        
                    # Long function check
                    if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                        if node.end_lineno - node.lineno > 50:
                            findings.append(Finding(file_path, node.lineno, f"Long function: {node.name} is {node.end_lineno - node.lineno} lines (>50)", "high"))
        except Exception:
            pass

    return findings
