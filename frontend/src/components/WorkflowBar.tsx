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
    <div className="flex gap-1 sm:gap-2">
      {STEPS.map((step, i) => {
        const active = i <= idx;
        const currentStep = i === idx;
        return (
          <div key={step.id} className="flex-1 min-w-0">
            <div
              className={`h-1 rounded-full mb-1.5 transition-all ${
                active ? "bg-emerald-500" : "bg-slate-800"
              } ${currentStep ? "ring-1 ring-emerald-400/50" : ""}`}
            />
            <p
              className={`text-[10px] sm:text-xs font-medium truncate ${
                active ? "text-emerald-400" : "text-slate-600"
              }`}
            >
              {step.label}
            </p>
            <p className="text-[9px] text-slate-600 hidden sm:block truncate">{step.desc}</p>
          </div>
        );
      })}
    </div>
  );
}
