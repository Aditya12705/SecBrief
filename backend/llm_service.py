"""LLM helpers — Mistral API with structured security + compliance outputs."""

from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

_COMPLIANCE_SCHEMA = """
  "owasp_category": "e.g. A03:2021-Injection or N/A",
  "cwe_id": "e.g. CWE-89 or N/A",
  "soc2_controls": ["CC6.1", "CC7.2"],
  "financial_impact_inr": "Plain English estimate in Indian Rupees, e.g. ₹2–8 lakhs potential breach cost"
"""

SYSTEM_EXPLAIN = f"""You are SecBrief, a security analyst for developers who are NOT security experts.
Respond with ONLY valid JSON (no markdown fences):
{{
  "title": "short headline",
  "severity": "Low|Medium|High|Critical",
  "risk_score": 1-10,
  "summary": "2-3 sentence plain English summary",
  "what_happened": "paragraph",
  "who_is_affected": "paragraph",
  {_COMPLIANCE_SCHEMA.strip()},
  "what_to_do": ["action strings"],
  "safe_commands": ["only safe shell commands if any"]
}}
Map findings to OWASP Top 10 (2021) and relevant SOC 2 Trust Service Criteria when applicable.
Never suggest rm -rf, drop database, or disabling security controls."""

SYSTEM_CODE_AUDIT = f"""You are SecBrief auditing a code snippet for vulnerabilities.
Respond with ONLY valid JSON:
{{
  "title": "short headline",
  "severity": "Low|Medium|High|Critical",
  "risk_score": 1-10,
  "summary": "2-3 sentences",
  "vulnerabilities": [{{"name": "SQL Injection", "line_hint": "approx line or pattern", "severity": "High", "fix": "use parameterized queries"}}],
  {_COMPLIANCE_SCHEMA.strip()},
  "what_to_do": ["prioritized fixes"],
  "what_happened": "what the code does wrong"
}}
Identify OWASP categories and CWE IDs precisely."""

SYSTEM_REPO_SCAN = f"""You are SecBrief scanning a GitHub repository for security posture.
Respond with ONLY valid JSON:
{{
  "title": "short headline",
  "severity": "Low|Medium|High|Critical",
  "risk_score": 1-10,
  "summary": "2-3 sentences",
  {_COMPLIANCE_SCHEMA.strip()},
  "dependency_risks": [{{"package": "name", "concern": "why", "severity": "Low|Medium|High"}}],
  "config_gaps": ["missing security practices"],
  "what_to_do": ["prioritized actions"],
  "recommended_scan_commands": ["npm audit", "pip audit"]
}}
Base analysis on manifest files provided."""

SYSTEM_PLAN = """You output ONLY valid JSON for a remediation plan ArmorIQ verifies:
{
  "goal": "one line",
  "steps": [
    {"action": "snake_case", "description": "human text", "params": {}}
  ]
}
Allowed actions: read_advisory, analyze_impact, bump_dependency, run_tests, open_pr, patch_config, scan_repo, patch_code.
Include delete_all ONLY if user explicitly requests destructive wipe (for policy demo)."""


def model_id() -> str:
    return os.getenv("MISTRAL_MODEL", "mistral-small-latest")


def _api_key_configured() -> bool:
    key = (os.getenv("MISTRAL_API_KEY") or "").strip()
    if not key:
        return False
    placeholders = ("your_key", "paste", "xxx", "sk-...")
    return not any(p in key.lower() for p in placeholders)


def llm_status() -> dict[str, Any]:
    return {
        "provider": "mistral",
        "model": model_id(),
        "configured": _api_key_configured(),
    }


def _chat_mistral(
    system: str,
    user: str,
    *,
    json_mode: bool = True,
    temperature: float = 0.3,
) -> tuple[str, str] | None:
    key = os.getenv("MISTRAL_API_KEY", "").strip()
    if not key:
        return None
    model = model_id()
    body: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    try:
        r = httpx.post(
            MISTRAL_API_URL,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json=body,
            timeout=120.0,
        )
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        if content:
            return content, f"mistral/{model}"
    except Exception:
        pass
    return None


