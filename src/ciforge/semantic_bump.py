import subprocess
import os
import re

def bump_version(repo_path: str) -> str:
    result = subprocess.run(["git", "log", "-n", "50", "--oneline"], cwd=repo_path, capture_output=True, text=True)
    log = result.stdout
    
    major = False
    minor = False
    
    for line in log.splitlines():
        if "BREAKING CHANGE" in line or re.search(r'\w+!:', line):
            major = True
        elif "feat:" in line:
            minor = True
            
    pyproject_path = os.path.join(repo_path, "pyproject.toml")
    if not os.path.exists(pyproject_path):
        return ""
        
    with open(pyproject_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    version_match = re.search(r'version\s*=\s*"(\d+)\.(\d+)\.(\d+)"', content)
    if not version_match:
        return ""
        
    v_major, v_minor, v_patch = map(int, version_match.groups())
    
    if major:
        v_major += 1
        v_minor = 0
        v_patch = 0
    elif minor:
        v_minor += 1
        v_patch = 0
    else:
        v_patch += 1
        
    new_version = f"{v_major}.{v_minor}.{v_patch}"
    new_content = content[:version_match.start()] + f'version = "{new_version}"' + content[version_match.end():]
    
    with open(pyproject_path, "w", encoding="utf-8") as f:
        f.write(new_content)
        
    return new_version
