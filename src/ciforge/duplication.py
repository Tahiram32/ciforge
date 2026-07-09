import ast
import glob
from .scanner import Finding

def get_ast_body(node):
    body = node.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, (ast.Str, ast.Constant)):
        body = body[1:]
    return body

def ast_to_string(body_nodes):
    return ast.dump(ast.Module(body=body_nodes, type_ignores=[]))

def analyze() -> list[Finding]:
    findings = []
    functions = {} 
    
    for py_file in glob.glob('**/*.py', recursive=True):
        if '.venv' in py_file or 'tests' in py_file or 'duplication.py' in py_file:
            continue
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content, filename=py_file)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if hasattr(node, "end_lineno") and hasattr(node, "lineno") and node.end_lineno is not None and node.lineno is not None:
                        if node.end_lineno - node.lineno < 2:
                            continue

                    body = get_ast_body(node)
                    if not body:
                        continue
                    if len(body) <= 1 and isinstance(body[0], (ast.Pass, ast.Return)):
                        continue
                        
                    is_not_implemented = False
                    if len(body) == 1 and isinstance(body[0], ast.Raise):
                        exc = body[0].exc
                        if isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name) and exc.func.id == "NotImplementedError":
                            is_not_implemented = True
                        elif isinstance(exc, ast.Name) and exc.id == "NotImplementedError":
                            is_not_implemented = True
                    if is_not_implemented:
                        continue
                        
                    body_str = ast_to_string(body)
                    if body_str not in functions:
                        functions[body_str] = []
                    functions[body_str].append((py_file, node.name, node.lineno))
        except Exception:
            pass
            
    reported = set()
    for body_str, funcs in functions.items():
        if len(funcs) > 1:
            for i in range(len(funcs)):
                for j in range(i + 1, len(funcs)):
                    f1, name1, line1 = funcs[i]
                    f2, name2, line2 = funcs[j]
                    
                    pair_id = tuple(sorted([f"{f1}:{name1}", f"{f2}:{name2}"]))
                    if pair_id in reported:
                        continue
                    reported.add(pair_id)
                    
                    findings.append(Finding(
                        file=f1,
                        line=line1,
                        message=f"💡 Tip: '{name1}' in {f1} is identical to '{name2}' in {f2}. Consider merging them into a single shared helper!",
                        severity="medium"
                    ))
                    
    return findings
