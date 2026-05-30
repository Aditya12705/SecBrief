# TRAE IDE — Master prompt for SecBrief

Copy everything inside the **MASTER PROMPT** block below into TRAE **SOLO** or **Builder** chat after opening this repo as your workspace root (`D:\Luma` or cloned path).

---

## Before you paste

1. Open **this folder** as the TRAE project root (not `backend/` alone).
2. Copy `.env.example` → `.env` and fill:
   - `ARMORIQ_API_KEY` from https://platform.armoriq.ai
   - `MISTRAL_API_KEY` from https://console.mistral.ai
   - Optional: `GITHUB_TOKEN`, `SECBRIEF_STRICT_ARMORIQ=true`
3. Tell TRAE: *"Read README.md, PITCH.md, and backend/main.py first, then execute the master prompt."*

---

## MASTER PROMPT (copy from here)

```text
You are a senior full-stack engineer improving **SecBrief** — an ArmorIQ Hackathon (Track 2) project.

## Hackathon constraints (non-negotiable)
- **Track:** Track 2 — AI Agent for the Real World
- **Must integrate:** ArmorIQ Python SDK (`armoriq-sdk`) — `capture_plan`, `get_intent_token`, `invoke()`, per-user `for_user(email)` scopes, audit on platform.armoriq.ai
- **LLM:** Mistral API only (no OpenAI). Env: MISTRAL_API_KEY, MISTRAL_MODEL
- **Optional:** ArmorClaw for pipeline scanning — document integration, do not remove ArmorIQ as core
- **Docs:** https://docs.armoriq.ai/docs · https://docs-openclaw.armoriq.ai/docs

## Product one-liner
**ChatGPT explains the CVE. SecBrief enforces the fix.**

SecBrief is NOT a general chatbot. It is a **security-only briefing agent** that:
1. Ingests SARIF, npm audit JSON, GitHub repo scan, code snippet, or pasted alerts
2. Produces plain-English briefings with OWASP, CWE, SOC 2, and INR (₹) impact via Mistral
3. Builds remediation plans where **every step is verified by ArmorIQ** (allow / hold / block)
4. Exports a Monday-morning incident brief and shows cryptographic intent receipts

## Current codebase (do not rewrite from scratch)
- `backend/main.py` — FastAPI: `/api/github/scan`, `/api/audit-code`, `/api/explain`, `/api/plan-fix`, `/api/export-brief`, `/api/why-secbrief`
- `backend/armoriq_service.py` — ArmorIQ verify + attack simulation + delegation demo
- `backend/llm_service.py` — Mistral structured JSON (explain, repo scan, code audit, plan)
- `backend/github_service.py` + `scan_enricher.py` — GitHub manifest + deep scan
- `backend/alert_parser.py` — SARIF / npm JSON upload parsing
- `backend/db.py` — SQLite sessions
- `frontend/src/app/page.tsx` — main UI with tabs: GitHub, Paste, Upload, Code, Demo repos
- `PITCH.md`, `PPT_CONTENT.md`, `SUBMISSION.md` — hackathon copy (keep product name **SecBrief**)

## How we differ from ChatGPT / Gemini / Claude (build UI + logic around this)
| Generic AI | SecBrief |
|------------|----------|
| Any topic | Security workflow only |
| Text suggestions | Signed intent plan + per-step enforce |
| No crypto proof | Plan hash + Merkle step proofs (ArmorIQ) |
| Prompt injection can add tools | Undeclared steps BLOCKED (`delete_all` demo) |
| No compliance mapping | OWASP + CWE + SOC2 + ₹ on every briefing |
| Manual paste | SARIF upload, npm JSON, GitHub deep scan, code audit |

## Your mission — make SecBrief judge-ready and demo-perfect

Work in phases. After each phase, run backend + frontend and fix errors before continuing.

### Phase A — Demo reliability (highest priority)
1. Ensure `python -m uvicorn main:app --reload --port 8000` works from `backend/` with venv
2. Ensure `npm run dev` works from `frontend/` — fix any JSX/TypeScript errors
3. Verify end-to-end flows:
   - Code tab → SQLi sample → Audit code → shows OWASP/CWE chips
   - Attack-the-agent ON → Generate verified fix plan → `delete_all` shows BLOCK + intent receipt
   - Demo repo Express.js → deep scan → briefing → plan
   - Upload SARIF or npm audit JSON → explain → plan
4. Add clear error toasts/messages when Mistral or ArmorIQ keys missing (no silent fallback without UI hint)
5. Health endpoint status reflected accurately in Header pills

### Phase B — UI/UX polish (hackathon wow factor)
1. **Product-only homepage** — no giant comparison table on main screen (judges hear pitch verbally; see PPT_CONTENT.md)
2. Professional security aesthetic: dark theme, clear workflow bar (Input → Brief → Plan → Enforce)
3. Prominent **Intent Receipt** card after plan-fix (plan_hash, merkle_root, armoriq_live badge)
4. **ComplianceBar** — OWASP, CWE, SOC2, ₹ always visible on analysis messages
5. Mobile-responsive layout; loading skeletons during Mistral calls
6. Empty states with 1-line value prop: "Explain the risk. Enforce the fix."
7. Do NOT use invalid JSX tags like `<motion>` — use `<div>` only unless framer-motion is installed

### Phase C — Logic & ArmorIQ depth
1. Harden `armoriq_service.py`:
   - When ARMORIQ_API_KEY set: always use live `capture_plan` → `get_intent_token` → `invoke()`
   - `simulate_attack=true`: sign plan WITHOUT delete_all, then attempt delete_all → must BLOCK with message "not in signed plan"
   - Return rich `intent_receipt` object for frontend
2. Add `armoriq.yaml` example + README note for `armoriq init` / MCP registration if needed
3. Improve Mistral prompts in `llm_service.py` for Indian startup context (INR ranges, realistic SOC2 controls)
4. GitHub scan: surface `heuristic_findings` and `deep_scan` results clearly in UI

### Phase D — GitHub repo options (expand demo repos)
Curate and wire 8–10 public repos in `github_service.py` DEMO_REPOS:
- Node: expressjs/express, fastify/fastify
- Python: pallets/flask, fastapi/fastapi
- JS tooling: vitejs/vite
- React: vercel/next.js (optional — slow scan, mark as "large")
- Security education: OWASP/NodeGoat or similar (if API allows)
Each card: label, stack, one-line "why scan this", estimated scan time

### Phase E — Pitch artifacts
1. Update SUBMISSION.md slides to match current features (SARIF, attack demo, export brief)
2. Ensure PITCH.md demo script matches actual UI button labels
3. Add 60-second "judge FAQ" section to PITCH.md:
   - "Why not ChatGPT?" → enforcement + audit
   - "Why Mistral + ArmorIQ?" → brain vs bouncer
   - "Is this production?" → MVP with clear enterprise path (GitHub App, CI plugin)

### Phase F — Deploy (optional if time)
- Docker / Hugging Face Space per HF_DEPLOY.md
- Single-port serve: static frontend from `static/` mount in main.py

## Code quality rules
- Minimal diffs; extend existing files before creating new ones
- No secrets in git; use .env only
- Python 3.11+; use `python -m uvicorn` not broken global uvicorn
- TypeScript strict; keep `@/` path alias
- No OpenAI SDK or API calls

## Definition of done
- [ ] 2-minute demo works offline with keys in .env
- [ ] Attack-the-agent shows BLOCK on undeclared step
- [ ] Intent receipt visible with plan hash
- [ ] Export Monday-morning brief downloads/opens
- [ ] At least 5 demo repos one-click scannable
- [ ] README + PITCH accurate

Start with Phase A. Show me a short checklist of what you changed after each phase.
```

