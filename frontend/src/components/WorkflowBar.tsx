"use client";

import type { WorkflowStep } from "@/lib/types";

const STEPS: { id: WorkflowStep; label: string; desc: string }[] = [
  { id: "input", label: "Input", desc: "Repo or alert" },
  { id: "analyze", label: "Analyze", desc: "AI + heuristics" },
  { id: "plan", label: "Plan", desc: "Remediation steps" },
  { id: "enforce", label: "Enforce", desc: "ArmorIQ gate" },
];

export function WorkflowBar({ current }: { current: WorkflowStep }) {
  const idx = STEPS.findIndex((s) => s.id === current);
  return (
    <div className="flex items-center gap-1 sm:gap-4 bg-slate-900/40 p-3 rounded-xl border border-slate-800/50">
      {STEPS.map((step, i) => {
        const active = i <= idx;
        const currentStep = i === idx;
        return (
          <div key={step.id} className="flex-1 min-w-0 group">
            <div className="flex items-center gap-2 mb-1">
              <div
                className={`w-4 h-4 rounded-full flex items-center justify-center text-[8px] font-bold transition-all ${
                  active ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/20" : "bg-slate-800 text-slate-500"
                } ${currentStep ? "ring-2 ring-emerald-400 ring-offset-2 ring-offset-slate-950" : ""}`}
              >
                {i + 1}
              </div>
              <div
                className={`flex-1 h-0.5 rounded-full transition-all ${
                  i < idx ? "bg-emerald-500" : "bg-slate-800"
                }`}
              />
            </div>
            <p
              className={`text-[10px] sm:text-xs font-bold truncate transition-colors ${
                active ? "text-emerald-400" : "text-slate-500"
              }`}
            >
              {step.label}
            </p>
            <p className="text-[9px] text-slate-600 hidden sm:block truncate opacity-0 group-hover:opacity-100 transition-opacity">
              {step.desc}
            </p>
          </div>
        );
      })}
    </div>
  );
}
