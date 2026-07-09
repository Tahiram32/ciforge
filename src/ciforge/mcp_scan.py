import json
import os
import re
from .scanner import Finding

def remove_comments(json_string):
    json_string = re.sub(r'//.*', '', json_string)
    json_string = re.sub(r'/\*.*?\*/', '', json_string, flags=re.DOTALL)
    return json_string

def analyze():
    findings = []
    for root, dirs, files in os.walk("."):
        for fname in files:
            if fname in ["mcp.config.jsonc", "mcp.json"]:
                filepath = os.path.join(root, fname)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    data = json.loads(remove_comments(content))
                    if not isinstance(data, dict) or "mcpServers" not in data:
                        findings.append(Finding(filepath, 0, "Missing mcpServers key", "high"))
                except Exception:
                    findings.append(Finding(filepath, 0, "Invalid JSON/JSONC", "high"))
    return findings
