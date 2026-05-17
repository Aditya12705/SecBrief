"use client";

/** Minimal markdown-ish renderer for SecBrief analysis text */
export function MarkdownLite({ text }: { text: string }) {
  const lines = text.split("\n");
  return (
    <div className="prose-ve text-sm space-y-1">
      {lines.map((line, i) => {
        if (line.startsWith("# "))
          return (
            <h1 key={i} className="text-base font-semibold text-white">
              {line.slice(2)}
            </h1>
          );
        if (line.startsWith("## "))
          return (
            <h2 key={i} className="text-sm font-semibold text-emerald-400/90 mt-3">
              {line.slice(3)}
            </h2>
          );
        if (line.startsWith("**") && line.endsWith("**"))
          return (
            <p key={i} className="font-medium text-slate-200">
              {line.replace(/\*\*/g, "")}
            </p>
          );
        if (line.startsWith("- "))
          return (
            <p key={i} className="text-slate-400 pl-3">
              • {line.slice(2)}
            </p>
          );
        if (/^\d+\.\s/.test(line))
          return (
            <p key={i} className="text-slate-400 pl-1">
              {line}
            </p>
          );
        if (line.startsWith("```"))
          return null;
        if (!line.trim()) return <br key={i} />;
        return (
          <p key={i} className="text-slate-400 leading-relaxed">
            {line}
          </p>
        );
      })}
    </div>
  );
}
