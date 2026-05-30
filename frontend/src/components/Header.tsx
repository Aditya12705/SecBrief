"use client";

import Link from "next/link";
import { SecBriefLogo } from "@/components/SecBriefLogo";

export function Header() {
  return (
    <header className="border-b border-slate-800/80 glass sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
        <div className="flex items-center justify-between">
          <SecBriefLogo size="md" showText tagline="Explain the risk · Enforce the fix" />
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
