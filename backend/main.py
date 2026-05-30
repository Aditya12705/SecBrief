"""SecBrief API — explain, audit, and enforce security remediation with ArmorIQ."""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Load env before other imports
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path, override=True)

from typing import Any, Optional
import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field

from alert_parser import extract_cve_ids, parse_upload
from armoriq_service import build_remediation_plan, verify_plan
from db import create_session, get_session, init_db, list_sessions, log_event, get_api_key_by_email
from auth import generate_api_key, get_current_user
from osv_scanner import scan_packages_osv
from cli_scanner import (
    analyze_packages_with_mistral,
    analyze_container_with_mistral,
    build_steps_packages,
    build_steps_container,
    make_receipt,
)
from export_service import build_incident_brief
from github_service import list_demo_repos, scan_repository
from llm_service import analyze_repo, audit_code, build_fix_plan, explain_alert, llm_status, model_id
from llm_service import _chat_mistral
from scan_enricher import deep_scan_repository, merge_deep_into_scan
from github_scan_service import run_github_scan

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
        "*"
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


class OsvScanRequest(BaseModel):
    ecosystem: str  # "npm", "PyPI", "Go", "Maven", "RubyGems", "crates.io"
    packages: list[dict[str, Any]]  # [{"name": str, "version": str}]
    user_email: Optional[str] = None


class PackageScanRequest(BaseModel):
    ecosystem: str
    packages: list[dict[str, Any]]
    user_email: Optional[str] = None


class ContainerScanRequest(BaseModel):
    image: str  # e.g. "nginx:1.21"
    sbom_packages: Optional[list[dict[str, Any]]] = None  # [{"name": str, "version": str, "ecosystem": str}]
    user_email: Optional[str] = None


class ProjectScanRequest(BaseModel):
    path: str = "."
    user_email: Optional[str] = None


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
    frontend_build_sha: str
    armoriq_configured: bool
    armoriq_config_file: bool
    github_token: bool
    llm: dict[str, Any]
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


