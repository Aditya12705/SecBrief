"""SecBrief API — explain, audit, and enforce security remediation with ArmorIQ."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field

from alert_parser import extract_cve_ids, parse_upload
from armoriq_service import build_remediation_plan, verify_plan
from db import create_session, get_session, init_db, list_sessions, log_event, get_api_key_by_email
from auth import generate_api_key, get_current_user
from export_service import build_incident_brief
from github_service import list_demo_repos, scan_repository
from llm_service import analyze_repo, audit_code, build_fix_plan, explain_alert, llm_status, model_id
from scan_enricher import deep_scan_repository, merge_deep_into_scan
from github_scan_service import run_github_scan

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
init_db()

app = FastAPI(
    title="SecBrief API",
    description="Security audit + policy-enforced remediation (ArmorIQ + Mistral)",
    version="1.0.0",
)

def _cors_origins() -> list[str]:
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]
    extra = os.getenv("FRONTEND_ORIGIN", "").strip()
    if extra and extra not in origins:
        origins.append(extra)
    return origins


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExplainRequest(BaseModel):
    email: EmailStr
    alert_text: str = Field(..., min_length=10, max_length=50000)
    session_id: str | None = None


class CodeAuditRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=10, max_length=50000)
    session_id: str | None = None


class PlanRequest(BaseModel):
    email: EmailStr
    alert_text: str = Field(..., min_length=10, max_length=50000)
    user_request: str = Field(default="Create a safe remediation plan")
    simulate_attack: bool = Field(
        default=False,
        description="Append malicious step after signing — demo prompt-injection defense",
    )
    use_delegation_demo: bool = Field(default=False)
    session_id: str | None = None


class GitHubScanRequest(BaseModel):
    email: EmailStr
    repo_url: str = Field(..., min_length=3, max_length=500)
    deep_scan: bool = Field(default=True)
    session_id: str | None = None


class ExportRequest(BaseModel):
    email: EmailStr
    session_id: str | None = None
    alert_text: str = ""
    analysis: dict[str, Any] | None = None
    plan: dict[str, Any] | None = None
    decisions: list[dict[str, Any]] = Field(default_factory=list)
    receipt: dict[str, Any] | None = None


class HealthResponse(BaseModel):
    status: str
    product: str
    armoriq_configured: bool
    armoriq_config_file: bool
    github_token: bool
    llm: dict
    strict_armoriq: bool


class SignupRequest(BaseModel):
    email: EmailStr


class SignupResponse(BaseModel):
    email: str
    api_key: str
    plan: str
    install_snippet: str


class MeResponse(BaseModel):
    email: str
    plan: str
    created_at: str


class GitHubScanFile(BaseModel):
    filename: str
    content: str


class GitHubScanPayload(BaseModel):
    repo: str
    pr_number: int
    changed_files: list[GitHubScanFile]
    ecosystem_files: list[GitHubScanFile] | None = None


def _ensure_session(email: str, session_id: str | None, input_mode: str, summary: str) -> str:
    if session_id:
        return session_id
    return create_session(email, input_mode, summary)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    key = os.getenv("ARMORIQ_API_KEY", "")
    config_path = Path(__file__).parent / "armoriq.yaml"
    return HealthResponse(
        status="ok",
        product="SecBrief",
        armoriq_configured=bool(key.startswith(("ak_live_", "ak_test_", "ak_claw_"))),
        armoriq_config_file=config_path.is_file(),
        github_token=bool(os.getenv("GITHUB_TOKEN", "").strip()),
        llm=llm_status(),
        strict_armoriq=os.getenv("SECBRIEF_STRICT_ARMORIQ", "").lower() in ("1", "true"),
    )


INSTALL_SNIPPET = """name: SecBrief Security Scan
on:
  pull_request:
    types: [opened, synchronize, reopened]