---

## Follow-up prompts (paste after master prompt completes a phase)

### UI only
```text
Improve SecBrief frontend only. Reference frontend/src/app/page.tsx and components/.
Goals: cleaner hero, better spacing, IntentReceiptCard more prominent, fix mobile layout.
Do not change backend API contracts. No comparison table on homepage.
```

### ArmorIQ hardening
```text
Focus on backend/armoriq_service.py and /api/plan-fix in main.py.
Ensure live ArmorIQ path works with ARMORIQ_API_KEY. Attack simulation must block delete_all
with clear message referencing signed plan. Improve intent_receipt fields for judges.
Add tests or a /api/plan-fix dry-run if helpful.
```

### GitHub repos
```text
Expand DEMO_REPOS in backend/github_service.py to 10 curated public repos.
Add stack badges and scan_time_hint. Update InputPanel demo tab UI to show grid cards.
Handle GitHub 403 with user-friendly message to add GITHUB_TOKEN.
```

### Pitch / slides
```text
Update SUBMISSION.md and PPT_CONTENT.md to match current SecBrief features.
Emphasize differentiation vs ChatGPT and vs enterprise copilot in slide 5.
Keep slides copy-paste ready for PowerPoint. Do not change application code.
```

### Bug fix
```text
SecBrief error: [paste error from terminal or browser console]
Fix with minimal diff. Verify backend health and frontend compile.
```

---

## TRAE workflow tips

| Step | Action |
|------|--------|
| 1 | **File → Open Folder** → repo root |
| 2 | Pin `PITCH.md`, `backend/main.py`, `frontend/src/app/page.tsx` in editor |
| 3 | Use **SOLO** for multi-file phases A–C |
| 4 | Use **Chat** for single bug fixes |
| 5 | Terminal 1: `cd backend && .\.venv\Scripts\python -m uvicorn main:app --reload` |
| 6 | Terminal 2: `cd frontend && npm run dev` |
| 7 | After TRAE edits: run both servers and click through PITCH.md demo script |

---

## Short prompt (if TRAE has token limits)

```text
Improve SecBrief (ArmorIQ Track 2 hackathon app in this repo): Mistral explains CVEs with OWASP/CWE/SOC2/INR; ArmorIQ enforces remediation steps with allow/block and intent receipt. Fix bugs, polish UI (product-only, no comparison wall), ensure Attack-the-agent blocks delete_all, expand GitHub demo repos, update PITCH.md. Read README.md and backend/main.py first. No OpenAI. Phases: reliability → UI → ArmorIQ → repos → pitch.
```
