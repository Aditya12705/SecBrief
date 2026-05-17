"""Deep scan enrichment — security files + signals beyond root manifests."""

from __future__ import annotations

import re
from typing import Any

import httpx

from github_service import _fetch_file, _get, _headers, parse_github_url

SECURITY_PATHS = [
    ".github/workflows/ci.yml",
    ".github/workflows/security.yml",
    ".github/dependabot.yml",
    "docker-compose.yml",
    ".env.example",
    "SECURITY.md",
    "trivy.yaml",
    ".trivyignore",
]

SECRET_PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "aws-key", "Possible AWS access key in repo"),
    (r"ghp_[a-zA-Z0-9]{20,}", "github-token", "Possible GitHub token in repo"),
    (r"sk-[a-zA-Z0-9]{20,}", "openai-key", "Possible API key in repo"),
    (r"BEGIN (RSA |EC )?PRIVATE KEY", "private-key", "Private key material in repo"),
]


def deep_scan_repository(url: str) -> dict[str, Any]:
    """Extend github scan with security paths and secret-pattern signals."""
    owner, repo = parse_github_url(url)
    extra_manifests: dict[str, str] = {}
    deep_findings: list[dict[str, str]] = []

    with httpx.Client() as client:
        for path in SECURITY_PATHS:
            content = _fetch_file(client, owner, repo, path)
            if content:
                extra_manifests[path] = content
                deep_findings.append(
                    {
                        "signal": path,
                        "note": f"Found {path} — included in posture analysis",
                        "severity": "info",
                    }
                )
        for pattern, signal, note in SECRET_PATTERNS:
            for path, body in extra_manifests.items():
                if re.search(pattern, body):
                    deep_findings.append({"signal": signal, "note": note, "severity": "high"})

        # Recent security-related issues (public)
        issues = _get(client, f"/repos/{owner}/{repo}/issues?state=open&per_page=5&labels=security")
        if isinstance(issues, list) and issues:
            deep_findings.append(
                {
                    "signal": "open-security-issues",
                    "note": f"{len(issues)} open issue(s) with security label",
                    "severity": "medium",
                }
            )

    return {
        "extra_manifests": extra_manifests,
        "deep_findings": deep_findings[:15],
        "scan_depth": "deep",
    }


def merge_deep_into_scan(base_scan: dict[str, Any], deep: dict[str, Any]) -> dict[str, Any]:
    """Merge deep scan results into base github scan payload."""
    extra = deep.get("extra_manifests", {})
    context = base_scan.get("scan_context", "")
    if extra:
        context += "\n\n=== Deep scan (security files) ===\n"
        for path, body in extra.items():
            context += f"\n--- {path} ---\n{body[:4000]}\n"
    findings = list(base_scan.get("heuristic_findings", []))
    findings.extend(deep.get("deep_findings", []))
    return {
        **base_scan,
        "heuristic_findings": findings[:20],
        "scan_context": context,
        "deep_scan": True,
        "manifests_found": list(set(base_scan.get("manifests_found", []) + list(extra.keys()))),
    }
