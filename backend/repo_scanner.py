import json
import re
from pathlib import Path
from typing import Any


def parse_mistral_json(raw: str) -> dict[str, Any] | None:
    if not raw:
        return None
    text = raw.strip()
    text = re.sub(r"^```(?:json)?", "", text, flags=re.MULTILINE).strip()
    text = re.sub(r"```$", "", text, flags=re.MULTILINE).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    try:
        return json.loads(text)
    except Exception:
        return None


def _is_ignored_path(path: Path) -> bool:
    parts = set(path.parts)
    ignored = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        ".next",
        "dist",
        "build",
        "backend/data",
    }
    if any(p in ignored for p in parts):
        return True
    if path.name.endswith((".min.js", ".min.css")):
        return True
    return False


def _collect_code_evidence(root: Path, max_files: int = 60, max_bytes: int = 20_000) -> list[dict[str, Any]]:
    patterns = [
        ("Hardcoded secret", re.compile(r"(api[_-]?key|secret|token|password)\s*=\s*['\"][^'\"]+['\"]", re.I)),
        ("JWT/Token", re.compile(r"(eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,})")),
        ("Eval/Exec", re.compile(r"\b(eval|exec)\s*\(", re.I)),
        ("Insecure deserialization", re.compile(r"\b(pickle\.load|yaml\.load)\b", re.I)),
        ("Shell injection risk", re.compile(r"\bsubprocess\.(Popen|call|run)\b.*shell\s*=\s*True", re.I)),
        ("SQL injection risk", re.compile(r"(SELECT|INSERT|UPDATE|DELETE).*(\+|%s|\{)", re.I)),
    ]

    exts = {".py", ".js", ".ts", ".tsx", ".go", ".java", ".rb", ".php", ".yml", ".yaml", ".toml", ".tf", ".sh"}
    evidence: list[dict[str, Any]] = []

    candidates: list[Path] = []
    for p in root.rglob("*"):
        if len(candidates) >= max_files:
            break
        if not p.is_file():
            continue
        if _is_ignored_path(p):
            continue
        if p.suffix.lower() not in exts and p.name not in ("Dockerfile",):
            continue
        candidates.append(p)

    for p in candidates:
        try:
            raw = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if not raw.strip():
            continue
        text = raw[:max_bytes]
        lines = text.splitlines()
        matched: list[dict[str, Any]] = []
        for idx, line in enumerate(lines):
            for label, rx in patterns:
                if rx.search(line):
                    start = max(0, idx - 2)
                    end = min(len(lines), idx + 3)
                    snippet = "\n".join(lines[start:end])
                    matched.append({"rule": label, "line": idx + 1, "snippet": snippet})
        if matched:
            rel = str(p.relative_to(root))
            evidence.append({"file": rel, "matches": matched[:5]})

    return evidence


def _collect_dependency_summary(root: Path, max_files: int = 20) -> list[str]:
    files = []
    for name in ("package.json", "requirements.txt", "requirements-dev.txt", "Pipfile", "poetry.lock", "go.mod", "pom.xml", "Gemfile.lock"):
        files.extend(list(root.rglob(name)))
        if len(files) >= max_files:
            break
    out: list[str] = []
    for f in files[:max_files]:
        if _is_ignored_path(f):
            continue
        try:
            rel = str(f.relative_to(root))
            content = f.read_text(encoding="utf-8", errors="ignore")
            out.append(f"FILE: {rel}\n{content[:6000]}")
        except Exception:
            continue
    return out


