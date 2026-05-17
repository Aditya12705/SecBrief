"use client";

import type { IntentReceipt } from "@/lib/types";

export function IntentReceiptCard({ receipt }: { receipt: IntentReceipt }) {
  if (!receipt?.plan_hash) return null;

  return (
    <div className="mt-4 rounded-xl border border-indigo-500/30 bg-indigo-950/20 p-4">
      <p className="text-[10px] uppercase tracking-widest text-indigo-400 font-semibold mb-2">
        Intent receipt
      </p>
      <dl className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] font-mono">
        <div>
          <dt className="text-slate-500">Plan hash</dt>
          <dd className="text-indigo-200 truncate" title={receipt.plan_hash}>
            {receipt.plan_hash}
          </dd>
        </div>
        <div>
          <dt className="text-slate-500">Steps signed</dt>
          <dd className="text-slate-200">{receipt.total_steps}</dd>
        </div>
      </dl>
    </div>
  );
}
