import React from "react";
import { SecBriefLogo } from "@/components/SecBriefLogo";

export function LandingPage({ onStart }: { onStart: () => void }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 sm:px-6 py-12 text-center relative overflow-hidden">
      {/* Background Decorative Elements */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-6xl h-full pointer-events-none opacity-20">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-emerald-500/20 blur-[120px] rounded-full" />
        <div className="absolute bottom-[10%] right-[-10%] w-[30%] h-[30%] bg-amber-500/10 blur-[100px] rounded-full" />
      </div>

      <div className="relative z-10 max-w-4xl w-full flex flex-col items-center">
        {/* Logo/Badge */}
        <div className="mb-8 flex items-center gap-3 px-4 py-2 rounded-full bg-slate-900/80 border border-slate-800 backdrop-blur-md animate-in fade-in slide-in-from-top-4 duration-1000">
          <SecBriefLogo size="sm" />
          <span className="text-xs font-bold text-slate-300 tracking-widest uppercase">SecBrief — AI Safety Agent</span>
        </div>

        {/* Hero Title */}
        <h1 className="text-4xl sm:text-7xl font-black text-white leading-[1.1] tracking-tight mb-6 animate-in fade-in slide-in-from-bottom-6 duration-1000 delay-200">
          Explain the <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-orange-500">risk</span>.<br />
          Enforce the <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-teal-500">fix</span>.
        </h1>

        <p className="text-lg sm:text-xl text-slate-400 max-w-2xl mb-10 leading-relaxed animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-300">
          Generic AI suggests code. SecBrief signs intent. 
          Stop prompt-injection disasters with <strong>ArmorIQ-verified</strong> remediation plans.
        </p>

        {/* Primary CTA */}
        <button
          onClick={onStart}
          className="group relative px-8 py-4 bg-emerald-600 hover:bg-emerald-500 text-white rounded-2xl font-bold text-lg transition-all hover:scale-[1.02] active:scale-[0.98] shadow-2xl shadow-emerald-900/20 animate-in fade-in slide-in-from-bottom-10 duration-1000 delay-500"
        >
          Launch Security Dashboard
          <span className="ml-2 group-hover:translate-x-1 transition-transform inline-block">→</span>
        </button>

        {/* Feature Grid */}
        <div className="mt-20 grid grid-cols-1 sm:grid-cols-3 gap-6 w-full animate-in fade-in slide-in-from-bottom-12 duration-1000 delay-700">
          <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800 text-left hover:border-slate-700 transition-colors">
            <div className="text-amber-400 text-2xl mb-3">🛡️</div>
            <h3 className="text-white font-bold mb-2 uppercase text-xs tracking-widest">Signed Intent</h3>
            <p className="text-slate-500 text-sm leading-relaxed">
              Every step is cryptographically signed. AI cannot add undeclared tools or commands.
            </p>
          </div>
          <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800 text-left hover:border-slate-700 transition-colors">
            <div className="text-emerald-400 text-2xl mb-3">🔍</div>
            <h3 className="text-white font-bold mb-2 uppercase text-xs tracking-widest">Plain English</h3>
            <p className="text-slate-500 text-sm leading-relaxed">
              Mistral-powered briefings map jargon to OWASP, CWE, and real ₹ financial risk.
            </p>
          </div>
          <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800 text-left hover:border-slate-700 transition-colors">
            <div className="text-blue-400 text-2xl mb-3">📑</div>
            <h3 className="text-white font-bold mb-2 uppercase text-xs tracking-widest">Audit Ready</h3>
            <p className="text-slate-500 text-sm leading-relaxed">
              Generate SOC2-ready incident briefs with ArmorIQ cryptographic receipts.
            </p>
          </div>
        </div>

        {/* Social Proof / Tech Stack */}
        <div className="mt-16 flex items-center gap-6 opacity-40 grayscale animate-in fade-in duration-1000 delay-1000">
          <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Powered By</span>
          <div className="h-4 w-px bg-slate-800" />
          <span className="text-xs font-bold text-white">Mistral AI</span>
          <span className="text-xs font-bold text-white">ArmorIQ SDK</span>
          <span className="text-xs font-bold text-white">Next.js 14</span>
        </div>
      </div>
    </div>
  );
}
