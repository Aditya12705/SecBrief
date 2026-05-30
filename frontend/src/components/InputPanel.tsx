"use client";

import { useRef } from "react";
import type { DemoRepo, InputMode } from "@/lib/types";

const TABS: { id: InputMode; label: string; icon: string }[] = [
  { id: "github", label: "Repo", icon: "⌘" },
  { id: "code", label: "Code", icon: "{}" },
  { id: "paste", label: "Alert", icon: "📋" },
  { id: "demo", label: "Demo", icon: "★" },
  { id: "scanner", label: "Scanner", icon: "🔍" },
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
  scanMode,
  setScanMode,
  scanEco,
  setScanEco,
  scanPkgText,
  setScanPkgText,
  ctrImage,
  setCtrImage,
  ctrSbom,
  setCtrSbom,
  scanLoading,
  scanResult,
  scanErr,
  onPkgScan,
  onCtrScan,
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
  scanMode: "package" | "container";
  setScanMode: (v: "package" | "container") => void;
  scanEco: string;
  setScanEco: (v: string) => void;
  scanPkgText: string;
  setScanPkgText: (v: string) => void;
  ctrImage: string;
  setCtrImage: (v: string) => void;
  ctrSbom: string;
  setCtrSbom: (v: string) => void;
  scanLoading: boolean;
  scanResult: any;
  scanErr: string;
  onPkgScan: () => void;
  onCtrScan: () => void;
}) {
  const fileRef = useRef<HTMLInputElement>(null);
  const severityBadge = (sev: string) => {
    const s = (sev || "UNKNOWN").toUpperCase();
    const base = "inline-flex items-center text-[10px] font-semibold px-2 py-0.5 rounded-md border";
    if (s === "CRITICAL") return `${base} bg-red-950/40 border-red-800/50 text-red-200`;
    if (s === "HIGH") return `${base} bg-amber-950/30 border-amber-800/40 text-amber-200`;
    if (s === "MEDIUM") return `${base} bg-indigo-950/30 border-indigo-800/40 text-indigo-200`;
    if (s === "LOW") return `${base} bg-emerald-950/30 border-emerald-800/40 text-emerald-200`;
    if (s === "NONE") return `${base} bg-slate-900/60 border-slate-700 text-slate-400`;
    return `${base} bg-slate-900/60 border-slate-700 text-slate-400`;
  };
  const chip = (text: string, cls: string) => (
    <span className={`text-[10px] px-2 py-1 rounded-md border ${cls}`}>{text}</span>
  );
  const armStatus = (s: string) => {
    if (s === "enforced") return { label: "✅ ENFORCED", cls: "bg-emerald-950/30 border-emerald-800/40 text-emerald-200" };
    if (s === "receipt_only") return { label: "📋 RECEIPT", cls: "bg-amber-950/30 border-amber-800/40 text-amber-200" };
    if (s === "unavailable") return { label: "⚠️ UNAVAILABLE", cls: "bg-amber-950/30 border-amber-800/40 text-amber-200" };
    return { label: "Skipped", cls: "bg-slate-900/60 border-slate-700 text-slate-400" };
  };

  return (
    <div className="flex flex-col gap-5 h-full">
      <div className="flex rounded-2xl bg-slate-950 p-1.5 border border-slate-800 shadow-inner">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => onModeChange(tab.id)}
            className={`flex-1 py-3 px-2 rounded-xl text-xs sm:text-sm font-bold transition-all duration-200 ${
              mode === tab.id
                ? "bg-emerald-600 text-white shadow-lg shadow-emerald-900/40 scale-[1.02]"
                : "text-slate-500 hover:text-slate-300 hover:bg-slate-900"
            }`}
          >
            <span className="block sm:inline mb-1 sm:mb-0 sm:mr-1.5 text-base sm:text-sm">{tab.icon}</span>
            <span className="block sm:inline">{tab.label}</span>
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

      {mode === "scanner" && (
        <div className="space-y-3 flex-1 overflow-y-auto">
          <div className="flex rounded-xl bg-slate-900/80 p-1 border border-slate-800">
            <button
              type="button"
              onClick={() => setScanMode("package")}
              className={`flex-1 py-2 px-2 rounded-lg text-xs sm:text-sm font-medium transition ${
                scanMode === "package"
                  ? "bg-emerald-600/90 text-white shadow"
                  : "text-slate-500 hover:text-slate-300"
              }`}
            >
              📦 Package Scan
            </button>
            <button
              type="button"
              onClick={() => setScanMode("container")}
              className={`flex-1 py-2 px-2 rounded-lg text-xs sm:text-sm font-medium transition ${
                scanMode === "container"
                  ? "bg-emerald-600/90 text-white shadow"
                  : "text-slate-500 hover:text-slate-300"
              }`}
            >
              🐳 Container Scan
            </button>
          </div>

          {scanMode === "package" && (
            <>
              <label className="text-xs text-slate-500">Ecosystem</label>
              <select
                className="w-full bg-slate-900/60 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
                value={scanEco}
                onChange={(e) => setScanEco(e.target.value)}
              >
                {["npm", "PyPI", "Go", "Maven", "RubyGems", "crates.io"].map((o) => (
                  <option key={o} value={o}>
                    {o}
                  </option>
                ))}
              </select>
              <label className="text-xs text-slate-500">Packages (one per line: name@version)</label>
              <textarea
                className="min-h-[140px] w-full bg-slate-900/60 border border-slate-700 rounded-lg px-3 py-2 text-xs font-mono resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
                rows={6}
                placeholder={"lodash@4.17.20\nflask@2.0.1"}
                value={scanPkgText}
                onChange={(e) => setScanPkgText(e.target.value)}
              />
              <button
                type="button"
                onClick={onPkgScan}
                disabled={scanLoading}
                className="w-full py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-sm font-semibold disabled:opacity-40 transition"
              >
                🔍 Scan Packages
              </button>
            </>
          )}

          {scanMode === "container" && (
            <>
              <label className="text-xs text-slate-500">Docker Image</label>
              <input
                className="w-full bg-slate-900/60 border border-slate-700 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
                placeholder="nginx:1.21"
                value={ctrImage}
                onChange={(e) => setCtrImage(e.target.value)}
              />
              <label className="text-xs text-slate-500">SBOM (optional, one per line: name@version:ecosystem)</label>
              <textarea
                className="min-h-[110px] w-full bg-slate-900/60 border border-slate-700 rounded-lg px-3 py-2 text-xs font-mono resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500/40"
                rows={4}
                placeholder="flask@2.0.1:PyPI"
                value={ctrSbom}
                onChange={(e) => setCtrSbom(e.target.value)}
              />
              <button
                type="button"
                onClick={onCtrScan}
                disabled={scanLoading}
                className="w-full py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-sm font-semibold disabled:opacity-40 transition"
              >
                🐳 Scan Container
              </button>
            </>
          )}

          {scanLoading && (
            <div className="flex flex-col items-center justify-center gap-2 py-6 text-sm text-slate-500 animate-pulse">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              Scanning with Mistral AI + ArmorIQ...
            </div>
          )}

          {!!scanErr && (
            <div className="text-xs text-red-300 bg-red-950/40 border border-red-800/50 rounded-lg px-3 py-2">
              {scanErr}
            </div>
          )}

          {scanResult !== null && (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2">
                {chip(`🔴 Critical: ${scanResult.critical_count ?? 0}`, "bg-red-950/40 border-red-800/50 text-red-200")}
                {chip(`🟠 High: ${scanResult.high_count ?? 0}`, "bg-amber-950/30 border-amber-800/40 text-amber-200")}
                {chip(`🟡 Medium: ${scanResult.medium_count ?? 0}`, "bg-indigo-950/30 border-indigo-800/40 text-indigo-200")}
                {chip(`🟢 Low: ${scanResult.low_count ?? 0}`, "bg-emerald-950/30 border-emerald-800/40 text-emerald-200")}
                {chip(`📦 Scanned: ${scanResult.total_scanned ?? "—"}`, "bg-slate-800/80 border-slate-700 text-slate-300")}
              </div>

              {scanMode === "container" && (
                <div className="space-y-2">
                  <div className="text-xs text-slate-400">
                    Image: <span className="text-slate-200 font-mono">{scanResult.image ?? "—"}</span> | OS:{" "}
                    <span className="text-slate-200">{scanResult.base_os_guess ?? "—"}</span> | Risk:{" "}
                    <span className={severityBadge(scanResult.overall_risk || "UNKNOWN")}>
                      {(scanResult.overall_risk || "UNKNOWN").toUpperCase()}
                    </span>
                  </div>
                  {scanResult.uses_latest_tag && (
                    <div className="text-xs text-amber-200 bg-amber-950/30 border border-amber-800/40 rounded-lg px-3 py-2">
                      ⚠️ Pin image to a specific digest — 'latest' is insecure
                    </div>
                  )}
                </div>
              )}

              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    {scanMode === "package" ? (
                      <tr className="text-xs text-slate-500 border-b border-slate-800">
                        <th className="text-left py-2 pr-2 font-medium">Package</th>
                        <th className="text-left py-2 pr-2 font-medium">Version</th>
                        <th className="text-left py-2 pr-2 font-medium">Severity</th>
                        <th className="text-left py-2 pr-2 font-medium">CVE IDs</th>
                        <th className="text-left py-2 pr-2 font-medium">Summary</th>
                        <th className="text-left py-2 pr-2 font-medium">Fix Version</th>
                        <th className="text-left py-2 pr-2 font-medium">OWASP</th>
                      </tr>
                    ) : (
                      <tr className="text-xs text-slate-500 border-b border-slate-800">
                        <th className="text-left py-2 pr-2 font-medium">Component</th>
                        <th className="text-left py-2 pr-2 font-medium">Severity</th>
                        <th className="text-left py-2 pr-2 font-medium">CVE IDs</th>
                        <th className="text-left py-2 pr-2 font-medium">Summary</th>
                      </tr>
                    )}
                  </thead>
                  <tbody className="text-slate-300">
                    {scanMode === "package" ? (
                      (scanResult.findings || []).filter((f: any) => f?.severity && f.severity !== "NONE").length ? (
                        (scanResult.findings || [])
                          .filter((f: any) => f?.severity && f.severity !== "NONE")
                          .map((f: any, idx: number) => (
                            <tr key={idx} className="border-b border-slate-800/60">
                              <td className="py-2 pr-2 font-mono text-xs text-slate-200">{f.package}</td>
                              <td className="py-2 pr-2 font-mono text-xs text-slate-400">{f.version}</td>
                              <td className="py-2 pr-2">
                                <span className={severityBadge(f.severity)}>{String(f.severity).toUpperCase()}</span>
                              </td>
                              <td className="py-2 pr-2 text-xs text-slate-400">
                                {(Array.isArray(f.cve_ids) ? f.cve_ids.join(", ") : "") || "—"}
                              </td>
                              <td className="py-2 pr-2 text-xs">{f.summary || "—"}</td>
                              <td className="py-2 pr-2 font-mono text-xs text-slate-400">{f.recommended_version || "—"}</td>
                              <td className="py-2 pr-2 text-xs text-slate-400">{f.owasp || "—"}</td>
                            </tr>
                          ))
                      ) : (
                        <tr>
                          <td colSpan={7} className="py-3 text-sm text-emerald-300">
                            ✅ No vulnerabilities found.
                          </td>
                        </tr>
                      )
                    ) : (
                      ([] as any[])
                        .concat(scanResult.image_findings || [])
                        .concat(scanResult.package_findings || [])
                        .length ? (
                        ([] as any[])
                          .concat(scanResult.image_findings || [])
                          .concat(scanResult.package_findings || [])
                          .map((f: any, idx: number) => (
                            <tr key={idx} className="border-b border-slate-800/60">
                              <td className="py-2 pr-2 font-mono text-xs text-slate-200">{f.component || f.package || "—"}</td>
                              <td className="py-2 pr-2">
                                <span className={severityBadge(f.severity)}>{String(f.severity || "UNKNOWN").toUpperCase()}</span>
                              </td>
                              <td className="py-2 pr-2 text-xs text-slate-400">
                                {(Array.isArray(f.cve_ids) ? f.cve_ids.join(", ") : "") || "—"}
                              </td>
                              <td className="py-2 pr-2 text-xs">{f.summary || "—"}</td>
                            </tr>
                          ))
                      ) : (
                        <tr>
                          <td colSpan={4} className="py-3 text-sm text-emerald-300">
                            ✅ No vulnerabilities found.
                          </td>
                        </tr>
                      )
                    )}
                  </tbody>
                </table>
              </div>

              {scanMode === "container" && scanResult.hardening_steps?.length ? (
                <div className="space-y-2">
                  <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">
                    🔧 Hardening Steps
                  </p>
                  <ul className="list-disc pl-5 text-xs text-slate-300 space-y-1">
                    {scanResult.hardening_steps.map((s: string, i: number) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              <div className="space-y-2">
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">
                  🔐 ArmorIQ Enforcement
                </p>
                <div className="flex flex-wrap items-center gap-2">
                  {(() => {
                    const st = armStatus(scanResult.armoriq?.status || "");
                    return chip(st.label, st.cls);
                  })()}
                </div>
                {scanResult.armoriq?.receipt && (
                  <div className="font-mono text-xs text-slate-300 bg-slate-900/60 border border-slate-700 rounded-lg px-3 py-2">
                    {String(scanResult.armoriq.receipt).slice(0, 64)}...
                  </div>
                )}
                {Array.isArray(scanResult.armoriq?.enforcement) &&
                  scanResult.armoriq.enforcement.some((e: any) => e?.decision === "BLOCK") && (
                    <div className="bg-red-950/40 border border-red-800/50 rounded-lg px-3 py-2 text-xs text-red-200">
                      <div className="font-semibold mb-1">🚫 BLOCKED BY ARMORIQ</div>
                      {scanResult.armoriq.enforcement
                        .filter((e: any) => e?.decision === "BLOCK")
                        .map((e: any, i: number) => (
                          <div key={i}>
                            {e.action} — {e.resource}
                          </div>
                        ))}
                    </div>
                  )}
              </div>

              <div className="flex flex-wrap gap-2">
                <span className="text-[10px] px-2 py-1 rounded-md bg-slate-800/80 border border-slate-700 text-slate-300">
                  <span className="text-amber-500/90 font-semibold">OWASP</span>{" "}
                  <span className="text-slate-400">A06:2021</span>
                </span>
                <span className="text-[10px] px-2 py-1 rounded-md bg-slate-800/80 border border-slate-700 text-slate-300">
                  <span className="text-amber-500/90 font-semibold">CWE</span>{" "}
                  <span className="text-slate-400">CWE-1104</span>
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      {scanSummary && (
        <p className="text-xs text-emerald-400/80 bg-emerald-950/30 border border-emerald-800/30 rounded-lg px-3 py-2">
          {scanSummary}
        </p>
      )}

      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3">
        <label className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer">
          <input
            type="checkbox"
            checked={useDelegation}
            onChange={(e) => onUseDelegationChange(e.target.checked)}
            className="rounded border-slate-600"
          />
          <span>
            <strong className="text-indigo-400">Delegation demo</strong> — scoped sub-agent token
          </span>
        </label>
      </div>

      <div className="mt-auto pt-4 border-t border-slate-800 space-y-4">
        <div className="rounded-xl bg-amber-950/20 border border-amber-800/30 p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xs font-bold text-amber-400 uppercase tracking-widest">
              Attack the Agent
            </h3>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                className="sr-only peer"
                checked={simulateAttack}
                onChange={(e) => onSimulateAttackChange(e.target.checked)}
              />
              <div className="w-9 h-5 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-amber-600"></div>
            </label>
          </div>
          <p className="text-[10px] text-slate-500 mb-3 leading-relaxed">
            Append a malicious <code className="text-amber-300/80">delete_all</code> step after LLM signs the intent plan. Proves ArmorIQ blocks undeclared steps (prompt-injection defense).
          </p>
          <button
            type="button"
            onClick={onPlanFix}
            disabled={loading || !(repoUrl || alertText || codeText)}
            className={`w-full py-3 rounded-lg text-sm font-bold transition-all shadow-lg ${
              simulateAttack 
                ? "bg-amber-600 hover:bg-amber-500 text-white shadow-amber-900/20" 
                : "bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-900/20"
            } disabled:opacity-40`}
          >
            {simulateAttack ? "Generate Plan + Attack" : "Generate Verified Fix Plan"}
          </button>
        </div>

        <button
          type="button"
          onClick={onExportBrief}
          disabled={!canExport}
          className="w-full py-2.5 rounded-lg border border-slate-700 text-slate-300 text-xs font-medium hover:bg-slate-800 disabled:opacity-30 transition flex items-center justify-center gap-2"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Export Incident Brief (.md)
        </button>
      </div>
    </div>
  );
}
