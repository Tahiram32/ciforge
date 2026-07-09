import ast
import os
from .scanner import Finding

def _get_project_modules():
    modules = set()
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in {".venv", ".git", "node_modules", "tests"}]
        for fname in files:
            if fname.endswith(".py"):
                modules.add(fname[:-3])
    return modules

def analyze():
    findings = []
    project_modules = _get_project_modules()
    
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in {".venv", ".git", "node_modules", "tests"}]
        for fname in files:
            if not fname.endswith(".py"): continue
            filepath = os.path.join(root, fname)
            
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    tree = ast.parse(f.read(), filename=filepath)
            except Exception:
                continue
                
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imported.add(node.module.split(".")[0])
                        
            internal_deps = [dep for dep in imported if dep in project_modules and dep != fname[:-3]]
            
            if len(internal_deps) > 10:
                findings.append(Finding(filepath, 0, f"Blast Radius Risk: {filepath} is highly coupled ({len(internal_deps)} internal imports)", "medium"))
    
    return findings
