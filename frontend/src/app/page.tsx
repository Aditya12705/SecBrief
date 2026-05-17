"use client";

import { useCallback, useEffect, useState } from "react";
import { ChatPanel } from "@/components/ChatPanel";
import { Header } from "@/components/Header";
import { InputPanel } from "@/components/InputPanel";
import { WorkflowBar } from "@/components/WorkflowBar";
import {
  auditCode,
  explainAlert,
  exportBrief,
  fetchDemoRepos,
  fetchSampleAlert,
  parseUpload,
  planFix,
  scanGithub,
} from "@/lib/api";
import type {
  Analysis,
  ChatMessage,
  DemoRepo,
  InputMode,
  IntentReceipt,
  WorkflowStep,
} from "@/lib/types";

function uid() {
  return Math.random().toString(36).slice(2, 10);
}

function analysisFromRecord(a: Record<string, unknown>): Analysis {
  return {
    title: a.title as string | undefined,
    severity: a.severity as string | undefined,
    risk_score: a.risk_score as number | undefined,
    summary: a.summary as string | undefined,
    formatted: a.formatted as string | undefined,
    owasp_category: a.owasp_category as string | undefined,
    cwe_id: a.cwe_id as string | undefined,
    soc2_controls: a.soc2_controls as string[] | undefined,
    financial_impact_inr: a.financial_impact_inr as string | undefined,
  };
}

function analysisForMessage(a: Analysis) {
  return {
    title: a.title,
    severity: a.severity,
    risk_score: a.risk_score,
    summary: a.summary,
    owasp_category: a.owasp_category,
    cwe_id: a.cwe_id,
    soc2_controls: a.soc2_controls,
    financial_impact_inr: a.financial_impact_inr,
  };
}

