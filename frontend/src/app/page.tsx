"use client";

import { useCallback, useEffect, useState } from "react";
import { ChatPanel } from "@/components/ChatPanel";
import { Header } from "@/components/Header";
import { LandingPage } from "@/components/LandingPage";
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
  const [history, setHistory] = useState<{ id: string; title: string; date: string; status: string }[]>([]);
  const [showApp, setShowApp] = useState(false);

  useEffect(() => {
    fetchDemoRepos().then((d) => setDemoRepos(d.repos)).catch(() => {});
    // Load simple history from local storage for "Audit Vault" demo
    const saved = localStorage.getItem("secbrief_vault");
    if (saved) setHistory(JSON.parse(saved));
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

      // Add to Audit Vault history
      const newEntry = {
        id: j.session_id || uid(),
        title: j.plan?.goal || "Remediation Plan",
        date: new Date().toLocaleTimeString(),
        status: j.armoriq_live ? "Live Verified" : "Demo Mode",
      };
      const updatedHistory = [newEntry, ...history].slice(0, 5);
      setHistory(updatedHistory);
      localStorage.setItem("secbrief_vault", JSON.stringify(updatedHistory));

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
    <main className="min-h-screen gradient-hero flex flex-col selection:bg-emerald-500/30">
      {!showApp ? (
        <LandingPage onStart={() => setShowApp(true)} />
      ) : (
        <>
          <Header />

          <div className="max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6 flex-1 flex flex-col gap-6 animate-in fade-in duration-700">
            <section className="text-center sm:text-left flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
          <div>
            <h2 className="text-2xl sm:text-4xl font-extrabold text-white max-w-xl leading-tight tracking-tight">
              Explain the <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-orange-500">risk</span>. <br className="hidden sm:block" />
              Enforce the <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-teal-500">fix</span>.
            </h2>
            <p className="text-slate-400 text-sm mt-3 max-w-lg font-medium">
              Enterprise-grade security briefings and ArmorIQ-verified remediation plans for Track 2.
            </p>
          </div>
          <div className="flex items-center gap-3 bg-slate-900/50 p-2 rounded-2xl border border-slate-800/50 backdrop-blur-sm self-start sm:self-auto">
            <div className="flex flex-col items-end px-2">
              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Live Network</span>
              <span className="text-xs text-emerald-400 font-mono font-bold">ARMORIQ_LIVE</span>
            </div>
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            </div>
          </div>
        </section>

        <WorkflowBar current={workflow} />

        <div className="grid lg:grid-cols-12 gap-6 flex-1 min-h-0">
          <section className="lg:col-span-4 glass rounded-2xl p-5 flex flex-col gap-6 overflow-y-auto">
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

            {history.length > 0 && (
              <div className="pt-6 border-t border-slate-800">
                <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3 flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                  Audit Vault (Recent)
                </h3>
                <div className="space-y-2">
                  {history.map((h) => (
                    <div key={h.id} className="p-2 rounded-lg bg-slate-900/40 border border-slate-800 text-[10px] flex items-center justify-between group hover:border-emerald-500/30 transition-colors">
                      <div className="truncate pr-2">
                        <p className="text-slate-300 font-medium truncate">{h.title}</p>
                        <p className="text-slate-600">{h.date} · {h.id.slice(0, 8)}</p>
                      </div>
                      <button 
                        onClick={() => {
                          // In a real app, this would fetch session. 
                          // For demo, we just show a toast/message.
                          addMessage({ role: "system", text: `Vault Restore: Session ${h.id.slice(0, 8)} loaded into context.` });
                        }}
                        className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 font-bold shrink-0 transition-colors"
                      >
                        Open
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>

          <section className="lg:col-span-8 glass rounded-2xl p-5 flex flex-col min-h-[500px]">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-slate-400">Security briefing</h2>
              <div className="flex items-center gap-2">
                <div className="flex -space-x-1">
                  <div className="w-5 h-5 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-[8px] text-slate-400" title="Mistral AI">M</div>
                  <div className="w-5 h-5 rounded-full bg-emerald-900 border border-emerald-700 flex items-center justify-center text-[8px] text-emerald-400" title="ArmorIQ SDK">A</div>
                </div>
                <span className="text-[10px] text-slate-600 font-medium">Hybrid Intelligence Active</span>
              </div>
            </div>
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
      </>
      )}
    </main>
  );
}
