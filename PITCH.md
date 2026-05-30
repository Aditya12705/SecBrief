# SecBrief — Winning Pitch Script & Demo Guide

## The Hook (Start here)
*(Slow, serious tone)*
"It’s 3:00 AM on a Monday. Your lead developer is exhausted. A critical SQL injection alert just hit the production server. 

He does what any modern developer does: he copies the alert into ChatGPT. The AI gives him a fix. It looks perfect. He copies, pastes, and hits 'Deploy.' 

**Ten seconds later, your entire customer database is gone.** 

The AI wasn't malicious—but the prompt was. A simple injection attack hidden in the alert text tricked the AI into adding a `drop database` command to the 'fix.'

Generic AI is the world's best explainer, but it's the world's worst gatekeeper. 

**This is why we built SecBrief.**"

---

## The Solution
"SecBrief doesn't just explain the risk; it cryptographically enforces the fix. By integrating the **ArmorIQ SDK**, we’ve created a 'Safety Sandbox' for remediation. 

When our Mistral-powered brain generates a fix, it signs a **Signed Intent Plan**. If a prompt-injection attack tries to sneak in a destructive command—like `delete_all`—ArmorIQ recognizes it wasn't part of the original intent and **blocks it instantly**.

We don't ask you to trust the AI. We ask you to trust the **Signed Receipt**."

---

## 30-Second Elevator Pitch
"SecBrief is a security-first agent that ingests SARIF, npm audit, or GitHub scans. It explains risks in plain English with **OWASP, CWE, and SOC 2 mapping**, then builds a remediation plan where every step is **cryptographically verified by ArmorIQ**. 

**ChatGPT explains the CVE. SecBrief enforces the fix.**"

---

## Live Demo Script (2 Minutes)

| Step | Action | Say this |
|------|--------|----------|
| **1. Ingest** | Click **"Load Sample"** in Alert tab | "We start by ingesting a standard security report." |
| **2. Brief** | Click **"Explain Alert"** | "Mistral translates jargon into plain English with SOC2 and ₹ impact mapping." |
| **3. Attack** | Toggle **"Attack Mode"** ON → **"Generate Verified Fix"** | "Now, we simulate a prompt-injection attack trying to wipe our data." |
| **4. Block** | Point to the **RED BLOCK** on `delete_all` | "ArmorIQ saw the malicious step. It wasn't in the signed plan, so it was blocked instantly." |
| **5. Proof** | Show the **Intent Receipt** card | "This is our audit trail. A cryptographic proof of every allowed action." |
| **6. Export** | Click **"Export Incident Brief"** | "We generate a SOC2-ready brief for your security team in one click." |

---

## Key Differentiators (For Q&A)
- **Safety First:** We use ArmorIQ CSRG (Signed Plans) to prevent tool-misuse.
- **Compliance Ready:** Real-time mapping to OWASP/CWE/SOC2.
- **Identity Bound:** Every fix is tied to a user email via `armoriq.for_user()`.
- **Audit Trail:** Full session history visible on [platform.armoriq.ai](https://platform.armoriq.ai).

---

## Track 2 Fit
SecBrief solves **Alert Fatigue** and **AI Safety** for non-expert developers using a production-grade security SDK (ArmorIQ) and the most efficient European LLM (Mistral).
