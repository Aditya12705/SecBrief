const COLORS: Record<string, string> = {
  critical: "bg-red-500/20 text-red-300 border-red-500/40",
  high: "bg-orange-500/20 text-orange-300 border-orange-500/40",
  medium: "bg-amber-500/20 text-amber-300 border-amber-500/40",
  low: "bg-sky-500/20 text-sky-300 border-sky-500/40",
  info: "bg-slate-500/20 text-slate-300 border-slate-500/40",
};

export function SeverityBadge({ severity, score }: { severity?: string; score?: number }) {
  const key = (severity || "medium").toLowerCase();
  const cls = COLORS[key] || COLORS.medium;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${cls}`}>
      {severity || "Unknown"}
      {score != null && <span className="opacity-70">· {score}/10</span>}
    </span>
  );
}
