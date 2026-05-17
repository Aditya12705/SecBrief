"use client";

import type { ChatMessage } from "@/lib/types";
import { IntentReceiptCard } from "./IntentReceiptCard";
import { MarkdownLite } from "./MarkdownLite";
import { ComplianceBar } from "./ComplianceBar";
import { SeverityBadge } from "./SeverityBadge";

export function ChatPanel({
  messages,
  loading,
}: {
  messages: ChatMessage[];
  loading: boolean;
}) {
  return (
    <div className="flex flex-col h-full min-h-[420px]">
      <div className="flex-1 overflow-y-auto space-y-4 pr-1">
        {messages.length === 0 && (
          <div className="rounded-xl border border-dashed border-slate-700 p-8 text-center">
            <p className="text-slate-400 text-sm max-w-md mx-auto">
              Upload a report, scan a repo, or paste an alert. Get a plain-English briefing, then a
              remediation plan with{" "}
              <strong className="text-emerald-400">verified allow / block</strong> on each step.
            </p>
          </div>
        )}
        {messages.map((msg) => (
          <article
            key={msg.id}
            className={`animate-in rounded-xl p-4 ${
              msg.role === "user"
                ? "ml-6 bg-slate-800/50 border border-slate-700/50"
                : "mr-2 glass"
            }`}
          >
            <header className="flex items-center gap-2 mb-2">
              <span
                className={`text-[10px] uppercase tracking-wider font-semibold ${
                  msg.role === "user" ? "text-slate-500" : "text-amber-400"
                }`}
              >
                {msg.role === "user" ? "You" : "SecBrief"}
              </span>
              {msg.analysis?.severity && (
                <SeverityBadge
                  severity={msg.analysis.severity}
                  score={msg.analysis.risk_score}
                />
              )}
              {msg.meta && (
                <span className="text-[10px] text-slate-600 ml-auto">{msg.meta}</span>
              )}
            </header>
            <ComplianceBar analysis={msg.analysis} />
            {msg.analysis?.summary && (
              <p className="text-sm text-slate-300 mb-2">{msg.analysis.summary}</p>
            )}
            <MarkdownLite text={msg.text} />
            {msg.decisions && msg.decisions.length > 0 && (
              <div className="mt-4 space-y-2">
                <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">
                  Policy check
                </p>
                {msg.decisions.map((d, j) => (
                  <div
                    key={j}
                    className={`flex gap-2 text-xs rounded-lg px-3 py-2 border ${
                      d.status === "block"
                        ? "bg-red-950/40 border-red-800/50"
                        : d.status === "hold"
                          ? "bg-amber-950/30 border-amber-800/40"
                          : "bg-emerald-950/30 border-emerald-800/40"
                    }`}
                  >
                    <span className="font-mono font-bold uppercase shrink-0 w-14">
                      {d.status}
                    </span>
                    <span className="text-slate-300">
                      <code className="text-emerald-300/90">{d.action}</code>
                      {d.csrg_path && (
                        <span className="text-slate-600 text-[10px] ml-1">({d.csrg_path})</span>
                      )}
                      {" — "}
                      {d.message}
                      {d.in_signed_plan === false && (
                        <span className="text-red-400 font-medium"> · NOT in signed plan</span>
                      )}
                      {d.simulated && (
                        <span className="text-slate-500"> (demo policy)</span>
                      )}
                    </span>
                  </div>
                ))}
              </div>
            )}
            {msg.receipt && <IntentReceiptCard receipt={msg.receipt} />}
          </article>
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-sm text-slate-500 animate-pulse">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            Working…
          </div>
        )}
      </div>
    </div>
  );
}
