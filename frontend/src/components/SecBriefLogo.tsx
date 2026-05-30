import type { SVGProps } from "react";

const sizes = {
  sm: 24,
  md: 40,
  lg: 56,
} as const;

type LogoSize = keyof typeof sizes;

type SecBriefLogoProps = {
  size?: LogoSize;
  className?: string;
  showText?: boolean;
  tagline?: string;
};

function LogoMark({ size, className, ...props }: SVGProps<SVGSVGElement> & { size: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden
      {...props}
    >
      <defs>
        <linearGradient id="sb-logo" x1="4" y1="2" x2="28" y2="30" gradientUnits="userSpaceOnUse">
          <stop stopColor="#f59e0b" />
          <stop offset="1" stopColor="#10b981" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="8" fill="url(#sb-logo)" />
      <path
        d="M16 7.5c-4.2 2.4-7 4.2-7 8.2 0 3.1 2.1 5.8 5.2 7.1-.9-1.4-1.4-3-1.4-4.6 0-4.8 3.2-7.2 3.2-10.7 0-1.1-.3-2.1-.8-3zm0 17c4.2-2.4 7-4.2 7-8.2 0-3.1-2.1-5.8-5.2-7.1.9 1.4 1.4 3 1.4 4.6 0 4.8-3.2 7.2-3.2 10.7 0 1.1.3 2.1.8 3z"
        fill="#fff"
        fillOpacity={0.95}
      />
      <path
        d="M11.5 12.5h9M11.5 16h7.5M11.5 19.5h9"
        stroke="#fff"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeOpacity={0.35}
      />
    </svg>
  );
}

export function SecBriefLogo({ size = "md", className = "", showText = false, tagline }: SecBriefLogoProps) {
  const px = sizes[size];

  if (!showText) {
    return (
      <LogoMark
        size={px}
        className={`shrink-0 shadow-lg shadow-emerald-500/20 ${className}`}
      />
    );
  }

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <LogoMark size={px} className="shrink-0 shadow-lg shadow-emerald-500/20" />
      <div>
        <h1 className="text-xl font-bold tracking-tight">
          Sec<span className="text-emerald-400">Brief</span>
        </h1>
        {tagline && <p className="text-xs text-slate-500">{tagline}</p>}
      </div>
    </div>
  );
}
