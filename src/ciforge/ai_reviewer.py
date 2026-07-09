import os
import json
import urllib.request
from typing import List
from .scanner import Finding, git_changed_files, git_diff

def analyze() -> List[Finding]:
    api_key = os.environ.get("CIFORGE_AI_KEY")
    if not api_key:
        return []

    files = git_changed_files()
    diffs = []
    for f in files:
        diff_text = git_diff(f)
        if diff_text:
            diffs.append(f"File: {f}\n{diff_text}")
    
    if not diffs:
        return []

    full_diff = "\n\n".join(diffs)
    
    # We don't want to send huge diffs to API, but for this mock/simple implementation we do.
    prompt = "Review the following code diff and identify logic flaws or missing edge cases. Provide a brief summary.\n\n" + full_diff

    req_data = json.dumps({
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a code reviewer."},
            {"role": "user", "content": prompt}
        ]
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=req_data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    )

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            summary = result["choices"][0]["message"]["content"]
            return [Finding("AI_Review", 0, f"AI Reviewer: {summary}", "medium")]
    except Exception as e:
        return [Finding("AI_Review", 0, f"AI Reviewer failed: {e}", "low")]
