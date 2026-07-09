import os
import urllib.request
import json
import re

def get_latest_pypi_version(package_name: str) -> str:
    try:
        url = f"https://pypi.org/pypi/{package_name}/json"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data["info"]["version"]
    except Exception:
        return ""

def get_latest_npm_version(package_name: str) -> str:
    try:
        url = f"https://registry.npmjs.org/{package_name}/latest"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data["version"]
    except Exception:
        return ""

def update_dependencies(repo_path: str):
    # Update requirements.txt
    req_path = os.path.join(repo_path, "requirements.txt")
    if os.path.exists(req_path):
        with open(req_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        new_lines = []
        for line in lines:
            # simple parsing: package==version
            match = re.match(r"^([a-zA-Z0-9_\-]+)==(.+)$", line.strip())
            if match:
                pkg = match.group(1)
                latest = get_latest_pypi_version(pkg)
                if latest:
                    new_lines.append(f"{pkg}=={latest}\n")
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        with open(req_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

    # Update package.json
    pkg_path = os.path.join(repo_path, "package.json")
    if os.path.exists(pkg_path):
        with open(pkg_path, "r", encoding="utf-8") as f:
            try:
                pkg_data = json.load(f)
            except json.JSONDecodeError:
                pkg_data = None
        
        if pkg_data:
            updated = False
            for section in ["dependencies", "devDependencies"]:
                if section in pkg_data:
                    for pkg in pkg_data[section]:
                        latest = get_latest_npm_version(pkg)
                        if latest:
                            prefix = ""
                            if pkg_data[section][pkg].startswith("^"):
                                prefix = "^"
                            elif pkg_data[section][pkg].startswith("~"):
                                prefix = "~"
                            
                            new_val = f"{prefix}{latest}"
                            if pkg_data[section][pkg] != new_val:
                                pkg_data[section][pkg] = new_val
                                updated = True
            
            if updated:
                with open(pkg_path, "w", encoding="utf-8") as f:
                    json.dump(pkg_data, f, indent=2)
                    f.write("\n")