def _parse_json(raw: str) -> dict[str, Any] | None:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return None


def _format_compliance_block(data: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    owasp = data.get("owasp_category")
    cwe = data.get("cwe_id")
    soc2 = data.get("soc2_controls")
    inr = data.get("financial_impact_inr")
    if owasp and str(owasp).upper() != "N/A":
        lines.append(f"**OWASP:** {owasp}")
    if cwe and str(cwe).upper() != "N/A":
        lines.append(f"**CWE:** {cwe}")
    if soc2 and isinstance(soc2, list) and soc2:
        lines.append(f"**SOC 2:** {', '.join(str(s) for s in soc2[:5])}")
    if inr:
        lines.append(f"**Financial impact:** {inr}")
    if lines:
        return ["## Compliance & risk", *lines, ""]
    return []


def _format_analysis(data: dict[str, Any]) -> str:
    lines = [
        f"# {data.get('title', 'Security analysis')}",
        f"**Severity:** {data.get('severity', 'Unknown')} · **Risk score:** {data.get('risk_score', '?')}/10",
        "",
        data.get("summary", ""),
        "",
    ]
    lines.extend(_format_compliance_block(data))
    if data.get("what_happened"):
        lines.extend(["## What happened", data["what_happened"], ""])
    if data.get("who_is_affected"):
        lines.extend(["## Who is affected", data["who_is_affected"], ""])
    if data.get("vulnerabilities"):
        lines.append("## Findings")
        for v in data["vulnerabilities"][:8]:
            lines.append(
                f"- **{v.get('name', '?')}** ({v.get('severity', '?')}): {v.get('fix', v.get('line_hint', ''))}"
            )
        lines.append("")
    if data.get("dependency_risks"):
        lines.append("## Dependency risks")
        for r in data["dependency_risks"][:8]:
            lines.append(f"- **{r.get('package', '?')}** ({r.get('severity', '?')}): {r.get('concern', '')}")
        lines.append("")
    if data.get("config_gaps"):
        lines.append("## Gaps")
        for g in data["config_gaps"][:6]:
            lines.append(f"- {g}")
        lines.append("")
    if data.get("what_to_do"):
        lines.append("## What to do next")
        for i, step in enumerate(data["what_to_do"][:8], 1):
            lines.append(f"{i}. {step}")
    if data.get("safe_commands"):
        lines.extend(["", "## Safe commands", "```", *data["safe_commands"][:5], "```"])
    if data.get("recommended_scan_commands"):
        lines.extend(["", "## Run locally", "```", *data["recommended_scan_commands"][:5], "```"])
    return "\n".join(lines)


def explain_alert(alert_text: str) -> tuple[dict[str, Any], str]:
    result = _chat_mistral(SYSTEM_EXPLAIN, alert_text[:12000], temperature=0.3)
    if result:
        raw, source = result
        parsed = _parse_json(raw)
        if parsed:
            parsed["formatted"] = _format_analysis(parsed)
            return parsed, source
    fallback = _fallback_explain_structured(alert_text)
    fallback["formatted"] = _format_analysis(fallback)
    return fallback, "fallback"


def audit_code(code: str) -> tuple[dict[str, Any], str]:
    prompt = f"Audit this code snippet:\n\n```\n{code[:15000]}\n```"
    result = _chat_mistral(SYSTEM_CODE_AUDIT, prompt, temperature=0.25)
    if result:
        raw, source = result
        parsed = _parse_json(raw)
        if parsed:
            parsed["formatted"] = _format_analysis(parsed)
            return parsed, source
    fallback = _fallback_explain_structured(code)
    fallback["title"] = "Code snippet audit"
    fallback["formatted"] = _format_analysis(fallback)
    return fallback, "fallback"


def analyze_repo(scan_context: str, repo_name: str) -> tuple[dict[str, Any], str]:
    prompt = f"Analyze security posture for repository: {repo_name}\n\n{scan_context[:20000]}"
    result = _chat_mistral(SYSTEM_REPO_SCAN, prompt, temperature=0.25)
    if result:
        raw, source = result
        parsed = _parse_json(raw)
        if parsed:
            parsed["formatted"] = _format_analysis(parsed)
            parsed["repo"] = repo_name
            return parsed, source
    fallback = {
        "title": f"Repo scan: {repo_name}",
        "severity": "Medium",
        "risk_score": 5,
        "summary": "Heuristic scan completed. Connect Mistral API for deep analysis.",
        "what_to_do": [
            "Run stack-appropriate audit",
            "Enable Dependabot",
            "Generate a verified fix plan in SecBrief",
        ],
        "formatted": "",
    }
    fallback["formatted"] = _format_analysis(fallback)
    return fallback, "fallback"


def build_fix_plan(alert_text: str, user_request: str) -> tuple[dict[str, Any], str]:
    prompt = f"Alert/context:\n{alert_text[:8000]}\n\nUser request:\n{user_request}"
    result = _chat_mistral(SYSTEM_PLAN, prompt, json_mode=True, temperature=0.2)
    if result:
        raw, source = result
        parsed = _parse_json(raw)
        if parsed and parsed.get("steps"):
            return parsed, source
    return _fallback_plan(alert_text), "fallback"


def _fallback_explain_structured(text: str) -> dict[str, Any]:
    severity, risk = "Medium", 5
    if re.search(r"critical|9\.[0-9]|remote code|rce", text, re.I):
        severity, risk = "Critical", 9
    elif re.search(r"high|8\.[0-9]", text, re.I):
        severity, risk = "High", 7
    elif re.search(r"low|info", text, re.I):
        severity, risk = "Low", 3
    owasp, cwe = "N/A", "N/A"
    if re.search(r"sql|query|select.*\+|f\".*select", text, re.I):
        owasp, cwe = "A03:2021-Injection", "CWE-89"
    elif re.search(r"eval\(|exec\(", text):
        owasp, cwe = "A03:2021-Injection", "CWE-94"
    return {
        "title": "Security finding",
        "severity": severity,
        "risk_score": risk,
        "summary": "Potential security issue detected. Review and remediate before production.",
        "what_happened": "Pattern matches a known vulnerability class.",
        "who_is_affected": "Application users and data integrity.",
        "owasp_category": owasp,
        "cwe_id": cwe,
        "soc2_controls": ["CC6.1", "CC7.2"] if owasp != "N/A" else [],
        "financial_impact_inr": "₹1–5 lakhs estimated exposure if exploited (illustrative)",
        "what_to_do": ["Review finding", "Apply patch", "Run verified fix plan"],
        "safe_commands": ["npm audit"],
    }


def _fallback_plan(alert_text: str) -> dict[str, Any]:
    steps = [
        {"action": "read_advisory", "description": "Read official advisory", "params": {}},
        {"action": "bump_dependency", "description": "Upgrade vulnerable dependency", "params": {}},
        {"action": "run_tests", "description": "Run test suite", "params": {}},
        {"action": "open_pr", "description": "Open PR with fix", "params": {}},
    ]
    if "delete" in alert_text.lower():
        steps.append({"action": "delete_all", "description": "Unsafe — policy demo", "params": {}})
    return {"goal": "Safely remediate reported vulnerability", "steps": steps}


async def call_mistral(prompt: str, system: str = "You are a security expert.") -> str:
    """Async call to Mistral for vulnerability analysis."""
    key = os.getenv("MISTRAL_API_KEY", "").strip()
    if not key:
        return "Error: MISTRAL_API_KEY not set"
    model = model_id()
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            r = await client.post(
                MISTRAL_API_URL,
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                },
            )
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
            return content or ""
        except Exception as e:
            return f"Error: {str(e)}"
