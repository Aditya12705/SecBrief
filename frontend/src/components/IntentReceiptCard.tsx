"use client";

import type { IntentReceipt } from "@/lib/types";

export function IntentReceiptCard({ receipt }: { receipt: IntentReceipt }) {
  if (!receipt?.plan_hash) return null;

  return (
    <div className="mt-4 rounded-xl border border-emerald-500/30 bg-emerald-950/20 p-4">
      <div className="flex items-center justify-between mb-3">
        <p className="text-[10px] uppercase tracking-widest text-emerald-400 font-bold">
          ArmorIQ Intent Receipt
        </p>
        <div className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-tighter ${
          receipt.armoriq_live ? "bg-emerald-500 text-white" : "bg-slate-700 text-slate-300"
        }`}>
          {receipt.armoriq_live ? "Live Verified" : "Demo Mode"}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-2 text-[10px] font-mono">
        <div>
          <dt className="text-slate-500 text-[9px] uppercase">Plan hash</dt>
          <dd className="text-emerald-200 truncate" title={receipt.plan_hash}>
            {receipt.plan_hash}
          </dd>
        </div>
        <div>
          <dt className="text-slate-500 text-[9px] uppercase">Steps signed</dt>
          <dd className="text-slate-200">{receipt.total_steps}</dd>
        </div>
        {receipt.token_id && (
          <div className="sm:col-span-2">
            <dt className="text-slate-500 text-[9px] uppercase">Token ID</dt>
            <dd className="text-slate-300 truncate">{receipt.token_id}</dd>
          </div>
        )}
        {receipt.merkle_root && receipt.merkle_root !== "0" && (
          <div>
            <dt className="text-slate-500 text-[9px] uppercase">Merkle Root</dt>
            <dd className="text-slate-400 truncate">{receipt.merkle_root}</dd>
          </div>
        )}
        {receipt.expires_in_seconds !== undefined && receipt.expires_in_seconds > 0 && (
          <div>
            <dt className="text-slate-500 text-[9px] uppercase">Expiry</dt>
            <dd className="text-amber-400">
              {Math.floor(receipt.expires_in_seconds / 60)}m left
            </dd>
          </div>
        )}
      </div>
      
      {receipt.policy_bound && (
        <div className="mt-3 pt-2 border-t border-emerald-500/10 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <svg className="w-3 h-3 text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span className="text-[9px] text-emerald-400 font-medium uppercase tracking-wider">Policy Enforcement Active</span>
          </div>
          <a 
            href="https://platform.armoriq.ai" 
            target="_blank" 
            rel="noreferrer"
            className="text-[9px] text-slate-500 hover:text-emerald-400 underline underline-offset-2 transition-colors"
          >
            View Audit on Platform
          </a>
        </div>
      )}
    </div>
  );
}
