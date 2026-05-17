# SecBrief — Presenter cheat sheet

Use this while demoing or answering judges. The **website stays clean**; say comparison lines out loud or show [PPT_CONTENT.md](./PPT_CONTENT.md) slides.

---

## One-liner

**ChatGPT explains the CVE. SecBrief enforces the fix.**

Tagline on screen: **Explain the risk. Enforce the fix.**

---

## 30-second elevator pitch

Developers get hundreds of security alerts they do not understand. AI copilots *suggest* fixes — including dangerous commands — with no proof and no compliance mapping.

**SecBrief** ingests SARIF, npm audit JSON, deep-scans a GitHub repo, or audits a code snippet. It explains the risk in plain English with **OWASP, CWE, SOC 2, and ₹ impact** — then builds a remediation plan where **every step is cryptographically verified by ArmorIQ** — allow, hold, or block — with an audit trail.

Turn on **Attack-the-agent** to show a malicious `delete_all` step **blocked** because it was never part of the signed plan.

---

## Mistral vs ArmorIQ (if judges ask “why two APIs?”)

| | Mistral | ArmorIQ |
|---|---------|---------|
| **Role** | Brain — language & planning | Bouncer — enforcement & audit |
| **Does** | Explain CVEs, OWASP map, draft fix steps | Sign intent plan, allow/block each step |
| **Does not** | Guarantee safety | Write friendly explanations |

**Together:** Mistral proposes → ArmorIQ enforces.

---

## vs ChatGPT / Gemini / Enterprise Copilot

| | Generic AI / Copilot | SecBrief |
|---|----------------------|----------|
| **Scope** | Anything | Security workflow only |
| **Output** | Chat text | **Security briefing** + verified step list |
| **Compliance** | Ad-hoc prose | OWASP / CWE / SOC2 / INR on every briefing |
| **Trust** | Trust the model | Trust the **signed plan** |
| **Prompt injection** | Can change tool behavior | Undeclared steps **fail** (`delete_all` demo) |
| **Audit** | Chat logs | Plan hash + [platform.armoriq.ai](https://platform.armoriq.ai) |
| **Input** | Paste chat | SARIF, npm JSON, GitHub scan, code audit |

---

## Live demo script (~2 min) — offline optimized

| Step | Action | Say this |
|------|--------|----------|
| 1 | **Code** tab → Load SQLi sample → **Audit code** | “We map to OWASP and CWE — not just chat.” |
| 2 | Point at compliance chips (OWASP, CWE, SOC2, ₹) | “Built for teams that need audit evidence, not jargon.” |
| 3 | Enable **Attack-the-agent** → **Generate verified fix plan** | “The LLM plan is signed first; then we try to run an extra destructive step.” |
| 4 | Point at **BLOCK** on `delete_all` | “Not in the signed plan — cryptography blocked it, not a prompt.” |
| 5 | Show intent receipt (plan hash) | “This is the compliance artifact enterprises need.” |
| 6 | **Export Monday-morning brief** + ArmorIQ dashboard | “Full audit trail for SOC2-ready teams.” |
| 7 | *(Optional)* Demo Repos → Express.js | “Same pipeline for SARIF and real repos.” |

**Close:** *“ChatGPT explains the CVE. SecBrief enforces the fix.”*

---

## Track 2 fit (one sentence)

Real-world alert fatigue, non-expert users, **measurable** safety via ArmorIQ SDK session enforcement, plus compliance mapping enterprises expect — in one demo flow.

---

## Troubleshooting during demo

| Issue | Fix |
|-------|-----|
| Unstyled white page | Stop `npm run dev`, delete `frontend/.next`, restart |
| Port 8000 error | Kill old process or use `--port 8001` |
| “demo” on plan steps | Set `ARMORIQ_API_KEY` in `.env`, restart backend |
| GitHub rate limit | Add `GITHUB_TOKEN` to `.env` |

---

## Links

- App: http://localhost:3000  
- API docs: http://localhost:8000/docs  
- Comparison JSON: http://localhost:8000/api/why-secbrief  
- ArmorIQ dashboard: https://platform.armoriq.ai  
- Slide copy: [PPT_CONTENT.md](./PPT_CONTENT.md)
