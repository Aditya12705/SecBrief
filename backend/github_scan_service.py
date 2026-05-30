"""GitHub PR scan service for SecBrief."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

from llm_service import audit_code, explain_alert

_PLATFORM_URL = "https://adi576-secbrief.hf.space"


def _normalize_severity(value: Any) -> str:
    v = str(value or "").strip().lower()
    if v == "critical":
        return "Critical"
    if v == "high":
        return "High"
    if v == "medium":
        return "Medium"
    if v == "low":
        return "Low"
    return "Low"


def _severity_rank(severity: str) -> int:
    s = _normalize_severity(severity).lower()
    return {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(s, 0)


def _parse_risk_score(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except Exception:
        return None


def _severity_from_risk_score(score: float | None) -> str | None:
    if score is None:
        return None
    if score >= 9:
        return "Critical"
    if score >= 7:
        return "High"
    if score >= 4:
        return "Medium"
    return "Low"



def _extract_owasp(value: Any) -> list[str]:
    if not value:
        return []
    text = str(value).strip()
    if not text or text.upper() == "N/A":
        return []
    match = re.search(r"(A\d{2}:2021)", text)
    if match:
        return [match.group(1)]
    head = text.split("-", 1)[0].strip()
    return [head] if head else []


def _extract_cwe(value: Any) -> list[str]:
    if not value:
        return []
    text = str(value).strip()
    if not text or text.upper() == "N/A":
        return []
    match = re.search(r"(CWE-\d+)", text, re.I)
    if match:
        return [match.group(1).upper()]
    return [text]


def _first_str(value: Any) -> str:
    if isinstance(value, list) and value:
        if isinstance(value[0], str):
            return value[0]
    if isinstance(value, str):
        return value
    return ""


def _parse_package_lock(content: str) -> list[dict[str, str]]:
    try:
        data = json.loads(content)
    except Exception:
        return []

    packages: list[dict[str, str]] = []
    pkgs = data.get("packages")
    if isinstance(pkgs, dict):
        for path, meta in pkgs.items():
            if not isinstance(meta, dict):
                continue
            version = meta.get("version")
            if not version:
                continue
            name = str(path or "")
            name = name.removeprefix("node_modules/")
            if not name:
                continue
            packages.append({"name": name, "version": str(version)})
    return packages


def _parse_requirements_txt(content: str) -> list[dict[str, str]]:
    packages: list[dict[str, str]] = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^([a-zA-Z0-9_.-]+)\s*([=<>~!]+)\s*([0-9a-zA-Z.]+)", line)
        if match:
            packages.append({"name": match.group(1), "version": match.group(3)})
    return packages


def _parse_go_sum(content: str) -> list[dict[str, str]]:
    packages: list[dict[str, str]] = []
    seen: set[str] = set()
    for line in content.splitlines():
        parts = line.strip().split()
        if len(parts) < 2:
            continue
        name = parts[0]
        version = parts[1].replace("/go.mod", "")
        key = f"{name}@{version}"
        if key in seen:
            continue
        seen.add(key)
        packages.append({"name": name, "version": version})
    return packages


def _parse_ecosystem_file(filename: str, content: str) -> list[dict[str, str]]:
    name = filename.lower()
    if name.endswith("package-lock.json"):
        return _parse_package_lock(content)
    if name.endswith("requirements.txt"):
        return _parse_requirements_txt(content)
    if name.endswith("go.sum"):
        return _parse_go_sum(content)
    return []


def _query_osv(packages: list[dict[str, str]]) -> list[dict[str, Any]]:
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
    except Exception:
        return []

    vulns: list[dict[str, Any]] = []
    for result in data.get("results", []) if isinstance(data, dict) else []:
        for vuln in result.get("vulns", []) if isinstance(result, dict) else []:
            if isinstance(vuln, dict):
                vulns.append(vuln)
    return vulns


def _severity_emoji(severity: str) -> str:
    return {
        "Critical": "🔴",
        "High": "🟠",
        "Medium": "🟡",
        "Low": "🟢",
    }.get(_normalize_severity(severity), "⚪")


def _format_pr_comment(overall_severity: str, findings: list[dict[str, Any]]) -> str:
    overall = _normalize_severity(overall_severity)
    lines: list[str] = [
        f"# {_severity_emoji(overall)} SecBrief Security Scan",
        f"**Overall severity:** {_severity_emoji(overall)} {overall}",
        f"**Total findings:** {len(findings)}",
        "",
    ]

    for f in findings:
        sev = _normalize_severity(f.get("severity"))
        title = str(f.get("title") or "Security finding")
        file_name = str(f.get("file") or "(dependencies)")
        explanation = str(f.get("explanation") or "").strip()
        fix_summary = str(f.get("fix_summary") or "").strip()

        lines.append(f"## {_severity_emoji(sev)} {title}")
        lines.append(f"**File:** {file_name}")
        if explanation:
            lines.append("")
            lines.append(explanation)
        tags: list[str] = []
        owasp = f.get("owasp") or []
        cwe = f.get("cwe") or []
        if isinstance(owasp, list) and owasp:
            tags.append(f"**OWASP:** {', '.join(str(x) for x in owasp)}")
        if isinstance(cwe, list) and cwe:
            tags.append(f"**CWE:** {', '.join(str(x) for x in cwe)}")
        if tags:
            lines.append("")
            lines.extend(tags)
        if fix_summary:
            lines.append("")
            lines.append(f"**Fix summary:** {fix_summary}")
        lines.append("")

    lines.append("---")
    lines.append(f"Powered by [SecBrief]({_PLATFORM_URL})")
    return "\n".join(lines)


def run_github_scan(payload: dict[str, Any]) -> dict[str, Any]:
    changed_files = payload.get("changed_files") or []
    ecosystem_files = payload.get("ecosystem_files") or []

    findings: list[dict[str, Any]] = []

    for entry in changed_files:
        if not isinstance(entry, dict):
            continue
        filename = str(entry.get("filename") or "").strip()
        content = str(entry.get("content") or "")
        if not filename or not content.strip():
            continue

        analysis, _ = audit_code(content)
        a = analysis if isinstance(analysis, dict) else {}
        if not a:
            continue

        risk_score = _parse_risk_score(a.get("risk_score"))
        sev = _normalize_severity(a.get("severity"))
        sev_from_risk = _severity_from_risk_score(risk_score)
        if sev_from_risk and _severity_rank(sev_from_risk) > _severity_rank(sev):
            sev = sev_from_risk

        owasp = _extract_owasp(a.get("owasp_category") or a.get("owasp"))
        cwe = _extract_cwe(a.get("cwe_id") or a.get("cwe"))

        base_explanation = str(a.get("summary") or a.get("what_happened") or "").strip()
        if not base_explanation:
            base_explanation = str(a.get("formatted") or "").strip()

        base_fix = _first_str(a.get("what_to_do")) or ""

        vulns: Any = a.get("vulnerabilities")
        if not isinstance(vulns, list) or not vulns:
            for alt in ("findings", "issues"):
                cand = a.get(alt)
                if isinstance(cand, list) and cand:
                    vulns = cand
                    break

        if isinstance(vulns, list) and vulns:
            for v in vulns:
                if not isinstance(v, dict):
                    continue
                v_sev = _normalize_severity(v.get("severity") or sev)
                title = str(v.get("name") or a.get("title") or "Security finding")
                explanation = str(v.get("explanation") or "").strip() or base_explanation
                fix_summary = str(v.get("fix") or "").strip() or base_fix or "Review and fix"
                findings.append(
                    {
                        "file": filename,
                        "line": v.get("line_hint"),
                        "severity": v_sev,
                        "title": title,
                        "explanation": explanation,
                        "owasp": owasp,
                        "cwe": cwe,
                        "soc2": a.get("soc2_controls", []) if isinstance(a.get("soc2_controls", []), list) else [],
                        "inr_impact": str(a.get("financial_impact_inr") or ""),
                        "fix_summary": fix_summary,
                    }
                )
        else:
            should_emit = False
            if _severity_rank(sev) > _severity_rank("Low"):
                should_emit = True
            if owasp or cwe:
                should_emit = True
            if risk_score is not None and risk_score > 3:
                should_emit = True
                if _severity_rank(sev) < _severity_rank("Medium"):
                    sev = "Medium"

            if should_emit:
                findings.append(
                    {
                        "file": filename,
                        "line": None,
                        "severity": sev,
                        "title": str(a.get("title") or "Security finding"),
                        "explanation": base_explanation,
                        "owasp": owasp,
                        "cwe": cwe,
                        "soc2": a.get("soc2_controls", []) if isinstance(a.get("soc2_controls", []), list) else [],
                        "inr_impact": str(a.get("financial_impact_inr") or ""),
                        "fix_summary": base_fix or "Review and fix",
                    }
                )

    all_packages: list[dict[str, str]] = []
    for entry in ecosystem_files:
        if not isinstance(entry, dict):
            continue
        filename = str(entry.get("filename") or "").strip()
        content = str(entry.get("content") or "")
        if not filename or not content.strip():
            continue
        all_packages.extend(_parse_ecosystem_file(filename, content))

    for vuln in _query_osv(all_packages):
        if not isinstance(vuln, dict):
            continue
        vuln_id = str(vuln.get("id") or "OSV")
        summary = str(vuln.get("summary") or "Vulnerability found").strip()

        dep_sev = "Medium"
        for entry in vuln.get("severity", []) if isinstance(vuln.get("severity"), list) else []:
            if not isinstance(entry, dict):
                continue
            if entry.get("type") != "CVSS_V3":
                continue
            try:
                score = float(entry.get("score", 5.0))
            except Exception:
                score = 5.0
            dep_sev = _normalize_severity(_severity_from_risk_score(score) or "Medium")
            break

        dep_analysis, _ = explain_alert(f"{vuln_id}: {summary}")
        dep_a = dep_analysis if isinstance(dep_analysis, dict) else {}
        owasp = _extract_owasp(dep_a.get("owasp_category") or dep_a.get("owasp"))
        cwe = _extract_cwe(dep_a.get("cwe_id") or dep_a.get("cwe"))
        explanation = str(dep_a.get("summary") or "").strip() or summary
        fix_summary = _first_str(dep_a.get("what_to_do")) or "Update dependency"

        findings.append(
            {
                "file": "(dependencies)",
                "line": None,
                "severity": dep_sev,
                "title": f"{vuln_id}: {summary}",
                "explanation": explanation,
                "owasp": owasp,
                "cwe": cwe,
                "soc2": dep_a.get("soc2_controls", []) if isinstance(dep_a.get("soc2_controls", []), list) else [],
                "inr_impact": str(dep_a.get("financial_impact_inr") or ""),
                "fix_summary": fix_summary,
            }
        )

    overall = "Low"
    for f in findings:
        f_sev = _normalize_severity(f.get("severity"))
        if _severity_rank(f_sev) > _severity_rank(overall):
            overall = f_sev

    return {
        "overall_severity": overall,
        "total_findings": len(findings),
        "findings": findings,
        "pr_comment": _format_pr_comment(overall, findings),
    }
