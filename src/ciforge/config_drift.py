"""Config drift detector for ciforge.

Parses pairs of .env-format files and reports keys present in one but
missing from the other.
"""
import os
import re
from typing import Dict, List, Tuple
from .scanner import Finding

# Common env file pairs to auto-detect
_AUTO_PAIRS: List[Tuple[str, str]] = [
    (".env.production", ".env.staging"),
    (".env.example", ".env"),
    (".env.prod", ".env.dev"),
]

_COMMENT_RE = re.compile(r"^\s*#")
_KEY_VALUE_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=")


def _parse_env_file(filepath: str) -> Dict[str, int]:
    """Parse an .env-format file and return {KEY: line_number} mapping."""
    keys: Dict[str, int] = {}
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for lineno, line in enumerate(f, start=1):
                if _COMMENT_RE.match(line) or not line.strip():
                    continue
                m = _KEY_VALUE_RE.match(line)
                if m:
                    keys[m.group(1)] = lineno
    except Exception:
        pass
    return keys


def analyze(file_a: str, file_b: str) -> List[Finding]:
    """Compare two env files and return drift findings.

    Reports keys present in file_a but missing from file_b and vice versa.
    """
    findings: List[Finding] = []
    keys_a = _parse_env_file(file_a)
    keys_b = _parse_env_file(file_b)

    name_a = os.path.basename(file_a)
    name_b = os.path.basename(file_b)

    for key, lineno in keys_a.items():
        if key not in keys_b:
            findings.append(
                Finding(
                    file=file_a,
                    line=lineno,
                    message=(
                        f"Config drift: '{key}' in {name_a} "
                        f"but missing from {name_b}"
                    ),
                    severity="medium",
                )
            )

    for key, lineno in keys_b.items():
        if key not in keys_a:
            findings.append(
                Finding(
                    file=file_b,
                    line=lineno,
                    message=(
                        f"Config drift: '{key}' in {name_b} "
                        f"but missing from {name_a}"
                    ),
                    severity="medium",
                )
            )

    return findings


def analyze_auto() -> List[Finding]:
    """Auto-detect common env file pairs in the repo and analyze each pair."""
    findings: List[Finding] = []
    for file_a, file_b in _AUTO_PAIRS:
        if os.path.isfile(file_a) and os.path.isfile(file_b):
            findings.extend(analyze(file_a, file_b))
    return findings