def scan_repository_with_mistral(root_dir: str, chat_mistral) -> dict[str, Any]:
    root = Path(root_dir).resolve()
    evidence = _collect_code_evidence(root)
    deps = _collect_dependency_summary(root)

    evidence_text = "\n\n".join(
        [
            f"FILE: {e['file']}\n" + "\n".join([f"- {m['rule']} @ line {m['line']}:\n{m['snippet']}" for m in e["matches"]])
            for e in evidence
        ]
    )
    deps_text = "\n\n".join(deps)

    prompt = f"""You are a security expert performing a whole-repository vulnerability review.

Analyze the repo for vulnerabilities across:
- dependencies (lockfiles/manifests)
- insecure code patterns (injection, secrets, auth, deserialization)
- risky configs (Dockerfile, CI/CD, hardcoded credentials)

You are given:

== Dependency files (truncated) ==
{deps_text}

== Code/config evidence (heuristic matches) ==
{evidence_text}

Think through risks first. Then at the end output ONLY a JSON block wrapped in ```json ... ``` with this exact structure:
```json
{{
  "summary": "1-2 paragraphs",
  "dependency_findings": [{{"ecosystem":"PyPI|npm|Go|Maven|RubyGems|Other","package":"name","version":"x","severity":"CRITICAL|HIGH|MEDIUM|LOW|NONE","cve_ids":["CVE-..."],"summary":"...","recommended_version":"x or null","owasp":"A06:2021-Vulnerable and Outdated Components"}}],
  "code_findings": [{{"file":"path","line":123,"severity":"CRITICAL|HIGH|MEDIUM|LOW","cwe":"CWE-89","owasp":"A03:2021-Injection","summary":"...","evidence":"...","recommendation":"..."}}],
  "config_findings": [{{"file":"path","severity":"HIGH","summary":"...","recommendation":"..."}}],
  "critical_count": 0,
  "high_count": 0,
  "medium_count": 0,
  "low_count": 0,
  "total_findings": 0
}}
```"""

    result = chat_mistral(
        "You are a security expert.",
        prompt,
        json_mode=False,
        temperature=0.2,
    )
    if not result:
        return {
            "summary": "",
            "dependency_findings": [],
            "code_findings": [],
            "config_findings": [],
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "total_findings": 0,
            "error": "Mistral is not configured (set MISTRAL_API_KEY) or request failed",
        }
    raw = result[0]
    parsed = parse_mistral_json(raw)
    if not parsed:
        return {
            "summary": "",
            "dependency_findings": [],
            "code_findings": [],
            "config_findings": [],
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "total_findings": 0,
            "error": "Unable to parse JSON from Mistral response",
            "raw_preview": raw[:800],
        }
    return parsed


def build_steps_repo_scan(result: dict[str, Any], target: str) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []

    for f in result.get("dependency_findings", []) or []:
        sev = f.get("severity")
        if sev in ("CRITICAL", "HIGH", "MEDIUM"):
            steps.append(
                {
                    "action": "remediate_vulnerable_package",
                    "resource": f"{f.get('package','unknown')}@{f.get('version','')}",
                    "metadata": {
                        "severity": sev,
                        "cve_ids": f.get("cve_ids", []),
                        "ecosystem": f.get("ecosystem", ""),
                        "owasp": f.get("owasp", "A06:2021-Vulnerable and Outdated Components"),
                    },
                }
            )

    for f in result.get("code_findings", []) or []:
        sev = f.get("severity")
        if sev in ("CRITICAL", "HIGH", "MEDIUM"):
            steps.append(
                {
                    "action": "patch_vulnerable_code",
                    "resource": f"{target}:{f.get('file','unknown')}:{f.get('line','')}",
                    "metadata": {
                        "severity": sev,
                        "cwe": f.get("cwe", ""),
                        "owasp": f.get("owasp", ""),
                    },
                }
            )

    for f in result.get("config_findings", []) or []:
        sev = f.get("severity")
        if sev in ("CRITICAL", "HIGH", "MEDIUM"):
            steps.append(
                {
                    "action": "harden_configuration",
                    "resource": f"{target}:{f.get('file','unknown')}",
                    "metadata": {"severity": sev},
                }
            )

    return steps or [{"action": "no_action_required", "resource": target, "metadata": {}}]

