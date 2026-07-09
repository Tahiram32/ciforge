import ast
import os
from .scanner import Finding

def is_unsafe_string(node):
    if isinstance(node, ast.JoinedStr):
        for val in node.values:
            if isinstance(val, ast.FormattedValue):
                if isinstance(val.value, ast.Name) and val.value.id == "user_input":
                    return True
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Attribute) and node.func.attr == "format":
            for kw in node.keywords:
                if kw.arg == "user_input":
                    return True
    return False

def analyze():
    findings = []
    for root, dirs, files in os.walk("."):
        for fname in files:
            if fname.endswith(".py"):
                filepath = os.path.join(root, fname)
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        tree = ast.parse(f.read(), filename=filepath)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call):
                            func_name = ""
                            if isinstance(node.func, ast.Attribute):
                                if isinstance(node.func.value, ast.Name):
                                    func_name = f"{node.func.value.id}.{node.func.attr}"
                                elif isinstance(node.func.value, ast.Attribute) and isinstance(node.func.value.value, ast.Name):
                                    func_name = f"{node.func.value.value.id}.{node.func.value.attr}.{node.func.attr}"
                            
                            if func_name in ("llm.invoke", "openai.ChatCompletion.create"):
                                unsafe = False
                                for arg in node.args:
                                    if is_unsafe_string(arg):
                                        unsafe = True
                                for kw in node.keywords:
                                    if is_unsafe_string(kw.value):
                                        unsafe = True
                                if unsafe:
                                    findings.append(Finding(filepath, getattr(node, 'lineno', 0), "Potential Prompt Injection: Unsafe string concatenation in LLM call", "high"))
                except Exception:
                    pass
    return findings
