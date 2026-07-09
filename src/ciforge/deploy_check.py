"""Deployment health check module for ciforge."""

import time
import urllib.request
import urllib.error
from typing import List
from .scanner import Finding


def check(url: str, retries: int = 3, timeout: int = 10) -> List[Finding]:
    """Perform a deployment health check by GETting the given URL.

    Retries up to `retries` times with a 2-second sleep between attempts.
    Returns an empty list if the endpoint responds with HTTP 200.
    Returns a critical Finding otherwise.
    """
    last_error: str = ""

    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                status = response.status
                if status == 200:
                    return []
                last_error = (
                    f"Deployment health check failed: {url} returned {status}"
                )
        except (urllib.error.URLError, OSError, Exception):
            last_error = (
                f"Deployment health check failed: could not reach {url}"
            )

        if attempt < retries - 1:
            time.sleep(2)

    return [
        Finding(
            file=url,
            line=0,
            message=last_error,
            severity="critical",
        )
    ]
