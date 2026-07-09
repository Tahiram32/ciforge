"""Auto-changelog generator for ciforge.

Parses conventional commit prefixes from git log and groups them into
a formatted markdown changelog.
"""
import subprocess
import re
from typing import Dict, List

# Mapping from conventional commit prefix to section header
_SECTIONS: Dict[str, str] = {
    "feat":     "## ✨ Features",
    "fix":      "## 🐛 Bug Fixes",
    "breaking": "## 💥 Breaking Changes",
    "chore":    "## 🔧 Chores",
    "docs":     "## 📝 Docs",
    "refactor": "## ♻️ Refactors",
}

# Display order for sections
_SECTION_ORDER = ["breaking", "feat", "fix", "refactor", "docs", "chore"]

_COMMIT_RE = re.compile(
    r"^([0-9a-f]+)\s+(feat|fix|breaking|chore|docs|refactor)[:(].*",
    re.IGNORECASE,
)


def generate() -> str:
    """Run git log and return a formatted markdown changelog string."""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--no-merges"],
            capture_output=True,
            text=True,
        )
        lines = result.stdout.splitlines()
    except Exception:
        lines = []

    buckets: Dict[str, List[str]] = {k: [] for k in _SECTIONS}

    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        # Split off the hash prefix
        parts = raw.split(" ", 1)
        if len(parts) < 2:
            continue
        commit_hash, subject = parts[0], parts[1]

        matched = False
        for prefix in _SECTIONS:
            pattern = re.compile(
                rf"^{re.escape(prefix)}[:(]", re.IGNORECASE
            )
            if pattern.match(subject):
                entry = f"- {subject} ({commit_hash})"
                buckets[prefix].append(entry)
                matched = True
                break

    parts_out: List[str] = ["# Changelog\n"]
    for key in _SECTION_ORDER:
        if buckets.get(key):
            parts_out.append(_SECTIONS[key])
            parts_out.extend(buckets[key])
            parts_out.append("")  # blank line between sections

    return "\n".join(parts_out)


def write_changelog(path: str = "CHANGELOG.md") -> None:
    """Generate the changelog and write it to the given file path."""
    content = generate()
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Changelog written to {path}")
