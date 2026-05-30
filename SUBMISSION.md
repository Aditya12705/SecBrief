# ArmorIQ Hackathon — Submission (SecBrief)

| Field | Content |
|-------|---------|
| **Title** | **SecBrief** — Explain the risk. Enforce the fix. |
| **Track** | Track 2 — AI Agent for the Real World |
| **Integrations** | ArmorIQ SDK, Mistral API, GitHub API |
| **Tech Stack** | FastAPI, Next.js, SQLite, Tailwind CSS |

## Problem: The "Copy-Paste" Risk
Security alerts are dense and jargon-heavy. Developers often turn to generic LLMs for fixes, then copy-paste shell commands or code changes without any verification. This invites prompt-injection attacks and lacks any audit trail for compliance.

## Solution: SecBrief
SecBrief is a security-first agent workflow that bridges the gap between explanation and enforcement.

1. **Ingest:** Deep scan GitHub repos, upload SARIF/JSON reports, or audit code snippets.
2. **Brief:** Mistral AI explains risks in plain English, mapping findings to **OWASP Top 10**, **CWE**, and **SOC 2** controls, with an estimated **₹ financial impact**.
3. **Plan:** Generate a structured remediation plan.
4. **Enforce:** Use **ArmorIQ SDK** to sign the intent plan. Each step is enforced: **allow**, **hold**, or **block**.
5. **Prove:** Demonstrate **Attack-the-agent** defense where undeclared malicious steps (like `delete_all`) are cryptographically blocked.
6. **Export:** Generate a compliance-ready "Monday-morning incident brief" with cryptographic proofs.

## Track 2 Specific: The "Audit Vault"
Winning Track 2 requires demonstrating enterprise-grade reliability. SecBrief includes an **Audit Vault**—a persistent record of every remediation performed, complete with its **ArmorIQ Intent Receipt**. This allows security teams to verify that 100% of AI-driven fixes were compliant and authorized, providing a ready-made artifact for SOC2 audits.

## Enterprise Readiness Features
- **ArmorIQ Intent Proofs:** Every remediation plan generates a cryptographic hash and token.
- **Compliance Mapping:** Direct links to OWASP, CWE, and SOC2 controls on every briefing.
- **Multi-Agent Safety:** Support for ArmorIQ delegation tokens to restrict sub-agents to specific, safe actions.
- **Incident Brief Export:** Automated Markdown reporting with embedded safety proofs.

## Demo Flow
1. **GitHub Scan:** Scan a repo (e.g., Express.js) to see dependency risk mapping.
2. **Code Audit:** Paste vulnerable SQL code to get OWASP/CWE chips.
3. **Verified Plan:** Generate a fix plan with ArmorIQ session enforcement.
4. **Attack Demo:** Enable "Attack Mode" to show ArmorIQ blocking a `delete_all` step injected after the plan was signed.
5. **Export:** Download the incident brief.

## Repository
Project: **SecBrief**  
Built with Mistral Small Latest and ArmorIQ Python SDK.

---
*SecBrief: ChatGPT explains the CVE. SecBrief enforces the fix.*