jobs:
  secbrief:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: SecBrief Scan
        uses: your-org/secbrief-action@v1
        with:
          api-key: ${{ secrets.SECBRIEF_API_KEY }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
"""


@app.post("/api/auth/signup", response_model=SignupResponse)
def api_auth_signup(body: SignupRequest) -> SignupResponse:
    existing = get_api_key_by_email(body.email)
    if existing:
        return SignupResponse(
            email=existing["email"],
            api_key=existing["api_key"],
            plan=existing["plan"],
            install_snippet=INSTALL_SNIPPET,
        )
    api_key = generate_api_key(body.email)
    return SignupResponse(
        email=body.email,
        api_key=api_key,
        plan="free",
        install_snippet=INSTALL_SNIPPET,
    )


@app.get("/api/auth/me", response_model=MeResponse)
def api_auth_me(email: str = Depends(get_current_user)) -> MeResponse:
    key_data = get_api_key_by_email(email)
    if not key_data:
        raise HTTPException(status_code=404, detail="User not found")
    return MeResponse(
        email=key_data["email"],
        plan=key_data["plan"],
        created_at=key_data["created_at"],
    )


@app.post("/api/github-scan")
def api_github_scan(
    payload: GitHubScanPayload,
    email: str = Depends(get_current_user),
) -> dict[str, Any]:
    result = run_github_scan(payload.model_dump())
    # Log to sessions
    sid = create_session(email, "github_scan", f"Scan {payload.repo} PR #{payload.pr_number}")
    log_event(sid, "github_scan", {"repo": payload.repo, "pr_number": payload.pr_number, "result": result})
    return result


@app.get("/api/demo-repos")
def api_demo_repos() -> dict:
    return {"repos": list_demo_repos()}


@app.post("/api/parse-upload")
async def api_parse_upload(file: UploadFile = File(...)) -> dict:
    raw = await file.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise HTTPException(status_code=400, detail="File must be UTF-8 text") from e
    if len(text) > 500_000:
        raise HTTPException(status_code=400, detail="File too large (max 500KB)")
    parsed = parse_upload(text, file.filename or "upload.txt")
    parsed["cve_ids"] = extract_cve_ids(parsed["alert_text"])
    return parsed


@app.post("/api/github/scan")
def api_github_scan(body: GitHubScanRequest) -> dict:
    try:
        scan = scan_repository(body.repo_url)
        if body.deep_scan:
            deep = deep_scan_repository(body.repo_url)
            scan = merge_deep_into_scan(scan, deep)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"GitHub API error: {e.response.status_code}. Add GITHUB_TOKEN for higher limits.",
        ) from e

    analysis, source = analyze_repo(scan["scan_context"], scan["full_name"])
    sid = _ensure_session(
        body.email,
        body.session_id,
        "github",
        f"Scan {scan['full_name']}",
    )
    log_event(sid, "scan", {"repo": scan["full_name"], "deep": body.deep_scan})

    return {
        "scan": scan,
        "analysis": analysis,
        "analysis_source": source,
        "user_email": body.email,
        "session_id": sid,
    }


@app.post("/api/audit-code")
def api_audit_code(body: CodeAuditRequest) -> dict:
    analysis, source = audit_code(body.code)
    sid = _ensure_session(body.email, body.session_id, "code", analysis.get("title", "Code audit"))
    log_event(sid, "audit_code", {"severity": analysis.get("severity"), "source": source})
    return {
        "analysis": analysis,
        "explanation": analysis.get("formatted", ""),
        "source": source,
        "user_email": body.email,
        "session_id": sid,
    }


@app.post("/api/explain")
def api_explain(body: ExplainRequest) -> dict:
    analysis, source = explain_alert(body.alert_text)
    sid = _ensure_session(
        body.email,
        body.session_id,
        "paste",
        analysis.get("title", "Alert explained"),
    )
    log_event(sid, "explain", {"severity": analysis.get("severity"), "source": source})
    return {
        "analysis": analysis,
        "explanation": analysis.get("formatted", ""),
        "source": source,
        "user_email": body.email,
        "session_id": sid,
        "cve_ids": extract_cve_ids(body.alert_text),
    }


@app.post("/api/plan-fix")
def api_plan_fix(body: PlanRequest) -> dict:
    raw_plan, plan_source = build_fix_plan(body.alert_text, body.user_request)
    plan = build_remediation_plan(
        raw_plan.get("goal", "Remediate vulnerability"),
        raw_plan.get("steps", []),
    )
    llm = model_id()
    prompt = f"{body.user_request}\n\nContext:\n{body.alert_text[:2000]}"

    result = verify_plan(
        body.email,
        llm,
        prompt,
        plan,
        simulate_attack=body.simulate_attack,
        use_delegation_demo=body.use_delegation_demo,
    )

    if result.error and os.getenv("SECBRIEF_STRICT_ARMORIQ", "").lower() in ("1", "true"):
        raise HTTPException(status_code=503, detail=result.error)

    sid = _ensure_session(
        body.email,
        body.session_id,
        "plan",
        plan.get("goal", "Remediation plan"),
    )
    log_event(
        sid,
        "plan_verify",
        {
            "armoriq_live": result.armoriq_live,
            "simulate_attack": body.simulate_attack,
            "receipt": result.receipt.to_dict(),
            "decisions": [d.__dict__ for d in result.decisions],
        },
    )

    return {
        "plan": plan,
        "plan_source": plan_source,
        "armoriq_live": result.armoriq_live,
        "intent_receipt": result.receipt.to_dict(),
        "decisions": [
            {
                "action": d.action,
                "mcp": d.mcp,
                "status": d.status,
                "message": d.message,
                "simulated": d.simulated,
                "csrg_path": d.csrg_path,
                "in_signed_plan": d.in_signed_plan,
            }
            for d in result.decisions
        ],
        "delegation_demo": result.delegation_demo,
        "summary": _summarize(result.decisions),
        "session_id": sid,
        "attack_mode": body.simulate_attack,
    }


@app.post("/api/export-brief")
def api_export_brief(body: ExportRequest) -> PlainTextResponse:
    md = build_incident_brief(
        user_email=body.email,
        analysis=body.analysis,
        plan=body.plan,
        decisions=body.decisions,
        receipt=body.receipt,
        session_id=body.session_id or "",
    )
    return PlainTextResponse(content=md, media_type="text/markdown; charset=utf-8")


@app.get("/api/sessions/{user_email}")
def api_sessions(user_email: str, limit: int = 15) -> dict:
    return {"sessions": list_sessions(user_email, limit=limit)}


@app.get("/api/session/{session_id}")
def api_session(session_id: str) -> dict:
    s = get_session(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return s


def _summarize(decisions) -> str:
    if not decisions:
        return "No steps in plan."
    blocked = sum(1 for d in decisions if d.status == "block")
    allowed = sum(1 for d in decisions if d.status == "allow")
    injected = sum(1 for d in decisions if not d.in_signed_plan)
    if blocked:
        msg = f"{allowed} step(s) allowed, {blocked} blocked by ArmorIQ policy."
        if injected:
            msg += f" {injected} step(s) were NOT in the signed LLM plan (injection blocked)."
        return msg
    return f"All {allowed} step(s) passed policy checks."


@app.get("/api/sample-alert")
def sample_alert() -> dict:
    return {
        "text": """npm audit report
==============================================================================
lodash  <=4.17.20
Severity: high
Prototype Pollution - https://github.com/advisories/GHSA-p6mc-m468-83gw
fix available via `npm audit fix`
Will install lodash@4.17.21

1 high severity vulnerability
""",
    }


@app.get("/api/why-secbrief")
def why_secbrief() -> dict:
    return {
        "tagline": "ChatGPT explains the CVE. SecBrief enforces the fix.",
        "product": "SecBrief",
        "differentiators": [
            "Security-only workflow — not a general enterprise copilot",
            "Signed intent plans (CSRG) — model cannot add undeclared steps",
            "Live allow / block / hold with audit on platform.armoriq.ai",
            "SARIF & npm audit JSON upload — not copy-paste only",
            "Attack-the-agent demo — proves prompt-injection defense",
            "Monday-morning export — compliance-ready incident brief",
            "Per-user SQLite session history + cryptographic receipt",
        ],
        "comparison": [
            {
                "dimension": "Purpose",
                "generic_ai": "General chat — HR, code, slides, anything",
                "secbrief": "Vulnerability explain → signed fix plan → policy enforcement only",
            },
            {
                "dimension": "Remediation trust",
                "generic_ai": "Suggests commands; user copy-pastes at own risk",
                "secbrief": "Each step bound to Ed25519-signed intent token + Merkle proof",
            },
            {
                "dimension": "Prompt injection",
                "generic_ai": "Malicious instructions can change tool behavior",
                "secbrief": "Undeclared steps fail enforce — even if LLM hallucinates them",
            },
            {
                "dimension": "Enterprise copilot",
                "generic_ai": "Broad DLP + tenant policies; rarely per-fix-step crypto",
                "secbrief": "Intent-Based Access Protocol on every remediation action",
            },
            {
                "dimension": "Audit & compliance",
                "generic_ai": "Chat logs; not tied to cryptographic plan hash",
                "secbrief": "Per-email ArmorIQ audit + exportable incident brief",
            },
            {
                "dimension": "Input formats",
                "generic_ai": "Paste text; manual context",
                "secbrief": "SARIF, npm audit JSON, GitHub deep scan, CVE paste",
            },
            {
                "dimension": "Multi-agent safety",
                "generic_ai": "Sub-agents often share parent credentials",
                "secbrief": "Delegation demo — sub-agent token scoped to allowed_actions",
            },
        ],
    }


@app.get("/api/why-intentseal")
@app.get("/api/why-patchproof")
@app.get("/api/why-vulnexplain")
@app.get("/api/why-luma")
def why_legacy() -> dict:
    return why_secbrief()


# --- Static frontend (Next.js export) for Hugging Face / single-container deploy ---
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")
