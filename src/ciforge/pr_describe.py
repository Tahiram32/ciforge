"""Auto PR description generator for ciforge."""

import json
import os
import urllib.request
import urllib.error
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_OPENAI_URL = "https://api.openai.com/v1/chat/completions"
_ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

_FALLBACK_TEMPLATE = """\
## Summary

<!-- Describe the purpose of this PR -->

## Changes

<!-- List the key changes made -->

## Testing

<!-- Describe how the changes were tested -->
"""

_PROMPT_SYSTEM = (
    "You are a helpful assistant that writes clear, concise GitHub pull request "
    "descriptions in markdown. Always include these exact sections: "
    "## Summary, ## Changes, ## Testing."
)

_PROMPT_USER_TMPL = (
    "Please write a GitHub PR description for the following diff.\n\n"
    "```diff\n{diff}\n```\n\n"
    "Return only the markdown description with sections: ## Summary, ## Changes, ## Testing."
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_config() -> tuple:
    """Return (provider, api_key, model)."""
    provider = os.environ.get("CIFORGE_AI_PROVIDER", "openai").lower()
    api_key = os.environ.get("CIFORGE_AI_KEY") or os.environ.get("OPENAI_API_KEY", "")
    model = os.environ.get("CIFORGE_AI_MODEL", "gpt-4o-mini")
    return provider, api_key, model


def _post_openai(diff_text: str, api_key: str, model: str) -> Optional[str]:
    """Call OpenAI chat completions API and return the response text."""
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": _PROMPT_SYSTEM},
            {"role": "user", "content": _PROMPT_USER_TMPL.format(diff=diff_text)},
        ],
    }).encode("utf-8")

    req = urllib.request.Request(
        _OPENAI_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"]
    except Exception:
        return None


def _post_anthropic(diff_text: str, api_key: str, model: str) -> Optional[str]:
    """Call Anthropic messages API and return the response text."""
    payload = json.dumps({
        "model": model,
        "max_tokens": 1024,
        "system": _PROMPT_SYSTEM,
        "messages": [
            {"role": "user", "content": _PROMPT_USER_TMPL.format(diff=diff_text)},
        ],
    }).encode("utf-8")

    req = urllib.request.Request(
        _ANTHROPIC_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body["content"][0]["text"]
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate(diff_text: str) -> str:
    """Generate a GitHub PR description for the given diff.

    Uses the AI provider configured via environment variables.
    Falls back to a markdown template if no key is available or the request fails.
    """
    provider, api_key, model = _get_config()

    if not api_key:
        return _FALLBACK_TEMPLATE

    result: Optional[str] = None

    if provider == "anthropic":
        result = _post_anthropic(diff_text, api_key, model)
    else:
        # Default: openai
        result = _post_openai(diff_text, api_key, model)

    if result:
        return result

    return _FALLBACK_TEMPLATE


def post_pr_description(pr_number: int, repo: str, token: str, description: str) -> None:
    """Patch a GitHub PR's body via the GitHub REST API.

    Args:
        pr_number: The pull-request number (e.g. 42).
        repo: The repository in ``owner/name`` format (e.g. ``octocat/hello``).
        token: A GitHub personal access token with ``repo`` scope.
        description: The markdown string to set as the PR body.
    """
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    payload = json.dumps({"body": description}).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="PATCH",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status in (200, 201):
                print(f"PR #{pr_number} description updated successfully.")
            else:
                print(f"Warning: GitHub API returned status {resp.status}.")
    except Exception as exc:
        print(f"Warning: Failed to update PR description: {exc}")
