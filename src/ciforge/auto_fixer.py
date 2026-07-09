import os
import json
import urllib.request
import subprocess
import time
from typing import List
from .scanner import Finding

_FIX_PROMPT = (
    "You are an expert developer. I will provide a list of code findings/issues "
    "and the current code. Provide the fixed full file content for each file. "
    "Return ONLY a valid JSON array of objects with keys 'file' and 'content'."
)

def call_llm_for_fixes(findings: List[Finding]) -> list:
    files_to_fix = list(set(f.file for f in findings if f.file and os.path.exists(f.file)))
    if not files_to_fix:
        return []
        
    context = "Findings:\n"
    for f in findings:
        context += f"- {f.file}:{f.line}: {f.message}\n"
        
    context += "\nFiles:\n"
    for file_path in files_to_fix:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                context += f"--- {file_path} ---\n{f.read()}\n\n"
        except Exception:
            pass

    provider = os.environ.get("CIFORGE_AI_PROVIDER", "openai").lower()
    model = os.environ.get("CIFORGE_AI_MODEL", "")
    api_key = os.environ.get("CIFORGE_AI_KEY") or os.environ.get("OPENAI_API_KEY", "")
    
    if not api_key:
        return []
        
    body_dict = {
        "model": model or "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": _FIX_PROMPT},
            {"role": "user", "content": context},
        ],
    }
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    
    if provider == "anthropic":
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }
        body_dict = {
            "model": model or "claude-3-haiku-20240307",
            "max_tokens": 4096,
            "system": _FIX_PROMPT,
            "messages": [{"role": "user", "content": context}],
        }
        
    body = json.dumps(body_dict).encode("utf-8")
    
    try:
        req = urllib.request.Request(url, data=body, headers=headers)
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if provider == "anthropic":
                content = result["content"][0]["text"]
            else:
                content = result["choices"][0]["message"]["content"]
                
            start = content.find("[")
            end = content.rfind("]")
            if start != -1 and end != -1:
                return json.loads(content[start:end+1])
    except Exception:
        pass
        
    return []

def run_agentic_fixes(findings: List[Finding], repo_path: str):
    if not findings:
        return
        
    orig_dir = os.getcwd()
    os.chdir(repo_path)
    try:
        fixes = call_llm_for_fixes(findings)
        if not fixes:
            return
            
        timestamp = int(time.time())
        branch_name = f"ciforge-autofix-{timestamp}"
        
        subprocess.run(["git", "checkout", "-b", branch_name], check=True, capture_output=True)
        
        for fix in fixes:
            file_path = fix.get("file")
            content = fix.get("content")
            if file_path and content and os.path.exists(file_path):
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                subprocess.run(["git", "add", file_path], check=True, capture_output=True)
                
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            return
            
        subprocess.run(["git", "commit", "-m", "Auto-fix issues found by CIForge"], check=True, capture_output=True)
        
        # Determine remote branch
        subprocess.run(["git", "push", "origin", branch_name], check=True, capture_output=True)
        
        gh_token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not gh_token:
            return
            
        remote_url = subprocess.run(["git", "config", "--get", "remote.origin.url"], capture_output=True, text=True).stdout.strip()
        if "github.com" in remote_url:
            parts = remote_url.split("github.com")[-1].strip(":/").replace(".git", "").split("/")
            if len(parts) >= 2:
                owner, repo = parts[-2], parts[-1]
                pr_data = {
                    "title": "Auto-fix issues found by CIForge",
                    "body": "Automated PR created by CIForge agentic fixer.",
                    "head": branch_name,
                    "base": "main"
                }
                req = urllib.request.Request(
                    f"https://api.github.com/repos/{owner}/{repo}/pulls",
                    data=json.dumps(pr_data).encode("utf-8"),
                    headers={
                        "Authorization": f"token {gh_token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                )
                try:
                    urllib.request.urlopen(req)
                except Exception:
                    pass
    except Exception:
        pass
    finally:
        os.chdir(orig_dir)
