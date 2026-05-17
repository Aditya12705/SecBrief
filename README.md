# SecBrief

**Explain the risk. Enforce the fix.**

Security copilot for the **ArmorIQ Hackathon (Track 2)**: turn CVE/SARIF noise and vulnerable code into plain-English **security briefings** with **OWASP / CWE / SOC 2 / INR** mapping, then **cryptographically verified** remediation plans via ArmorIQ.

> **Presenter materials:** [PITCH.md](./PITCH.md) · [PPT_CONTENT.md](./PPT_CONTENT.md) · [SUBMISSION.md](./SUBMISSION.md)  
> The live app is product-only; comparison tables and judge talking points live in those files.

---

## One-liner

*ChatGPT explains the CVE. SecBrief enforces the fix.*

---

## How it works

```
Input (SARIF / alert / repo / code)  →  Brief (Mistral + compliance)  →  Plan  →  Enforce (ArmorIQ)  →  Export
```

| Layer | Role |
|-------|------|
| **Mistral** | Plain-English explanations, risk scores, OWASP/CWE/SOC2/INR fields, remediation steps |
| **ArmorIQ SDK** | Signs the intent plan (CSRG), enforces allow / block / hold per step, audit on [platform.armoriq.ai](https://platform.armoriq.ai) |
| **FastAPI + SQLite** | API, SARIF/npm parsing, GitHub deep scan, session history |
| **Next.js** | Demo UI — scan, audit code, explain, verify, export |

**Why both?** Mistral is the *brain* (language + planning). ArmorIQ is the *bouncer* (cryptographic proof that only declared steps run).

---

## Features

- **Inputs:** GitHub deep scan · code snippet audit · paste alert · upload SARIF / npm audit JSON · curated demo repos
- **Briefings:** Severity, risk score 1–10, OWASP/CWE/SOC2/INR chips on every analysis
- **Enforcement:** Per-step allow / block / hold + intent receipt (plan hash)
- **Demos:** Attack-the-agent (`delete_all` blocked) · delegation (scoped sub-agent)
- **Export:** Monday-morning Markdown incident brief
- **Sessions:** SQLite audit log per user email

---

## Quick start

### Prerequisites

- Python 3.11+
- Node.js 18+
- [ArmorIQ API key](https://platform.armoriq.ai)
- [Mistral API key](https://console.mistral.ai)

### 1. Environment

Copy `.env.example` → `.env` at repo root:

```env
ARMORIQ_API_KEY=ak_live_...
MISTRAL_API_KEY=...
MISTRAL_MODEL=mistral-small-latest
NEXT_PUBLIC_API_URL=http://localhost:8000
# Optional: GITHUB_TOKEN=ghp_...  (higher GitHub API limits)
# Optional: SECBRIEF_STRICT_ARMORIQ=true  (fail closed if ArmorIQ errors)
```

### 2. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

If port 8000 is busy, use `--port 8001` and set `NEXT_PUBLIC_API_URL` accordingly.

### 3. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). If styles look broken, stop the dev server, delete `frontend/.next`, and run `npm run dev` again.

---

## Demo script (~2 min) — offline round

| Step | Action | Say this |
|------|--------|----------|
| 1 | **Code** tab → Load SQLi sample → **Audit code** | “We map to OWASP and CWE — not just chat.” |
| 2 | Point at compliance chips (OWASP, CWE, SOC2, ₹) | “Built for teams that need audit evidence.” |
| 3 | Enable **Attack-the-agent** → **Generate verified fix plan** | “Plan is signed first; then we inject an undeclared destructive step.” |
| 4 | Show **BLOCK** on `delete_all` | “Cryptography blocked it — not a better prompt.” |
| 5 | Intent receipt + **Export Monday-morning brief** | “Compliance artifact for SOC2-ready teams.” |
| 6 | *(Optional)* Demo Repos → Express.js deep scan | “Same pipeline for SARIF and real repos.” |

Full talking points: [PITCH.md](./PITCH.md)

---

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service status |
| GET | `/api/why-secbrief` | Comparison JSON (for slides / charts) |
| GET | `/api/demo-repos` | Curated GitHub repos |
| GET | `/api/sample-alert` | Sample npm audit text |
| POST | `/api/parse-upload` | SARIF or npm audit JSON file |
| POST | `/api/github/scan` | Deep repo scan (`deep_scan: true`) |
| POST | `/api/explain` | Plain-English alert explanation |
| POST | `/api/audit-code` | Code snippet vulnerability audit |
| POST | `/api/plan-fix` | Verified plan + intent receipt |
| POST | `/api/export-brief` | Markdown incident brief |
| GET | `/api/sessions/{email}` | Session history |

Legacy comparison aliases: `/api/why-intentseal`, `/api/why-patchproof`, `/api/why-vulnexplain`, `/api/why-luma`

---

## Project structure

```
backend/
  main.py              # FastAPI routes
  armoriq_service.py   # ArmorIQ session enforce + intent receipt
  llm_service.py       # Mistral + compliance fields
  github_service.py    # GitHub manifest scan
  scan_enricher.py     # Deep scan (workflows, heuristics)
  alert_parser.py      # SARIF / npm audit JSON
  db.py                # SQLite sessions
  armoriq.yaml         # Agent + policy config
frontend/
  src/app/page.tsx     # Main UI
```

---

## Deploy (optional)

| Service | Root | Notes |
|---------|------|-------|
| **Vercel** | `frontend/` | Set `NEXT_PUBLIC_API_URL` to your backend URL |
| **Railway / Render** | `backend/` | `uvicorn main:app --host 0.0.0.0 --port $PORT` · set `FRONTEND_ORIGIN` for CORS |

---

## Hackathon checklist

- [ ] `ARMORIQ_API_KEY` and `MISTRAL_API_KEY` in `.env`
- [ ] Backend on :8000, frontend on :3000
- [ ] Live demo: code audit → OWASP chips → attack-the-agent BLOCK
- [ ] Screenshot: briefing + blocked step + ArmorIQ audit
- [ ] 2-min demo video recorded
- [ ] Slides from [PPT_CONTENT.md](./PPT_CONTENT.md)
- [ ] Team details on [SUBMISSION.md](./SUBMISSION.md)

---

## Repos

- **SecBrief** — this hackathon project (publish as `secbrief` on GitHub)
- **VulnExplain** — your older repo (keep unchanged)

---

## License

Hackathon submission — ArmorIQ Track 2.
