import subprocess
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Finding:
    file: str
    line: int
    message: str
    severity: str

def git_changed_files() -> List[str]:
    try:
        # Check if we are in a git repo
        subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True, check=True)
        # Get changed files (staged and unstaged) compared to HEAD, or just all tracked/untracked for simplicity in tests
        # To avoid issues with fresh git repos, we can just look at status
        result = subprocess.run(["git", "diff", "--name-only", "HEAD"], capture_output=True, text=True)
        if result.returncode != 0:
            result = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True)
        return [line for line in result.stdout.splitlines() if line.strip()]
    except Exception:
        return []

def git_diff(file_path: str) -> str:
    try:
        result = subprocess.run(["git", "diff", "HEAD", "--", file_path], capture_output=True, text=True)
        if result.returncode != 0 or not result.stdout.strip():
            # If no HEAD, try `git diff --no-index /dev/null file_path` or similar
            # Since we only care about added lines for new files or diffs
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Fake a diff for newly added files
            diff = f"--- /dev/null\n+++ b/{file_path}\n@@ -0,0 +1,{len(content.splitlines())} @@\n"
            for line in content.splitlines():
                diff += f"+{line}\n"
            return diff
        return result.stdout
    except Exception:
        return ""

def _extract_diff_sections(diff_text: str) -> List[Tuple[int, str]]:
    added_lines = []
    current_line = 0
    
    for line in diff_text.splitlines():
        if line.startswith('@@'):
            parts = line.split()
            if len(parts) >= 3:
                new_hunk = parts[2]
                if new_hunk.startswith('+'):
                    new_hunk = new_hunk[1:]
                    new_start = new_hunk.split(',')[0]
                    current_line = int(new_start) - 1
        elif line.startswith('+') and not line.startswith('+++'):
            current_line += 1
            added_lines.append((current_line, line[1:]))
        elif line.startswith('-') and not line.startswith('---'):
            pass
        elif not line.startswith('\\'):
            if current_line > 0:
                current_line += 1
                
    return added_lines
