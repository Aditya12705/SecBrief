"use client";

import Link from "next/link";

export function Header() {
  return (
    <header className="border-b border-slate-800/80 glass sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-emerald-600 flex items-center justify-center text-sm font-bold shadow-lg shadow-emerald-500/20">
              SB
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">
                Sec<span className="text-emerald-400">Brief</span>
              </h1>
              <p className="text-xs text-slate-500">Explain the risk · Enforce the fix</p>
            </div>
          </div>
          <Link
            href="/signup"
            className="text-sm px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
          >
            Get API Key
          </Link>
        </div>
      </div>
    </header>
  );
}
