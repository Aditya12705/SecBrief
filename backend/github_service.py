"""GitHub repository intake — public repos via GitHub REST API."""

from __future__ import annotations

import os
import re
from typing import Any
import httpx

# Curated public repos for hackathon demos (varied stacks)
DEMO_REPOS: list[dict[str, str]] = [
    {
        "url": "https://github.com/expressjs/express",
        "label": "Express.js",
        "stack": "Node.js",
        "why": "Popular API framework — classic dependency surface",
    },
    {
        "url": "https://github.com/pallets/flask",
        "label": "Flask",
        "stack": "Python",
        "why": "Lightweight Python web — requirements.txt analysis",
    },
    {
        "url": "https://github.com/django/django",
        "label": "Django",
        "stack": "Python",
        "why": "Enterprise Python web — extensive security features",
    },
    {
        "url": "https://github.com/vitejs/vite",
        "label": "Vite",
        "stack": "JavaScript",
        "why": "Modern frontend tooling — package.json + lockfiles",
    },
    {
        "url": "https://github.com/fastapi/fastapi",
        "label": "FastAPI",
        "stack": "Python",
        "why": "API framework — pyproject & security headers",
    },
    {
        "url": "https://github.com/vercel/next.js",
        "label": "Next.js",
        "stack": "React",
        "why": "Full-stack React — large dependency tree",
    },
    {
        "url": "https://github.com/gin-gonic/gin",
        "label": "Gin",
        "stack": "Go",
        "why": "High-performance Go web — go.mod analysis",
    },
    {
        "url": "https://github.com/rails/rails",
        "label": "Ruby on Rails",
        "stack": "Ruby",
        "why": "The OG web framework — Gemfile & secret_key_base",
    },
    {
        "url": "https://github.com/spring-projects/spring-boot",
        "label": "Spring Boot",
        "stack": "Java",
        "why": "Enterprise Java — pom.xml & Log4j context",
    },
    {
        "url": "https://github.com/rust-lang/rust",
        "label": "Rust",
        "stack": "Rust",
        "why": "Memory safe systems language — Cargo.toml scan",
    },
]

MANIFEST_FILES = [
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "requirements.txt",
    "Pipfile",
    "pyproject.toml",
    "go.mod",
    "Cargo.toml",
    "Gemfile",
    "composer.json",
    "pom.xml",
    "build.gradle",
    "Dockerfile",
    ".github/dependabot.yml",
]

RISKY_PATTERNS = [
    (r"\blodash\b", "lodash", "Check version — historic prototype pollution CVEs"),
    (r"\baxios\b", "axios", "HTTP client — review SSRF and version advisories"),
    (r"\bminimist\b", "minimist", "CLI parser — past prototype pollution issues"),
    (r"\bjsonwebtoken\b", "jsonwebtoken", "JWT lib — algorithm confusion if misconfigured"),
    (r"\bexpress\b", "express", "Ensure body-parser limits and security headers"),
    (r"\brequests\b", "requests", "Python HTTP — pin versions for CVE fixes"),
    (r"\bpillow\b", "pillow", "Image lib — frequent security patches"),
    (r"\bcryptography\b", "cryptography", "Keep updated — OpenSSL bindings"),
    (r"\bopenssl\b", "openssl", "Crypto — version-critical"),
    (r"eval\(", "eval()", "Dangerous pattern in source"),
    (r"exec\(", "exec()", "Dangerous pattern in source"),
    (r"password\s*=\s*['\"][^'\"]+['\"]", "hardcoded-secret", "Possible hardcoded credential"),
]


def parse_github_url(url: str) -> tuple[str, str]:
    url = url.strip().rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    # github.com/owner/repo
    m = re.match(r"(?:https?://)?(?:www\.)?github\.com/([^/]+)/([^/#?]+)", url, re.I)
    if m:
        return m.group(1), m.group(2)
    # owner/repo shorthand
    m = re.match(r"^([^/]+)/([^/]+)$", url)
    if m:
        return m.group(1), m.group(2)
    raise ValueError("Invalid GitHub URL. Use https://github.com/owner/repo or owner/repo")


def _headers() -> dict[str, str]:
    h = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "SecBrief-Security-Agent",
    }
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _get(client: httpx.Client, path: str) -> Any:
    r = client.get(f"https://api.github.com{path}", headers=_headers(), timeout=30.0)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def _fetch_file(client: httpx.Client, owner: str, repo: str, path: str) -> str | None:
    data = _get(client, f"/repos/{owner}/{repo}/contents/{path}")
    if not data or data.get("encoding") != "base64":
        return None
    import base64

    try:
        raw = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        return raw[:50000]
    except Exception:
        return None


def _heuristic_findings(manifests: dict[str, str]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    combined = "\n".join(manifests.values())
    for pattern, name, note in RISKY_PATTERNS:
        if re.search(pattern, combined, re.I):
            findings.append({"signal": name, "note": note, "severity": "medium"})
    if "dependabot" in combined.lower():
        findings.append(
            {
                "signal": "dependabot",
                "note": "Dependabot configured — good baseline, still verify open alerts",
                "severity": "info",
            }
        )
    if not manifests:
        findings.append(
            {
                "signal": "no-manifest",
                "note": "No standard manifest found at repo root — scan may be incomplete",
                "severity": "low",
            }
        )
    return findings[:12]


def scan_repository(url: str) -> dict[str, Any]:
    owner, repo = parse_github_url(url)
    with httpx.Client() as client:
        meta = _get(client, f"/repos/{owner}/{repo}")
        if not meta:
            raise ValueError(f"Repository not found: {owner}/{repo}")

        manifests: dict[str, str] = {}
        for path in MANIFEST_FILES:
            content = _fetch_file(client, owner, repo, path)
            if content:
                manifests[path] = content

        default_branch = meta.get("default_branch", "main")
        readme = _fetch_file(client, owner, repo, "README.md")

    findings = _heuristic_findings(manifests)
    context_parts = [
        f"Repository: {owner}/{repo}",
        f"Description: {meta.get('description') or 'N/A'}",
        f"Language: {meta.get('language') or 'Unknown'}",
        f"Stars: {meta.get('stargazers_count', 0)} | Default branch: {default_branch}",
        f"URL: {meta.get('html_url')}",
        "",
        "=== Manifest files ===",
    ]
    for path, body in manifests.items():
        context_parts.append(f"\n--- {path} ---\n{body[:8000]}")
    if readme:
        context_parts.append(f"\n--- README (excerpt) ---\n{readme[:3000]}")
    if findings:
        context_parts.append("\n=== Heuristic signals ===")
        for f in findings:
            context_parts.append(f"- [{f['severity']}] {f['signal']}: {f['note']}")

    return {
        "owner": owner,
        "repo": repo,
        "full_name": f"{owner}/{repo}",
        "html_url": meta.get("html_url"),
        "description": meta.get("description"),
        "language": meta.get("language"),
        "stars": meta.get("stargazers_count", 0),
        "default_branch": default_branch,
        "manifests_found": list(manifests.keys()),
        "heuristic_findings": findings,
        "scan_context": "\n".join(context_parts),
    }


def list_demo_repos() -> list[dict[str, str]]:
    return DEMO_REPOS
