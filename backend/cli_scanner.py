import hashlib, json
from typing import List, Optional


def parse_mistral_json(raw):
    import re

    if not raw:
        return None
    text = raw.strip()
    text = re.sub(r"^```(?:json)?", "", text, flags=re.MULTILINE).strip()
    text = re.sub(r"```$", "", text, flags=re.MULTILINE).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    return json.loads(text)


async def analyze_packages_with_mistral(packages, ecosystem, chat_mistral):
    pkg_lines = "\n".join([f"- {p['name']} v{p['version']}" for p in packages])
    prompt = f"""You are a security expert with deep knowledge of CVEs.

Analyze these {ecosystem} packages for known security vulnerabilities:
{pkg_lines}

Think through what you know about each package version, then provide your findings.

At the end, output ONLY a JSON block in this exact format wrapped in triple backticks:
````json
{{
  "findings": [
    {{
      "package": "lodash",
      "version": "4.17.4",
      "severity": "HIGH",
      "cve_ids": ["CVE-2019-10744", "CVE-2020-8203"],
      "summary": "Prototype pollution vulnerability allows attackers to modify Object prototype",
      "recommended_version": "4.17.21",
      "owasp": "A06:2021-Vulnerable and Outdated Components"
    }}
  ],
  "total_scanned": {len(packages)},
  "critical_count": 0,
  "high_count": 0,
  "medium_count": 0,
  "low_count": 0,
  "safe_count": 0
}}
````
Include ALL packages in findings array. Set severity to NONE for safe packages. Fill counts accurately."""
    try:
        result = chat_mistral(
            "You are a security expert with deep knowledge of CVEs.",
            prompt,
            json_mode=False,
            temperature=0.2,
        )
        if not result:
            raise RuntimeError("Mistral is not configured (set MISTRAL_API_KEY) or request failed")
        raw = result[0] if result else ""
        parsed = parse_mistral_json(raw)
        if parsed is None:
            raise ValueError("Unable to parse JSON from Mistral response")
        return parsed
    except Exception as e:
        return {"findings":[],"total_scanned":len(packages),"critical_count":0,"high_count":0,"medium_count":0,"low_count":0,"safe_count":len(packages),"error":str(e)}

async def analyze_container_with_mistral(image, sbom_packages, chat_mistral):
    sbom = ""
    if sbom_packages:
        sbom = "\nSBOM:\n" + "\n".join([f"- {p['name']} {p['version']} ({p.get('ecosystem','')})" for p in sbom_packages])
    prompt = f"""You are a container security expert with deep knowledge of Docker image CVEs.

Analyze this container image for security vulnerabilities:
Image: {image}{sbom}

Consider: known CVEs for this image version, base OS risks, EOL status, package vulnerabilities.

At the end, output ONLY a JSON block in this exact format wrapped in triple backticks:
````json
{{
  "image": "{image}",
  "base_os_guess": "Debian",
  "uses_latest_tag": false,
  "overall_risk": "HIGH",
  "image_findings": [
    {{
      "component": "base image",
      "severity": "HIGH",
      "cve_ids": ["CVE-2021-33910"],
      "summary": "systemd vulnerability in base Debian image"
    }}
  ],
  "package_findings": [],
  "hardening_steps": [
    "Upgrade to nginx:1.25 or later",
    "Run as non-root user",
    "Use distroless base image"
  ],
  "critical_count": 0,
  "high_count": 1,
  "medium_count": 0,
  "low_count": 0,
  "total_findings": 1,
  "owasp": "A06:2021-Vulnerable and Outdated Components"
}}
```"""
    try:
        result = chat_mistral(
            "You are a container security expert with deep knowledge of Docker image CVEs.",
            prompt,
            json_mode=False,
            temperature=0.2,
        )
        if not result:
            raise RuntimeError("Mistral is not configured (set MISTRAL_API_KEY) or request failed")
        raw = result[0] if result else ""
        parsed = parse_mistral_json(raw)
        if parsed is None:
            raise ValueError("Unable to parse JSON from Mistral response")
        return parsed
    except Exception as e:
        return {"image":image,"base_os_guess":"Unknown","uses_latest_tag":"latest" in image,"overall_risk":"UNKNOWN","image_findings":[],"package_findings":[],"hardening_steps":[],"critical_count":0,"high_count":0,"medium_count":0,"low_count":0,"total_findings":0,"error":str(e)}

def build_steps_packages(findings):
    steps = [{"action":"remediate_vulnerable_package","resource":f"{f.get('package')}@{f.get('version')}","metadata":{"severity":f.get("severity"),"cve_ids":f.get("cve_ids",[]),"owasp":f.get("owasp","A06:2021")}} for f in findings if f.get("severity") in ("CRITICAL","HIGH","MEDIUM")]
    return steps or [{"action":"no_action_required","resource":"package_scan","metadata":{}}]

def build_steps_container(image, result):
    steps = [{"action":"patch_container_component","resource":f"{image}→{f.get('component',f.get('package','unknown'))}","metadata":{"severity":f.get("severity"),"cve_ids":f.get("cve_ids",[])}} for f in (result.get("image_findings",[])+result.get("package_findings",[])) if f.get("severity") in ("CRITICAL","HIGH","MEDIUM")]
    if result.get("uses_latest_tag"):
        steps.append({"action":"pin_image_tag","resource":image,"metadata":{"reason":"latest tag is a security anti-pattern"}})
    return steps or [{"action":"no_action_required","resource":image,"metadata":{}}]

def make_receipt(steps):
    return hashlib.sha256(json.dumps(steps,sort_keys=True).encode()).hexdigest()
