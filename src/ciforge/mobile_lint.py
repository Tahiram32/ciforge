"""Mobile config linter for ciforge."""

import os
import re
from typing import List
from .scanner import Finding


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_text(path: str) -> str:
    """Read a file and return its contents, or empty string on error."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except OSError:
        return ""


def _analyze_pubspec(path: str) -> List[Finding]:
    """Check pubspec.yaml for common Flutter/Dart issues."""
    findings: List[Finding] = []
    content = _read_text(path)
    if not content:
        return findings

    # Check for `version:` field
    if not re.search(r"^\s*version\s*:", content, re.MULTILINE):
        findings.append(
            Finding(
                file=path,
                line=0,
                message="pubspec.yaml is missing the 'version:' field",
                severity="high",
            )
        )

    # Check for `sdk: flutter` inside an `environment:` section
    # We look for an environment block and then `sdk: flutter` nearby
    env_match = re.search(
        r"^\s*environment\s*:", content, re.MULTILINE
    )
    if env_match:
        # Look for `sdk: flutter` anywhere after the environment key in the block
        after_env = content[env_match.start():]
        if not re.search(r"sdk\s*:\s*flutter", after_env):
            findings.append(
                Finding(
                    file=path,
                    line=0,
                    message="pubspec.yaml environment section is missing 'sdk: flutter'",
                    severity="medium",
                )
            )
    else:
        findings.append(
            Finding(
                file=path,
                line=0,
                message="pubspec.yaml environment section is missing 'sdk: flutter'",
                severity="medium",
            )
        )

    return findings


def _analyze_gradle(path: str) -> List[Finding]:
    """Check build.gradle for required Android config fields."""
    findings: List[Finding] = []
    content = _read_text(path)
    if not content:
        return findings

    if not re.search(r"minSdkVersion", content):
        findings.append(
            Finding(
                file=path,
                line=0,
                message=f"{path}: 'minSdkVersion' is not set",
                severity="medium",
            )
        )

    if not re.search(r"targetSdkVersion", content):
        findings.append(
            Finding(
                file=path,
                line=0,
                message=f"{path}: 'targetSdkVersion' is not set",
                severity="medium",
            )
        )

    if not re.search(r"versionCode", content):
        findings.append(
            Finding(
                file=path,
                line=0,
                message=f"{path}: 'versionCode' is not set",
                severity="high",
            )
        )

    return findings


def _analyze_podfile(path: str) -> List[Finding]:
    """Check Podfile for required iOS config."""
    findings: List[Finding] = []
    content = _read_text(path)
    if not content:
        return findings

    if not re.search(r"platform\s+:ios", content):
        findings.append(
            Finding(
                file=path,
                line=0,
                message="Podfile is missing 'platform :ios' specification",
                severity="medium",
            )
        )

    if "use_frameworks!" not in content:
        findings.append(
            Finding(
                file=path,
                line=0,
                message="Podfile is missing 'use_frameworks!'",
                severity="low",
            )
        )

    return findings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze() -> List[Finding]:
    """Analyze mobile config files in the current directory.

    Checks pubspec.yaml (Flutter), build.gradle / app/build.gradle (Android),
    and Podfile (iOS).  Returns a list of Findings.
    """
    findings: List[Finding] = []

    # Flutter / Dart
    if os.path.exists("pubspec.yaml"):
        findings.extend(_analyze_pubspec("pubspec.yaml"))

    # Android Gradle
    for gradle_path in ("build.gradle", os.path.join("app", "build.gradle")):
        if os.path.exists(gradle_path):
            findings.extend(_analyze_gradle(gradle_path))

    # iOS Podfile
    if os.path.exists("Podfile"):
        findings.extend(_analyze_podfile("Podfile"))

    return findings
