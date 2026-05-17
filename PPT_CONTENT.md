# SecBrief — PowerPoint slide copy

Copy-paste into your deck. **Do not put comparison walls on the website** — the app is product-only.

---

## Slide 1 — Title

**SecBrief**  
Explain the risk. Enforce the fix.

ArmorIQ Hackathon · Track 2 — AI Agent for the Real World

*[Team name] · [College] · [Team ID]*

---

## Slide 2 — Problem

- Developers receive hundreds of CVEs, SARIF findings, and Dependabot alerts
- Reports are jargon-heavy (CVSS, CWE, GHSA)
- Small teams have no dedicated AppSec
- **New risk:** AI copilots *suggest* fixes with **no enforcement** and **no audit proof**
- Indian startups need **understandable risk + ₹ impact**, not just CVE IDs

---

## Slide 3 — Solution

**SecBrief** — security-only briefing agent:

1. **Ingest** — SARIF, npm audit JSON, GitHub deep scan, code snippet, or paste
2. **Brief** — plain English, severity, risk score, OWASP / CWE / SOC 2 / ₹
3. **Plan** — structured remediation steps
4. **Enforce** — ArmorIQ signs the plan; each step is allow / block / hold
5. **Audit** — intent receipt + platform.armoriq.ai + exportable brief

---

## Slide 4 — One-liner

# ChatGPT explains the CVE.
# SecBrief enforces the fix.

---

## Slide 5 — Why not ChatGPT / Gemini / Enterprise Copilot?

| Dimension | Generic AI / Copilot | SecBrief |
|-----------|----------------------|----------|
| **Purpose** | General chat | Vulnerability briefing workflow only |
| **Output** | Text suggestions | Plain English briefing + verified step list |
| **Compliance** | Optional prose | OWASP + CWE + SOC2 + INR on every briefing |
| **Remediation** | Suggested commands | Signed intent plan + enforce per step |
| **Prompt injection** | Malicious prompts can steer tools | Undeclared steps fail (`delete_all` demo) |
| **Audit** | Chat history | Cryptographic plan hash + ArmorIQ dashboard |
| **Input** | Manual paste | SARIF, npm JSON, GitHub deep scan, code audit |
| **Multi-agent** | Shared credentials common | Delegation with scoped sub-tokens |

**Optional bullets:**
- Code snippet audit tab
- Attack-the-agent live BLOCK
- Monday-morning compliance export
- Per-user session history

---

## Slide 6 — Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│ SARIF /     │    │ Mistral API  │    │ ArmorIQ SDK     │    │ User         │
│ code / repo │───▶│ Brief +      │───▶│ start_plan +    │───▶│ Briefing +   │
│             │    │ OWASP map    │    │ enforce_sdk     │    │ allow/block  │
└─────────────┘    └──────────────┘    └─────────────────┘    └──────────────┘
                                              │
                                              ▼
                                    platform.armoriq.ai (audit)
```

| Layer | Tech |
|-------|------|
| Frontend | Next.js 14, Tailwind |
| Backend | FastAPI, SQLite |
| LLM | Mistral (`mistral-small-latest`) |
| Security | ArmorIQ SDK, `armoriq.yaml`, CSRG tokens |
| Scan | GitHub API + deep scan (workflows, Dependabot, heuristics) |

---

## Slide 7 — Mistral + ArmorIQ (judge Q&A)

| | Mistral | ArmorIQ |
|---|---------|---------|
| **Job** | Brain — explain & plan | Bouncer — sign & enforce |
| **Output** | Plain English, OWASP map, steps | Allow / block / hold per step |
| **Trust model** | Probabilistic (LLM) | Cryptographic (CSRG + policy) |

**We use both because explanation needs an LLM; safety needs intent verification.**

---

## Slide 8 — Live demo flow

1. **Code** tab → SQLi sample → **Audit code** → show OWASP/CWE/INR chips  
2. Enable **Attack-the-agent** → **Generate verified fix plan**  
3. Show **BLOCK** on `delete_all` (not in signed plan)  
4. Intent receipt — plan hash  
5. **platform.armoriq.ai** audit screenshot  
6. Export Monday-morning brief  

*Backup path: Demo Repos → expressjs/express deep scan*

*Screen recording: [your URL]*

---

## Slide 9 — Impact

- **Who:** Student devs, SMBs, anyone fixing Dependabot without AppSec
- **Time:** CVE understanding: hours → minutes
- **Safety:** Blocks undeclared / destructive AI-suggested steps
- **Compliance:** OWASP/SOC2/INR mapping + exportable brief for audit readiness

---

## Slide 10 — Track 2 fit

- Real-world problem (alert fatigue + AI remediation risk)
- Non-expert audience (plain English briefings)
- AI agent with **deep ArmorIQ integration** (`start_plan`, `enforce_sdk`, audit)
- Demo-ready MVP with **measurable** allow/block outcomes

---

## Slide 11 — Thank you / contact

**SecBrief** — Explain the risk. Enforce the fix.

- Demo: *[deployed URL]*
- Repo: *[GitHub URL — e.g. github.com/you/secbrief]*
- ArmorIQ audit screenshot attached

---

## Speaker notes — 30 sec (read verbatim)

> Developers drown in CVE jargon, and ChatGPT only suggests fixes — it cannot prove they are safe. SecBrief ingests SARIF or audits your code, explains the risk in plain English with OWASP and SOC 2 mapping, estimates impact in rupees, then ArmorIQ cryptographically verifies every remediation step. In our demo we inject a malicious delete-all command after signing the plan — ArmorIQ blocks it because it was never declared. ChatGPT explains the CVE; SecBrief enforces the fix.

---

## Optional: live data for charts

```http
GET http://localhost:8000/api/why-secbrief
```

Returns JSON comparison table for auto-generated slides.

---

## Pre-demo checklist

- [ ] `.env` has valid `ARMORIQ_API_KEY` + `MISTRAL_API_KEY`
- [ ] Backend :8000, frontend :3000 (hard refresh browser)
- [ ] Code audit → compliance chips visible
- [ ] Attack-the-agent tested once before recording
- [ ] ArmorIQ dashboard logged in with demo email
- [ ] Screenshot folder: briefing + BLOCK step + audit log
