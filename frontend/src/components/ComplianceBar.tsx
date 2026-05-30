"use client";

import type { Analysis } from "@/lib/types";

export function ComplianceBar({ analysis }: { analysis?: Analysis }) {
  if (!analysis) return null;
  const items: { label: string; value: string }[] = [];
  if (analysis.owasp_category && analysis.owasp_category !== "N/A") {
    items.push({ label: "OWASP", value: analysis.owasp_category });
  }
  if (analysis.cwe_id && analysis.cwe_id !== "N/A") {
    items.push({ label: "CWE", value: analysis.cwe_id });
  }
  if (analysis.soc2_controls?.length) {
    items.push({ label: "SOC 2", value: analysis.soc2_controls.join(", ") });
  }
  if (analysis.financial_impact_inr) {
    items.push({ label: "Impact", value: analysis.financial_impact_inr });
  }
  if (!items.length) return null;

  return (
    <div className="flex flex-wrap gap-2 mb-3">
      {items.map((item) => (
        <span
          key={item.label}
          className="inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-medium bg-slate-900 text-slate-300 border border-slate-700/50 shadow-sm"
          title={item.value}
        >
          <span className="text-amber-400 mr-1.5 font-bold uppercase tracking-tighter text-[9px]">
            {item.label}
          </span>{" "}
          <span className="text-slate-200 max-w-[150px] truncate">
            {item.value}
          </span>
        </span>
      ))}
    </div>
  );
}
