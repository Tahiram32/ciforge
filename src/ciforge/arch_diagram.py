"""Architecture diagram generator for ciforge."""

import ast
import os
from typing import Dict, List, Set

# Directories to exclude when walking the project
_EXCLUDED_DIRS: Set[str] = {".venv", ".git", "node_modules", "tests"}


def _get_project_modules() -> Set[str]:
    """Collect all internal module names by walking .py files."""
    modules: Set[str] = set()
    for root, dirs, files in os.walk("."):
        # Prune excluded directories in-place
        dirs[:] = [d for d in dirs if d not in _EXCLUDED_DIRS]
        for fname in files:
            if fname.endswith(".py"):
                module_name = fname[:-3]  # strip .py
                modules.add(module_name)
    return modules


def _parse_imports(filepath: str) -> List[str]:
    """Parse a Python file and return a list of module names it imports."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as fh:
            source = fh.read()
        tree = ast.parse(source, filename=filepath)
    except (SyntaxError, OSError):
        return []

    imported: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                # Only the top-level name matters
                imported.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.append(node.module.split(".")[0])
    return imported


def generate() -> str:
    """Walk the project, parse imports, and return a Mermaid diagram string.

    Only edges between internal project modules are included.
    """
    project_modules = _get_project_modules()

    # Build adjacency: source_module -> [imported internal modules]
    graph: Dict[str, List[str]] = {}

    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in _EXCLUDED_DIRS]
        for fname in files:
            if not fname.endswith(".py"):
                continue
            module_name = fname[:-3]
            filepath = os.path.join(root, fname)
            imported = _parse_imports(filepath)

            internal_deps = [
                dep for dep in imported
                if dep in project_modules and dep != module_name
            ]

            if internal_deps:
                if module_name not in graph:
                    graph[module_name] = []
                for dep in internal_deps:
                    if dep not in graph[module_name]:
                        graph[module_name].append(dep)

    lines = ["graph TD"]
    if not graph:
        lines.append("    %% No internal module dependencies found")
    else:
        for src, targets in sorted(graph.items()):
            for tgt in sorted(targets):
                lines.append(f"    {src} --> {tgt}")

    return "\n".join(lines)


def write_diagram() -> None:
    """Generate the Mermaid diagram and write/append it to ARCHITECTURE.md."""
    diagram = generate()
    md_content = f"\n## Architecture Diagram\n\n```mermaid\n{diagram}\n```\n"

    mode = "a" if os.path.exists("ARCHITECTURE.md") else "w"
    with open("ARCHITECTURE.md", mode, encoding="utf-8") as fh:
        fh.write(md_content)

    print("Architecture diagram written to ARCHITECTURE.md")
