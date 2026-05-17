"""Parse SARIF, npm audit JSON, and other scanner formats into normalized alert text."""

from __future__ import annotations

import json
import re
from typing import Any


def detect_format(text: str, filename: str = "") -> str:
    name = filename.lower()
    stripped = text.strip()
    if name.endswith(".sarif") or name.endswith(".json"):
        if '"runs"' in stripped and '"results"' in stripped:
            return "sarif"
        if '"vulnerabilities"' in stripped or '"metadata"' in stripped and '"vulnerabilities"' in stripped:
            return "npm_audit"
    if stripped.startswith("{"):
        try:
            data = json.loads(stripped)
            if isinstance(data, dict):
                if "runs" in data:
                    return "sarif"
                if "vulnerabilities" in data or data.get("auditReportVersion"):
                    return "npm_audit"
        except json.JSONDecodeError:
            pass
    return "text"


def parse_upload(text: str, filename: str = "") -> dict[str, Any]:
    fmt = detect_format(text, filename)
    if fmt == "sarif":
        return _parse_sarif(text, filename)
    if fmt == "npm_audit":
        return _parse_npm_audit(text, filename)
    return {
        "format": "text",
        "filename": filename,
        "finding_count": 1,
        "alert_text": text.strip(),
        "title": "Uploaded security report",
    }


def _parse_sarif(raw: str, filename: str) -> dict[str, Any]:
    data = json.loads(raw)
    lines: list[str] = ["SARIF security report", "=" * 40, ""]
    count = 0
    for run in data.get("runs", []):
        tool = run.get("tool", {}).get("driver", {})
        tool_name = tool.get("name", "scanner")
        lines.append(f"Tool: {tool_name}")
        for res in run.get("results", [])[:40]:
            count += 1
            rule = res.get("ruleId", "unknown")
            level = res.get("level", "warning")
            msg = res.get("message", {})
            text = msg.get("text") if isinstance(msg, dict) else str(msg)
            locs = res.get("locations", [])
            path = ""
            if locs:
                phys = locs[0].get("physicalLocation", {}).get("artifactLocation", {})
                path = phys.get("uri", "")
            lines.append(f"\n[{count}] {level.upper()} — {rule}")
            if path:
                lines.append(f"  Location: {path}")
            lines.append(f"  {text}")
        lines.append("")
    alert = "\n".join(lines)
    return {
        "format": "sarif",
        "filename": filename,
        "finding_count": count,
        "alert_text": alert,
        "title": f"SARIF report ({count} finding(s))",
    }


def _parse_npm_audit(raw: str, filename: str) -> dict[str, Any]:
    data = json.loads(raw)
    vulns = data.get("vulnerabilities") or {}
    lines = ["npm audit report", "=" * 40, ""]
    count = 0
    for name, v in list(vulns.items())[:50]:
        count += 1
        sev = v.get("severity", "unknown")
        via = v.get("via", [])
        title = name
        if via and isinstance(via[0], dict):
            title = via[0].get("title", name)
        fix = v.get("fixAvailable")
        fix_str = "fix available" if fix else "no automatic fix"
        lines.append(f"{name} — {sev} — {title} ({fix_str})")
    if count == 0 and data.get("metadata", {}).get("vulnerabilities"):
        meta = data["metadata"]["vulnerabilities"]
        lines.append(
            f"Summary: {meta.get('high', 0)} high, {meta.get('moderate', 0)} moderate, "
            f"{meta.get('low', 0)} low"
        )
        count = sum(meta.values()) if isinstance(meta, dict) else 1
    alert = "\n".join(lines)
    return {
        "format": "npm_audit",
        "filename": filename,
        "finding_count": max(count, 1),
        "alert_text": alert,
        "title": f"npm audit ({count} package(s))",
    }


def extract_cve_ids(text: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"CVE-\d{4}-\d+", text, re.I)))
