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
    <div className="flex flex-wrap gap-2 mb-2">
      {items.map((item) => (
        <span
          key={item.label}
          className="text-[10px] px-2 py-1 rounded-md bg-slate-800/80 border border-slate-700 text-slate-300"
          title={item.value}
        >
          <span className="text-amber-500/90 font-semibold">{item.label}</span>{" "}
          <span className="text-slate-400">{item.value.length > 40 ? `${item.value.slice(0, 40)}…` : item.value}</span>
        </span>
      ))}
    </div>
  );
}
