"use client";

import type { ReactNode } from "react";
import type { InputMode } from "@/lib/types";

const TABS: {
  id: InputMode;
  label: string;
  icon: ReactNode;
}[] = [
  {
    id: "github",
    label: "Repo",
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 2C6.48 2 2 6.48 2 12c0 4.42 2.87 8.17 6.84 9.5.5.09.66-.22.66-.48 0-.24-.01-.87-.01-1.7-2.78.6-3.37-1.34-3.37-1.34-.45-1.15-1.1-1.46-1.1-1.46-.9-.62.07-.61.07-.61 1 .07 1.53 1.03 1.53 1.03.9 1.53 2.36 1.09 2.94.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.64 0 0 .84-.27 2.75 1.02A9.58 9.58 0 0112 6.8c.85.004 1.71.11 2.51.33 1.91-1.29 2.75-1.02 2.75-1.02.55 1.37.2 2.39.1 2.64.64.7 1.03 1.59 1.03 2.68 0 3.85-2.34 4.69-4.57 4.93.36.31.68.92.68 1.85 0 1.34-.01 2.42-.01 2.75 0 .27.16.58.67.48A10 10 0 0022 12c0-5.52-4.48-10-10-10z" />
      </svg>
    ),
  },
  {
    id: "code",
    label: "Code",
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
      </svg>
    ),
  },
  {
    id: "paste",
    label: "Alert",
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
  },
  {
    id: "demo",
    label: "Demo",
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
      </svg>
    ),
  },
  {
    id: "scanner",
    label: "Scan",
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
      </svg>
    ),
  },
];

export function TabBar({
  mode,
  onModeChange,
}: {
  mode: InputMode;
  onModeChange: (m: InputMode) => void;
}) {
  return (
    <div
      className="rounded-xl border border-slate-800 bg-slate-950/80 p-1"
      role="tablist"
      aria-label="Input source"
    >
      <div className="flex gap-0.5">
        {TABS.map((tab) => {
          const active = mode === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => onModeChange(tab.id)}
              className={`
                flex-1 min-w-0 flex flex-col items-center justify-center gap-1
                py-2.5 px-1 rounded-lg text-center transition-colors duration-150
                focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50
                ${
                  active
                    ? "bg-slate-800 text-emerald-400 shadow-sm ring-1 ring-emerald-500/25"
                    : "text-slate-500 hover:text-slate-300 hover:bg-slate-900/80"
                }
              `}
            >
              <span className={active ? "text-emerald-400" : "text-slate-500"}>{tab.icon}</span>
              <span className="text-[11px] font-semibold leading-none truncate w-full">
                {tab.label}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