export default function Home() {
  const [email, setEmail] = useState("dev@example.com");
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [mode, setMode] = useState<InputMode>("github");
  const [repoUrl, setRepoUrl] = useState("https://github.com/expressjs/express");
  const [alertText, setAlertText] = useState("");
  const [codeText, setCodeText] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [demoRepos, setDemoRepos] = useState<DemoRepo[]>([]);
  const [workflow, setWorkflow] = useState<WorkflowStep>("input");
  const [scanSummary, setScanSummary] = useState<string | undefined>();
  const [contextText, setContextText] = useState("");
  const [simulateAttack, setSimulateAttack] = useState(false);
  const [useDelegation, setUseDelegation] = useState(false);
  const [lastAnalysis, setLastAnalysis] = useState<Analysis | null>(null);
  const [lastPlan, setLastPlan] = useState<{ goal: string; steps: unknown[] } | null>(null);
  const [lastDecisions, setLastDecisions] = useState<ChatMessage["decisions"]>([]);
  const [lastReceipt, setLastReceipt] = useState<IntentReceipt | null>(null);

  useEffect(() => {
    fetchDemoRepos().then((d) => setDemoRepos(d.repos)).catch(() => {});
  }, []);

  const addMessage = useCallback((msg: Omit<ChatMessage, "id">) => {
    setMessages((m) => [...m, { ...msg, id: uid() }]);
  }, []);

  const loadSample = useCallback(async () => {
    const j = await fetchSampleAlert();
    setAlertText(j.text);
    setContextText(j.text);
    setMode("paste");
    setWorkflow("input");
  }, []);

  const handleUpload = async (file: File) => {
    setLoading(true);
    try {
      const parsed = await parseUpload(file);
      setAlertText(parsed.alert_text);
      setContextText(parsed.alert_text);
      setMode("paste");
      addMessage({
        role: "assistant",
        text: `Parsed **${parsed.title}** (${parsed.format}, ${parsed.finding_count} finding(s)).`,
      });
    } catch (e) {
      addMessage({
        role: "assistant",
        text: e instanceof Error ? e.message : "Upload failed",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleScanRepo = async (url: string) => {
    if (!url.trim()) return;
    setLoading(true);
    setWorkflow("analyze");
    setRepoUrl(url);
    addMessage({ role: "user", text: `Deep scan: ${url}` });
    try {
      const j = await scanGithub(email, url, sessionId, true);
      setSessionId(j.session_id);
      const scan = j.scan as {
        full_name: string;
        manifests_found: string[];
        heuristic_findings: { signal: string; note: string; severity: string }[];
        deep_scan?: boolean;
      };
      const analysis = analysisFromRecord(j.analysis as Record<string, unknown>);
      setContextText((j.scan as { scan_context: string }).scan_context || "");
      setLastAnalysis(analysis);
      setScanSummary(
        `Deep scan ${scan.full_name} · ${scan.manifests_found.length} manifest(s) · ${scan.heuristic_findings.length} signal(s)`
      );
      addMessage({
        role: "assistant",
        text: analysis.formatted || "Scan complete.",
        analysis: analysisForMessage(analysis),
        meta: j.analysis_source,
      });
      setWorkflow("plan");
    } catch (e) {
      addMessage({
        role: "assistant",
        text: e instanceof Error ? e.message : "GitHub scan failed",
      });
      setWorkflow("input");
    } finally {
      setLoading(false);
    }
  };

  const handleExplain = async () => {
    if (!alertText.trim()) return;
    setLoading(true);
    setWorkflow("analyze");
    setContextText(alertText);
    addMessage({ role: "user", text: "Explain this security alert in plain English" });
    try {
      const j = await explainAlert(email, alertText, sessionId);
      setSessionId(j.session_id);
      const a = analysisFromRecord(j.analysis as Record<string, unknown>);
      setLastAnalysis(a);
      addMessage({
        role: "assistant",
        text: j.explanation || a.formatted || "",
        analysis: analysisForMessage(a),
        meta: j.source,
      });
      setWorkflow("plan");
    } catch (e) {
      addMessage({
        role: "assistant",
        text: e instanceof Error ? e.message : "Explain failed",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAuditCode = async () => {
    if (!codeText.trim()) return;
    setLoading(true);
    setWorkflow("analyze");
    setContextText(codeText);
    addMessage({ role: "user", text: "Audit this code snippet for vulnerabilities" });
    try {
      const j = await auditCode(email, codeText, sessionId);
      setSessionId(j.session_id);
      const a = analysisFromRecord(j.analysis as Record<string, unknown>);
      setLastAnalysis(a);
      addMessage({
        role: "assistant",
        text: j.explanation || a.formatted || "",
        analysis: analysisForMessage(a),
        meta: j.source,
      });
      setWorkflow("plan");
    } catch (e) {
      addMessage({
        role: "assistant",
        text: e instanceof Error ? e.message : "Code audit failed",
      });
    } finally {
      setLoading(false);
    }
  };

  const handlePlanFix = async () => {
    const ctx = contextText || alertText || codeText;
    if (!ctx.trim()) return;
    setLoading(true);
    setWorkflow("enforce");
    addMessage({
      role: "user",
      text: simulateAttack
        ? "Generate plan + simulate prompt-injection attack (delete_all)"
        : "Generate ArmorIQ policy-checked remediation plan",
    });
    try {
      const j = await planFix(email, ctx, {
        session_id: sessionId,
        simulate_attack: simulateAttack,
        use_delegation_demo: useDelegation,
      });
      setSessionId(j.session_id);
      setLastPlan(j.plan);
      setLastDecisions(j.decisions);
      setLastReceipt(j.intent_receipt);

      const steps = (j.plan?.steps || [])
        .map((s, i) => `${i + 1}. ${s.action} — ${s.description || ""}`)
        .join("\n");
      let extra = "";
      if (j.delegation_demo?.length) {
        extra =
          "\n\n**Delegation:** " + j.delegation_demo.map((d) => d.message).join(" ");
      }
      addMessage({
        role: "assistant",
        text: `## Remediation plan\n**Goal:** ${j.plan?.goal}\n\n${steps}\n\n**${j.summary}**${extra}`,
        decisions: j.decisions,
        receipt: j.intent_receipt,
        meta: j.armoriq_live ? "verified" : "demo",
      });
    } catch (e) {
      addMessage({
        role: "assistant",
        text: e instanceof Error ? e.message : "Plan failed",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const md = await exportBrief({
        email,
        session_id: sessionId,
        alert_text: contextText || alertText,
        analysis: lastAnalysis,
        plan: lastPlan,
        decisions: lastDecisions || [],
        receipt: lastReceipt,
      });
      const blob = new Blob([md], { type: "text/markdown" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `secbrief-brief-${Date.now()}.md`;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch {
      addMessage({ role: "assistant", text: "Export failed — generate a plan first." });
    }
  };

  const onSelectDemo = (repo: DemoRepo) => {
    setMode("github");
    handleScanRepo(repo.url);
  };

  return (
    <main className="min-h-screen gradient-hero flex flex-col">
      <Header />

      <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 py-6 flex-1 flex flex-col gap-6">
        <section className="text-center sm:text-left">
          <h2 className="text-2xl sm:text-3xl font-bold text-white max-w-xl leading-tight">
            Explain the <span className="text-amber-400">risk</span>. Enforce the{" "}
            <span className="text-emerald-400">fix</span>.
          </h2>
          <p className="text-slate-500 text-sm mt-2 max-w-lg">
            OWASP-mapped briefings, code audits, and ArmorIQ-verified remediation — built for
            Track 2.
          </p>
        </section>

        <WorkflowBar current={workflow} />

        <div className="grid lg:grid-cols-2 gap-6 flex-1 min-h-0">
          <section className="glass rounded-2xl p-5 flex flex-col">
            <InputPanel
              mode={mode}
              onModeChange={setMode}
              email={email}
              onEmailChange={setEmail}
              repoUrl={repoUrl}
              onRepoUrlChange={setRepoUrl}
              alertText={alertText}
              onAlertTextChange={setAlertText}
              codeText={codeText}
              onCodeTextChange={setCodeText}
              demoRepos={demoRepos}
              onSelectDemo={onSelectDemo}
              onLoadSample={loadSample}
              onScanRepo={() => handleScanRepo(repoUrl)}
              onExplain={handleExplain}
              onAuditCode={handleAuditCode}
              onPlanFix={handlePlanFix}
              onUploadFile={handleUpload}
              loading={loading}
              scanSummary={scanSummary}
              simulateAttack={simulateAttack}
              onSimulateAttackChange={setSimulateAttack}
              useDelegation={useDelegation}
              onUseDelegationChange={setUseDelegation}
              onExportBrief={handleExport}
              canExport={!!(lastPlan || lastDecisions?.length)}
            />
          </section>

          <section className="glass rounded-2xl p-5 flex flex-col">
            <h2 className="text-sm font-semibold text-slate-400 mb-3">Security briefing</h2>
            <ChatPanel messages={messages} loading={loading} />
          </section>
        </div>

        <footer className="text-center text-[11px] text-slate-600 pb-4">
          SecBrief
          {sessionId && (
            <span className="text-slate-700 font-mono"> · {sessionId.slice(0, 8)}</span>
          )}
          {/* ADD: View Team Dashboard link — appears after session is active */}
          {sessionId && (
            <div style={{ marginTop: "0.6rem" }}>
              <a
                href="/pulse"
                style={{
                  display: "inline-block",
                  fontSize: "0.72rem",
                  color: "#34d399",
                  textDecoration: "none",
                  padding: "0.3rem 0.8rem",
                  borderRadius: "8px",
                  border: "1px solid rgba(52,211,153,0.3)",
                  background: "rgba(52,211,153,0.07)",
                  transition: "background 0.2s",
                }}
              >
                View team dashboard →
              </a>
            </div>
          )}
        </footer>
      </div>
    </main>
  );
}
