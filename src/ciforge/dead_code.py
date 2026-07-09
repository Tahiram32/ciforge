"""Dead code detector for ciforge.

Walks all .py files in the current directory (excluding .venv, node_modules, .git),
uses ast to find defined function/class names, then checks whether each name is
referenced outside its definition file.
"""
import ast
import os
from typing import List, Dict, Set
from .scanner import Finding

# Names that are always considered "in use" regardless of references
_SKIP_NAMES: Set[str] = {
    "__init__",
    "__main__",
    "main",
    "setUp",
    "tearDown",
    "setUpClass",
    "tearDownClass",
    "setUpModule",
    "tearDownModule",
}

_EXCLUDED_DIRS = {".venv", "node_modules", ".git", "__pycache__"}


def _iter_py_files():
    """Yield relative paths to all .py files, skipping excluded dirs."""
    for dirpath, dirnames, filenames in os.walk("."):
        # Prune excluded directories in-place so os.walk doesn't descend into them
        dirnames[:] = [d for d in dirnames if d not in _EXCLUDED_DIRS]
        for fname in filenames:
            if fname.endswith(".py"):
                yield os.path.join(dirpath, fname)


def _collect_definitions(filepath: str) -> List[str]:
    """Return list of top-level FunctionDef and ClassDef names in a file."""
    names: List[str] = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
        tree = ast.parse(source, filename=filepath)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.append(node.name)
    except Exception:
        pass
    return names


def analyze() -> List[Finding]:
    """Detect dead code (defined but never referenced outside definition file).

    Returns a list of Finding objects with severity 'low'.
    """
    findings: List[Finding] = []

    # Phase 1: collect all definitions per file
    definitions: Dict[str, List[str]] = {}  # filepath -> [name, ...]
    all_files = list(_iter_py_files())

    for filepath in all_files:
        defs = _collect_definitions(filepath)
        if defs:
            definitions[filepath] = defs

    # Phase 2: for each defined name, check if it's referenced in ANY other file
    for def_file, names in definitions.items():
        # Read the content of all OTHER files once into a combined string
        other_contents = []
        for fp in all_files:
            if fp == def_file:
                continue
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                    other_contents.append(fh.read())
            except Exception:
                pass
        combined_other = "\n".join(other_contents)

        for name in names:
            # Skip reserved / always-used names and test helpers
            if name in _SKIP_NAMES:
                continue
            if name.startswith("test_") or name.startswith("Test"):
                continue

            # Check if used in any other file
            if name in combined_other:
                continue

            # Check if used locally in its own file (more than just the 'def' or 'class' statement)
            import re
            try:
                with open(def_file, "r", encoding="utf-8", errors="ignore") as f:
                    local_content = f.read()
                # Find all word boundary occurrences of the name
                occurrences = len(re.findall(r'\b' + re.escape(name) + r'\b', local_content))
                if occurrences > 1:
                    continue  # Used locally
            except Exception:
                pass

            findings.append(
                Finding(
                    file=def_file,
                    line=0,
                    message=f"Dead code: '{name}' is defined but never referenced",
                    severity="low",
                )
            )

    return findings
