---
title: SecBrief
emoji: 🛡️
colorFrom: yellow
colorTo: green
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# SecBrief

**Explain the risk. Enforce the fix.**

Security copilot for the **ArmorIQ Hackathon (Track 2)**: turn CVE/SARIF noise and vulnerable code into plain-English **security briefings** with **OWASP / CWE / SOC 2 / INR** mapping, then **cryptographically verified** remediation plans via ArmorIQ.

**Live demo:** use this Space URL. Set `ARMORIQ_API_KEY` and `MISTRAL_API_KEY` in **Settings → Variables**.

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

## Quick start (local)

### Prerequisites

- Python 3.11+
- Node.js 18+
- [ArmorIQ API key](https://platform.armoriq.ai)
- [Mistral API key](https://console.mistral.ai)

### Environment

Copy `.env.example` → `.env` at repo root:

```env
ARMORIQ_API_KEY=ak_live_...
MISTRAL_API_KEY=...
MISTRAL_MODEL=mistral-small-latest
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Run locally

```powershell
cd backend
.\.venv\Scripts\activate
python -m uvicorn main:app --reload --port 8000

cd frontend
npm install
npm run dev
```

Or Docker (same as HF): `docker build -t secbrief .` then `docker run -p 7860:7860 --env-file .env secbrief`

---

## Demo script (~2 min)

| Step | Action |
|------|--------|
| 1 | **Code** tab → SQLi sample → **Audit code** |
| 2 | **Attack-the-agent** → **Generate verified fix plan** |
| 3 | Show **BLOCK** on `delete_all` + intent receipt |

Full talking points: [PITCH.md](./PITCH.md)

---

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service status |
| GET | `/api/why-secbrief` | Comparison JSON |
| POST | `/api/github/scan` | Deep repo scan |
| POST | `/api/audit-code` | Code snippet audit |
| POST | `/api/plan-fix` | Verified plan + intent receipt |
| POST | `/api/export-brief` | Markdown incident brief |

---

## Project structure

```
backend/     # FastAPI + ArmorIQ + Mistral
frontend/    # Next.js UI (static export in Docker)
Dockerfile   # HF Space build
```

Deploy guide: [HF_DEPLOY.md](./HF_DEPLOY.md)
