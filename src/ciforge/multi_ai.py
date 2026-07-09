"""Multi-model AI reviewer for ciforge.

Reads CIFORGE_AI_PROVIDER, CIFORGE_AI_MODEL, and CIFORGE_AI_KEY (fallback: OPENAI_API_KEY)
and calls the appropriate provider API to review a code diff.

Supported providers: openai, anthropic, ollama
"""
import os
import json
import urllib.request
from typing import List
from .scanner import Finding

_SYSTEM_PROMPT = (
    "You are a senior code reviewer. Review the following code diff for bugs, "
    "security issues, and code smells. Return ONLY a valid JSON array of objects "
    "with keys 'line' (integer or 0), 'message' (string), and "
    "'severity' (one of: low, medium, high, critical). "
    "If there are no issues, return an empty array []."
)


def _parse_findings(text: str, source: str) -> List[Finding]:
    """Parse a JSON array of issue objects from the model response text."""
    findings: List[Finding] = []
    try:
        start = text.find("[")
        end = text.rfind("]")
        if start == -1 or end == -1:
            return findings
        data = json.loads(text[start : end + 1])
        if not isinstance(data, list):
            return findings
        for item in data:
            if not isinstance(item, dict):
                continue
            line = int(item.get("line", 0))
            message = str(item.get("message", ""))
            severity = str(item.get("severity", "medium"))
            if severity not in ("low", "medium", "high", "critical"):
                severity = "medium"
            if message:
                findings.append(Finding(source, line, f"AI ({source}): {message}", severity))
    except Exception:
        pass
    return findings


def _call_openai(diff_text: str, model: str, api_key: str) -> List[Finding]:
    body = json.dumps({
        "model": model or "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": diff_text},
        ],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            content = result["choices"][0]["message"]["content"]
            return _parse_findings(content, "openai")
    except Exception:
        return []


def _call_anthropic(diff_text: str, model: str, api_key: str) -> List[Finding]:
    body = json.dumps({
        "model": model or "claude-3-haiku-20240307",
        "max_tokens": 1024,
        "system": _SYSTEM_PROMPT,
        "messages": [
            {"role": "user", "content": diff_text},
        ],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            content = result["content"][0]["text"]
            return _parse_findings(content, "anthropic")
    except Exception:
        return []


def _call_ollama(diff_text: str, model: str) -> List[Finding]:
    body = json.dumps({
        "model": model or "llama3",
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": diff_text},
        ],
        "stream": False,
    }).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            content = result["message"]["content"]
            return _parse_findings(content, "ollama")
    except Exception:
        return []


def analyze(diff_text: str) -> List[Finding]:
    """Analyze a diff using the configured AI provider.

    Returns a list of Finding objects. Never raises; returns [] on any error.
    """
    if not diff_text or not diff_text.strip():
        return []

    provider = os.environ.get("CIFORGE_AI_PROVIDER", "openai").lower()
    model = os.environ.get("CIFORGE_AI_MODEL", "")
    api_key = os.environ.get("CIFORGE_AI_KEY") or os.environ.get("OPENAI_API_KEY", "")

    try:
        if provider == "ollama":
            return _call_ollama(diff_text, model)
        elif provider == "anthropic":
            if not api_key:
                return []
            return _call_anthropic(diff_text, model, api_key)
        else:  # default: openai
            if not api_key:
                return []
            return _call_openai(diff_text, model, api_key)
    except Exception:
        return []
