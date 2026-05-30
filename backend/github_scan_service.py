"""GitHub PR scan service for SecBrief."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

from llm_service import audit_code, explain_alert


def _parse_package_lock(content: str) -> list[dict[str, str]]:
    """Parse package-lock.json to get package names and versions."""
    try:
        data = json.loads(content)
        packages = []
        if "packages" in data:
            for name, pkg in data["packages"].items():
                if name and name != "" and "version" in pkg:
                    packages.append({"name": name.lstrip("node_modules/"), "version": pkg["version"]})
        return packages
    except Exception:
        return []


def _parse_requirements_txt(content: str) -> list[dict[str, str]]:
    """Parse requirements.txt to get package names and versions."""
    packages = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Simple parsing for name==version
        match = re.match(r"^([a-zA-Z0-9_-]+)\s*([=<>~]+)\s*([0-9a-zA-Z.]+)", line)
        if match:
            packages.append({"name": match.group(1), "version": match.group(3)})
    return packages


def _parse_go_sum(content: str) -> list[dict[str, str]]:
    """Parse go.sum to get package names and versions."""
    packages = []
    seen = set()
    for line in content.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2:
            name = parts[0]
            version = parts[1].replace("/go.mod", "")
            key = f"{name}@{version}"
            if key not in seen:
                seen.add(key)
                packages.append({"name": name, "version": version})
    return packages


def _parse_ecosystem_file(filename: str, content: str) -> list[dict[str, str]]:
    """Parse ecosystem file based on filename."""
    name = filename.lower()
    if "package-lock.json" in name:
        return _parse_package_lock(content)
    elif "requirements.txt" in name:
        return _parse_requirements_txt(content)
    elif "go.sum" in name:
        return _parse_go_sum(content)
    return []


def _query_osv(packages: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Query OSV API for vulnerabilities."""
    if not packages:
        return []
    queries = [{"package": {"name": p["name"]}, "version": p["version"]} for p in packages[:100]]
    try:
        r = httpx.post(
            "https://api.osv.dev/v1/querybatch",
            json={"queries": queries},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        findings = []
        for result in data.get("results", []):
            for vuln in result.get("vulns", []):
                findings.append(vuln)
        return findings
    except Exception:
        return []


def _format_pr_comment(overall_severity: str, findings: list[dict[str, Any]]) -> str:
    """Format findings as a GitHub PR comment."""
    emoji_map = {
        "Critical": "🔴",
        "High": "🟠",
        "Medium": "🟡",
        "Low": "🟢",
    }
    emoji = emoji_map.get(overall_severity, "⚪")

    lines = [
        f"# {emoji} SecBrief Security Scan",
        f"**Overall severity:** {overall_severity}",
        f"**Total findings:** {len(findings)}",
        "",
    ]

    for finding in findings:
        sev_emoji = emoji_map.get(finding.get("severity", "Low"), "⚪")
        lines.append(f"## {sev_emoji} {finding.get('title', 'Finding')}")
        if finding.get("file"):
            lines.append(f"**File:** {finding['file']}")
        if finding.get("explanation"):
            lines.append(f"{finding['explanation']}")
        if finding.get("owasp"):
            lines.append(f"**OWASP:** {', '.join(finding['owasp'])}")
        if finding.get("cwe"):
            lines.append(f"**CWE:** {', '.join(finding['cwe'])}")
        if finding.get("soc2"):
            lines.append(f"**SOC 2:** {', '.join(finding['soc2'])}")
        if finding.get("inr_impact"):
            lines.append(f"**Financial impact:** {finding['inr_impact']}")
        if finding.get("fix_summary"):
            lines.append(f"**Fix:** {finding['fix_summary']}")
        lines.append("")

    lines.append("---")
    lines.append("Powered by [SecBrief](https://secbrief.dev)")
    return "\n".join(lines)


def run_github_scan(payload: dict[str, Any]) -> dict[str, Any]:
    """Run a full GitHub PR scan."""
    repo = payload.get("repo", "")
    pr_number = payload.get("pr_number", 0)
    changed_files = payload.get("changed_files", [])
    ecosystem_files = payload.get("ecosystem_files", [])

    findings = []

    # 1. Scan code files
    for file in changed_files:
        filename = file.get("filename", "")
        content = file.get("content", "")
        if not filename or not content:
            continue
        analysis, _ = audit_code(content)
        if analysis and analysis.get("severity") not in ("Low", None):
            vulns = analysis.get("vulnerabilities", [])
            if vulns:
                for v in vulns:
                    owasp = []
                    if analysis.get("owasp_category") and analysis["owasp_category"] != "N/A":
                        owasp = [analysis["owasp_category"].split("-")[0]]
                    cwe = []
                    if analysis.get("cwe_id") and analysis["cwe_id"] != "N/A":
                        cwe = [analysis["cwe_id"]]
                    findings.append({
                        "file": filename,
                        "line": v.get("line_hint"),
                        "severity": v.get("severity", analysis.get("severity", "Medium")),
                        "title": v.get("name", analysis.get("title", "Code finding")),
                        "explanation": analysis.get("summary", ""),
                        "owasp": owasp,
                        "cwe": cwe,
                        "soc2": analysis.get("soc2_controls", []),
                        "inr_impact": analysis.get("financial_impact_inr", ""),
                        "fix_summary": v.get("fix", ""),
                    })
            else:
                owasp = []
                if analysis.get("owasp_category") and analysis["owasp_category"] != "N/A":
                    owasp = [analysis["owasp_category"].split("-")[0]]
                cwe = []
                if analysis.get("cwe_id") and analysis["cwe_id"] != "N/A":
                    cwe = [analysis["cwe_id"]]
                findings.append({
                    "file": filename,
                    "line": None,
                    "severity": analysis.get("severity", "Medium"),
                    "title": analysis.get("title", "Code finding"),
                    "explanation": analysis.get("summary", ""),
                    "owasp": owasp,
                    "cwe": cwe,
                    "soc2": analysis.get("soc2_controls", []),
                    "inr_impact": analysis.get("financial_impact_inr", ""),
                    "fix_summary": analysis.get("what_to_do", ["Review and fix"])[0] if analysis.get("what_to_do") else "Review and fix",
                })

    # 2. Scan ecosystem files (dependencies)
    all_packages = []
    for file in ecosystem_files:
        filename = file.get("filename", "")
        content = file.get("content", "")
        if not filename or not content:
            continue
        packages = _parse_ecosystem_file(filename, content)
        all_packages.extend(packages)

    osv_findings = _query_osv(all_packages)
    for vuln in osv_findings:
        vuln_id = vuln.get("id", "CVE")
        summary = vuln.get("summary", "Vulnerability found")
        severity = "Medium"
        for severity_obj in vuln.get("severity", []):
            if severity_obj.get("type") == "CVSS_V3":
                score = float(severity_obj.get("score", 5.0))
                if score >= 9.0:
                    severity = "Critical"
                elif score >= 7.0:
                    severity = "High"
                elif score >= 4.0:
                    severity = "Medium"
                else:
                    severity = "Low"
        # Get explanation from LLM
        alert_text = f"{vuln_id}: {summary}"
        analysis, _ = explain_alert(alert_text)
        owasp = []
        if analysis.get("owasp_category") and analysis["owasp_category"] != "N/A":
            owasp = [analysis["owasp_category"].split("-")[0]]
        cwe = []
        if analysis.get("cwe_id") and analysis["cwe_id"] != "N/A":
            cwe = [analysis["cwe_id"]]
        findings.append({
            "file": None,
            "line": None,
            "severity": severity,
            "title": f"{vuln_id}: {summary[:80]}...",
            "explanation": analysis.get("summary", summary),
            "owasp": owasp,
            "cwe": cwe,
            "soc2": analysis.get("soc2_controls", []),
            "inr_impact": analysis.get("financial_impact_inr", ""),
            "fix_summary": analysis.get("what_to_do", ["Update dependency"])[0] if analysis.get("what_to_do") else "Update dependency",
        })

    # Calculate overall severity
    overall_severity = "Low"
    severities = [f.get("severity", "Low") for f in findings]
    if "Critical" in severities:
        overall_severity = "Critical"
    elif "High" in severities:
        overall_severity = "High"
    elif "Medium" in severities:
        overall_severity = "Medium"

    pr_comment = _format_pr_comment(overall_severity, findings)

    return {
        "overall_severity": overall_severity,
        "total_findings": len(findings),
        "findings": findings,
        "pr_comment": pr_comment,
    }