def _frontend_build_sha() -> str:
    sha_path = Path(__file__).resolve().parent.parent / "static" / ".build-sha"
    try:
        return sha_path.read_text(encoding="utf-8").strip() or "unknown"
    except OSError:
        return "unknown"


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    key = os.getenv("ARMORIQ_API_KEY", "")
    config_path = Path(__file__).parent / "armoriq.yaml"
    return HealthResponse(
        status="ok",
        product="SecBrief",
        frontend_build_sha=_frontend_build_sha(),
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
        uses: AditthyaSS/secbrief-action@v1
        with:
          api-key: ${{ secrets.SECBRIEF_API_KEY }}
          github-token: ${{ secrets.GITHUB_TOKEN }}
          secbrief-api-url: https://aditya12705-secbrief.hf.space
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


# --- Mistral-based Vulnerability Scanning ---

@app.post("/api/package-scan")
async def package_scan(req: PackageScanRequest):
    result = await analyze_packages_with_mistral(req.packages, req.ecosystem, _chat_mistral)
    steps = build_steps_packages(result.get("findings",[]))
    armoriq = {"status":"skipped","receipt":None,"enforcement":[]}
    try:
        armoriq_service: Any = __import__("armoriq_service")
        enforcement = await armoriq_service.enforce_plan(steps)
        receipt = armoriq_service.create_intent_receipt(steps)
        armoriq = {"status":"enforced","receipt":receipt,"enforcement":enforcement}
    except:
        armoriq = {"status":"receipt_only","receipt":make_receipt(steps),"enforcement":steps}
    try:
        from db import save_scan_log
        save_scan_log("package",req.ecosystem,result.get("total_scanned",0),result.get("critical_count",0),str(armoriq.get("receipt","")),req.user_email)
    except: pass
    return {**result,"armoriq":armoriq}

@app.post("/api/container-scan")
async def container_scan(req: ContainerScanRequest):
    result = await analyze_container_with_mistral(req.image, req.sbom_packages, _chat_mistral)
    steps = build_steps_container(req.image, result)
    armoriq = {"status":"skipped","receipt":None,"enforcement":[]}
    try:
        armoriq_service: Any = __import__("armoriq_service")
        enforcement = await armoriq_service.enforce_plan(steps)
        receipt = armoriq_service.create_intent_receipt(steps)
        armoriq = {"status":"enforced","receipt":receipt,"enforcement":enforcement}
    except:
        armoriq = {"status":"receipt_only","receipt":make_receipt(steps),"enforcement":steps}
    try:
        from db import save_scan_log
        save_scan_log("container",req.image,result.get("total_findings",0),result.get("critical_count",0),str(armoriq.get("receipt","")),req.user_email)
    except: pass
    return {**result,"armoriq":armoriq}

@app.get("/api/scan-history")
async def scan_history(email: Optional[str] = None, limit: int = 20):
    try:
        from db import get_scan_logs
        return {"logs": get_scan_logs(email, limit)}
    except Exception as e:
        return {"logs":[],"error":str(e)}


@app.post("/api/project-scan")
async def project_scan(req: ProjectScanRequest):
    try:
        from repo_scanner import build_steps_repo_scan, scan_repository_with_mistral

        repo_root = Path(__file__).resolve().parent.parent
        target = (repo_root / (req.path or ".")).resolve()
        if repo_root not in target.parents and target != repo_root:
            raise HTTPException(status_code=400, detail="Invalid path (must be inside repository)")

        result = scan_repository_with_mistral(str(target), _chat_mistral)
        steps = build_steps_repo_scan(result, str(target))

        armoriq = {"status":"skipped","receipt":None,"enforcement":[]}
        try:
            armoriq_service: Any = __import__("armoriq_service")
            enforcement = await armoriq_service.enforce_plan(steps)
            receipt = armoriq_service.create_intent_receipt(steps)
            armoriq = {"status":"enforced","receipt":receipt,"enforcement":enforcement}
        except:
            armoriq = {"status":"receipt_only","receipt":make_receipt(steps),"enforcement":steps}

        try:
            from db import save_scan_log
            save_scan_log(
                "project",
                str(target),
                result.get("total_findings", 0),
                result.get("critical_count", 0),
                str(armoriq.get("receipt", "")),
                req.user_email,
            )
        except:
            pass

        return {**result, "armoriq": armoriq, "target": str(target)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/osv-scan")
async def osv_scan(req: OsvScanRequest):
    try:
        # Normalize packages — inject ecosystem
        packages = [
            {"name": p.get("name", ""), "version": p.get("version", ""), "ecosystem": req.ecosystem}
            for p in req.packages if p.get("name")
        ]

        # Run OSV scan
        scan_result = await scan_packages_osv(packages)

        # Build ArmorIQ enforcement plan — one step per vulnerable package
        steps = []
        for vuln in scan_result["vulnerabilities"]:
            steps.append({
                "action": "remediate_vulnerability",
                "resource": f"{vuln['package']}@{vuln['version']}",
                "metadata": {
                    "vuln_id": vuln["vuln_id"],
                    "severity": vuln["severity"],
                    "ecosystem": vuln["ecosystem"],
                    "osv_url": vuln["osv_url"],
                }
            })

        # If no vulns, add a "no_action_required" step so ArmorIQ still logs it
        if not steps:
            steps = [{"action": "no_action_required", "resource": f"{req.ecosystem} scan", "metadata": {"packages_scanned": len(packages)}}]

        # Call existing ArmorIQ enforcement
        armoriq_result = {"status": "skipped", "receipt": None, "enforcement": []}
        try:
            armoriq_service: Any = __import__("armoriq_service")
            enforcement = await armoriq_service.enforce_plan(steps)
            receipt = armoriq_service.create_intent_receipt(steps)
            armoriq_result = {"status": "enforced", "receipt": receipt, "enforcement": enforcement}
        except Exception:
            # Fallback
            receipt = make_receipt(steps)
            armoriq_result = {"status": "unavailable", "receipt": receipt, "enforcement": []}

        # Log to DB
        try:
            from db import save_osv_scan_log
            save_osv_scan_log("package", req.ecosystem, scan_result["total_vulns"], scan_result["critical_count"], str(armoriq_result.get("receipt", "")), req.user_email)
        except: pass

        return {
            **scan_result,
            "armoriq": armoriq_result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Pulse dashboard (read-only) ---
from dashboard_router import router as dashboard_router
app.include_router(dashboard_router)

# --- Static frontend (Next.js export) for Hugging Face / single-container deploy ---
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")
