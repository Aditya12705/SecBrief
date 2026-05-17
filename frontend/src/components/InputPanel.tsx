"use client";

import { useRef } from "react";
import type { DemoRepo, InputMode } from "@/lib/types";

const TABS: { id: InputMode; label: string; icon: string }[] = [
  { id: "github", label: "Repo", icon: "⌘" },
  { id: "code", label: "Code", icon: "{}" },
  { id: "paste", label: "Alert", icon: "📋" },
  { id: "demo", label: "Demo", icon: "★" },
];

const SAMPLE_VULN_CODE = `// SQL injection example
const userId = req.query.id;
const sql = "SELECT * FROM users WHERE id = " + userId;
db.query(sql);`;

export function InputPanel({
  mode,
  onModeChange,
  email,
  onEmailChange,
  repoUrl,
  onRepoUrlChange,
  alertText,
  onAlertTextChange,
  codeText,
  onCodeTextChange,
  demoRepos,
  onSelectDemo,
  onLoadSample,
  onScanRepo,
  onExplain,
  onAuditCode,
  onPlanFix,
  onUploadFile,
  loading,
  scanSummary,
  simulateAttack,
  onSimulateAttackChange,
  useDelegation,
  onUseDelegationChange,
  onExportBrief,
  canExport,
}: {
  mode: InputMode;
  onModeChange: (m: InputMode) => void;
  email: string;
  onEmailChange: (v: string) => void;
  repoUrl: string;
  onRepoUrlChange: (v: string) => void;
  alertText: string;
  onAlertTextChange: (v: string) => void;
  codeText: string;
  onCodeTextChange: (v: string) => void;
  demoRepos: DemoRepo[];
  onSelectDemo: (repo: DemoRepo) => void;
  onLoadSample: () => void;
  onScanRepo: () => void;
  onExplain: () => void;
  onAuditCode: () => void;
  onPlanFix: () => void;
  onUploadFile: (file: File) => void;
  loading: boolean;
  scanSummary?: string;
  simulateAttack: boolean;
  onSimulateAttackChange: (v: boolean) => void;
  useDelegation: boolean;
  onUseDelegationChange: (v: boolean) => void;
  onExportBrief: () => void;
  canExport: boolean;
}) {
  const fileRef = useRef<HTMLInputElement>(null);

  return (
    <div className="flex flex-col gap-4 h-full">
      <div className="flex rounded-xl bg-slate-900/80 p-1 border border-slate-800">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => onModeChange(tab.id)}
            className={`flex-1 py-2 px-2 rounded-lg text-xs sm:text-sm font-medium transition ${
              mode === tab.id
                ? "bg-emerald-600/90 text-white shadow"
                : "text-slate-500 hover:text-slate-300"
            }`}
          >
            <span className="mr-1 opacity-70">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      <label className="text-xs text-slate-500">
        Email <span className="text-slate-600">(ArmorIQ audit identity)</span>
      </label>
      <input
        className="w-full bg-slate-900/60 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
        value={email}
        onChange={(e) => onEmailChange(e.target.value)}
        placeholder="you@company.com"
      />

      {mode === "github" && (
        <>
          <label className="text-xs text-slate-500">GitHub repository URL</label>
          <input
            className="w-full bg-slate-900/60 border border-slate-700 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
            value={repoUrl}
            onChange={(e) => onRepoUrlChange(e.target.value)}
            placeholder="https://github.com/owner/repo"
          />
          <p className="text-[11px] text-slate-600">
            Deep scan: manifests + security workflows + Dependabot + secret-pattern signals.
          </p>
          <button
            type="button"
            onClick={onScanRepo}
            disabled={loading || !repoUrl.trim()}
            className="w-full py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-sm font-semibold disabled:opacity-40 transition"
          >
            Deep scan repository
          </button>
        </>
      )}

      {mode === "code" && (
        <>
          <label className="text-xs text-slate-500">Code snippet to audit</label>
          <textarea
            className="flex-1 min-h-[180px] w-full bg-slate-900/60 border border-slate-700 rounded-lg px-3 py-2 text-xs font-mono resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
            value={codeText}
            onChange={(e) => onCodeTextChange(e.target.value)}
            placeholder="Paste vulnerable code…"
          />
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => onCodeTextChange(SAMPLE_VULN_CODE)}
              className="px-3 py-2 rounded-lg border border-slate-600 text-xs hover:bg-slate-800"
            >
              Load SQLi sample
            </button>
            <button
              type="button"
              onClick={onAuditCode}
              disabled={loading || !codeText.trim()}
              className="px-3 py-2 rounded-lg bg-emerald-600/90 text-xs font-medium disabled:opacity-40"
            >
              Audit code
            </button>
          </div>
        </>
      )}

      {mode === "paste" && (
        <>
          <label className="text-xs text-slate-500">
            Vulnerability report or upload SARIF / npm audit JSON
          </label>
          <input
            ref={fileRef}
            type="file"
            accept=".json,.sarif,.txt"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) onUploadFile(f);
              e.target.value = "";
            }}
          />
          <textarea
            className="flex-1 min-h-[180px] w-full bg-slate-900/60 border border-slate-700 rounded-lg px-3 py-2 text-xs font-mono resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
            value={alertText}
            onChange={(e) => onAlertTextChange(e.target.value)}
            placeholder="Paste npm audit, Snyk, CVE text… or upload SARIF/JSON"
          />
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => fileRef.current?.click()}
              className="px-3 py-2 rounded-lg border border-indigo-600/50 text-xs text-indigo-300 hover:bg-indigo-950/40"
            >
              Upload SARIF / JSON
            </button>
            <button
              type="button"
              onClick={onLoadSample}
              className="px-3 py-2 rounded-lg border border-slate-600 text-xs hover:bg-slate-800"
            >
              Load sample
            </button>
            <button
              type="button"
              onClick={onExplain}
              disabled={loading || !alertText.trim()}
              className="px-3 py-2 rounded-lg bg-emerald-600/90 text-xs font-medium disabled:opacity-40"
            >
              Explain alert
            </button>
          </div>
        </>
      )}

      {mode === "demo" && (
        <div className="space-y-2 flex-1 overflow-y-auto">
          <p className="text-xs text-slate-500">One-click deep scan — curated repos</p>
          {demoRepos.map((repo) => (
            <button
              key={repo.url}
              type="button"
              onClick={() => onSelectDemo(repo)}
              disabled={loading}
              className="w-full text-left p-3 rounded-xl border border-slate-800 hover:border-emerald-500/40 hover:bg-slate-900/80 transition disabled:opacity-50"
            >
              <div className="flex justify-between items-start gap-2">
                <span className="font-medium text-sm text-slate-200">{repo.label}</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                  {repo.stack}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-1">{repo.why}</p>
            </button>
          ))}
        </div>
      )}

      {scanSummary && (
        <p className="text-xs text-emerald-400/80 bg-emerald-950/30 border border-emerald-800/30 rounded-lg px-3 py-2">
          {scanSummary}
        </p>
      )}

      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3 space-y-2">
        <p className="text-[10px] uppercase tracking-wide text-slate-500 font-semibold">
          Enforcement options
        </p>
        <label className="flex items-start gap-2 text-xs text-slate-400 cursor-pointer">
          <input
            type="checkbox"
            checked={simulateAttack}
            onChange={(e) => onSimulateAttackChange(e.target.checked)}
            className="mt-0.5 rounded border-slate-600"
          />
          <span>
            <strong className="text-red-400">Attack-the-agent</strong> — inject{" "}
            <code className="text-slate-500">delete_all</code> after signing (proves injection
            block)
          </span>
        </label>
        <label className="flex items-start gap-2 text-xs text-slate-400 cursor-pointer">
          <input
            type="checkbox"
            checked={useDelegation}
            onChange={(e) => onUseDelegationChange(e.target.checked)}
            className="mt-0.5 rounded border-slate-600"
          />
          <span>
            <strong className="text-indigo-400">Delegation demo</strong> — scoped sub-agent token
          </span>
        </label>
      </div>

      <div className="mt-auto pt-2 border-t border-slate-800 space-y-2">
        <button
          type="button"
          onClick={onPlanFix}
          disabled={loading || (!alertText.trim() && !codeText.trim() && !scanSummary)}
          className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-sm font-semibold disabled:opacity-40 transition"
        >
          Generate verified fix plan
        </button>
        <button
          type="button"
          onClick={onExportBrief}
          disabled={!canExport}
          className="w-full py-2 rounded-lg border border-slate-600 text-xs text-slate-400 hover:text-slate-200 hover:border-slate-500 disabled:opacity-30 transition"
        >
          Export Monday-morning brief (Markdown)
        </button>
      </div>
    </div>
  );
}
