import json
import re
from typing import List
from .scanner import Finding, git_diff, _extract_diff_sections

def analyze(file_path: str, diff_text: str = None) -> List[Finding]:
    findings = []
    
    if diff_text is None:
        diff_text = git_diff(file_path)
        
    added_lines = _extract_diff_sections(diff_text)
    
    if file_path.endswith('.env') and not file_path.endswith('.env.example'):
        if added_lines:
            findings.append(Finding(file_path, 0, ".env file added to diff", "high"))
            
    if file_path.endswith('.json'):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            json.loads(content)
        except json.JSONDecodeError as e:
            findings.append(Finding(file_path, getattr(e, 'lineno', 0), f"Invalid JSON: {str(e)}", "high"))
        except FileNotFoundError:
            pass

    if file_path.endswith('.yaml') or file_path.endswith('.yml'):
        for line_num, line_content in added_lines:
            if re.search(r'^\s*\t', line_content) or '\t' in line_content:
                findings.append(Finding(file_path, line_num, "YAML file indented with tabs", "medium"))
                
    if file_path.endswith('.toml'):
        try:
            import tomllib
        except ImportError:
            tomllib = None
        if tomllib:
            try:
                with open(file_path, 'rb') as f:
                    tomllib.load(f)
            except tomllib.TOMLDecodeError as e:
                findings.append(Finding(file_path, 0, f"Invalid TOML: {str(e)}", "high"))
            except FileNotFoundError:
                pass

    if file_path.endswith('.xml'):
        import xml.etree.ElementTree as ET
        try:
            ET.parse(file_path)
        except ET.ParseError as e:
            findings.append(Finding(file_path, 0, f"Invalid XML: {str(e)}", "high"))
        except FileNotFoundError:
            pass

    return findings
