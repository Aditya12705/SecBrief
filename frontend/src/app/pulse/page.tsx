"use client";

/**
 * /pulse — SecBrief Pulse Dashboard
 * NEW FILE — does NOT modify frontend/src/app/page.tsx
 *
 * Fetches from /api/dashboard (dashboard_router.py) and renders live ArmorIQ stats.
 * Matches SecBrief's existing dark theme exactly (globals.css tokens).
 */

import { useEffect, useState } from "react";

// ── Types ─────────────────────────────────────────────────────────────────────

interface OWASPEntry {
  category: string;
  count: number;
}

interface EnforcementSummary {
  allowed: number;
  blocked: number;
  held: number;
}

interface RecentSession {
  email: string;
  source: string;
  risk_score: number;
  owasp_tags: string[];
  blocked_count: number;
  timestamp: string;
}

interface DashboardData {
  total_scans: number;
  avg_risk_score: number;
  steps_blocked: number;
  active_users: number;
  owasp_breakdown: OWASPEntry[];
  enforcement_summary: EnforcementSummary;
  recent_sessions: RecentSession[];
}

// ── Constants ─────────────────────────────────────────────────────────────────

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Design tokens — mirrors globals.css
const C = {
  bg: "#06080f",
  card: "#0d1220",
  cardHover: "#121a2e",
  border: "#1e293b",
  accent: "#34d399",
  accentDim: "#059669",
  warn: "#fbbf24",
  danger: "#f87171",
  muted: "#94a3b8",
  text: "#e2e8f0",
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function riskColor(score: number): string {
  if (score >= 7) return C.danger;
  if (score >= 4) return C.warn;
  return C.accent;
}

function riskLabel(score: number): string {
  if (score >= 7) return "HIGH";
  if (score >= 4) return "MED";
  return "LOW";
}

function fmtTimestamp(ts: string): string {
  try {
    return new Date(ts).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return ts;
  }
}

// ── Skeleton ──────────────────────────────────────────────────────────────────

function Skeleton({ w = "100%", h = "1rem" }: { w?: string; h?: string }) {
  return (
    <div
      style={{
        width: w,
        height: h,
        borderRadius: "6px",
        background: C.border,
        animation: "pulse-sk 1.6s ease-in-out infinite",
      }}
    />
  );
}

// ── Stat card ─────────────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  sub,
  accent,
  loading,
}: {
  label: string;
  value: string | number;
  sub?: string;
  accent?: string;
  loading: boolean;
}) {
  return (
    <div
      style={{
        background: C.card,
        border: `1px solid ${C.border}`,
        borderRadius: "14px",
        padding: "1.25rem 1.5rem",
        display: "flex",
        flexDirection: "column",
        gap: "0.35rem",
        transition: "background 0.2s",
      }}
      onMouseEnter={(e) =>
        ((e.currentTarget as HTMLDivElement).style.background = C.cardHover)
      }
      onMouseLeave={(e) =>
        ((e.currentTarget as HTMLDivElement).style.background = C.card)
      }
    >
      <span style={{ fontSize: "0.72rem", color: C.muted, letterSpacing: "0.08em", textTransform: "uppercase" }}>
        {label}
      </span>
      {loading ? (
        <Skeleton h="2rem" w="60%" />
      ) : (
        <span
          style={{
            fontSize: "2rem",
            fontWeight: 700,
            color: accent ?? C.text,
            lineHeight: 1.1,
          }}
        >
          {value}
        </span>
      )}
      {sub && !loading && (
        <span style={{ fontSize: "0.75rem", color: C.muted }}>{sub}</span>
      )}
    </div>
  );
}

// ── OWASP Bar Chart ───────────────────────────────────────────────────────────

function OWASPChart({
  data,
  loading,
}: {
  data: OWASPEntry[];
  loading: boolean;
}) {
  const max = Math.max(...data.map((d) => d.count), 1);
  return (
    <div
      style={{
        background: C.card,
        border: `1px solid ${C.border}`,
        borderRadius: "14px",
        padding: "1.25rem 1.5rem",
        flex: 1,
      }}
    >
      <h3 style={{ fontSize: "0.8rem", color: C.muted, marginBottom: "1rem", letterSpacing: "0.08em", textTransform: "uppercase" }}>
        Top OWASP Categories
      </h3>
      {loading ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} h="1.5rem" />
          ))}
        </div>
      ) : data.length === 0 ? (
        <p style={{ color: C.muted, fontSize: "0.85rem" }}>No data yet — run a scan first.</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.65rem" }}>
          {data.map((entry) => (
            <div key={entry.category}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  marginBottom: "0.25rem",
                  fontSize: "0.78rem",
                }}
              >
                <span style={{ color: C.text }}>{entry.category}</span>
                <span style={{ color: C.muted }}>{entry.count}</span>
              </div>
              <div
                style={{
                  height: "6px",
                  borderRadius: "99px",
                  background: C.border,
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    height: "100%",
                    width: `${(entry.count / max) * 100}%`,
                    background: `linear-gradient(90deg, ${C.accent}, ${C.accentDim})`,
                    borderRadius: "99px",
                    transition: "width 0.6s cubic-bezier(0.4,0,0.2,1)",
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Donut Chart (SVG) ─────────────────────────────────────────────────────────

function DonutChart({
  data,
  loading,
}: {
  data: EnforcementSummary;
  loading: boolean;
}) {
  const total = data.allowed + data.blocked + data.held || 1;
  const segments = [
    { label: "Allowed", value: data.allowed, color: C.accent },
    { label: "Blocked", value: data.blocked, color: C.danger },
    { label: "Held", value: data.held, color: C.warn },
  ];

  const R = 48;
  const cx = 60;
  const cy = 60;
  const circumference = 2 * Math.PI * R;

  let offset = 0;
  const arcs = segments.map((seg) => {
    const dash = (seg.value / total) * circumference;
    const arc = { ...seg, dash, offset };
    offset += dash;
    return arc;
  });

  return (
    <div
      style={{
        background: C.card,
        border: `1px solid ${C.border}`,
        borderRadius: "14px",
        padding: "1.25rem 1.5rem",
        flex: 1,
      }}
    >
      <h3 style={{ fontSize: "0.8rem", color: C.muted, marginBottom: "1rem", letterSpacing: "0.08em", textTransform: "uppercase" }}>
        ArmorIQ Enforcement
      </h3>
      {loading ? (
        <div style={{ display: "flex", justifyContent: "center" }}>
          <Skeleton w="120px" h="120px" />
        </div>
      ) : (
        <div style={{ display: "flex", alignItems: "center", gap: "1.5rem", flexWrap: "wrap" }}>
          <svg width={120} height={120} viewBox="0 0 120 120">
            {arcs.map((arc) => (
              <circle
                key={arc.label}
                cx={cx}
                cy={cy}
                r={R}
                fill="none"
                stroke={arc.color}
                strokeWidth={14}
                strokeDasharray={`${arc.dash} ${circumference - arc.dash}`}
                strokeDashoffset={-arc.offset}
                style={{ transform: "rotate(-90deg)", transformOrigin: "60px 60px", transition: "stroke-dasharray 0.6s ease" }}
              />
            ))}
            <text x={cx} y={cy + 5} textAnchor="middle" fontSize="13" fontWeight="700" fill={C.text}>
              {total}
            </text>
            <text x={cx} y={cy + 17} textAnchor="middle" fontSize="8" fill={C.muted}>
              steps
            </text>
          </svg>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {segments.map((seg) => (
              <div key={seg.label} style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.8rem" }}>
                <span
                  style={{
                    width: "10px",
                    height: "10px",
                    borderRadius: "50%",
                    background: seg.color,
                    flexShrink: 0,
                  }}
                />
                <span style={{ color: C.muted }}>{seg.label}</span>
                <span style={{ color: C.text, fontWeight: 600, marginLeft: "auto", paddingLeft: "0.5rem" }}>
                  {seg.value}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Recent Sessions Table ─────────────────────────────────────────────────────

function SessionsTable({
  rows,
  loading,
}: {
  rows: RecentSession[];
  loading: boolean;
}) {
  return (
    <div
      style={{
        background: C.card,
        border: `1px solid ${C.border}`,
        borderRadius: "14px",
        padding: "1.25rem 1.5rem",
        overflowX: "auto",
      }}
    >
      <h3 style={{ fontSize: "0.8rem", color: C.muted, marginBottom: "1rem", letterSpacing: "0.08em", textTransform: "uppercase" }}>
        Recent Sessions
      </h3>
      {loading ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.65rem" }}>
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} h="2rem" />
          ))}
        </div>
      ) : rows.length === 0 ? (
        <p style={{ color: C.muted, fontSize: "0.85rem" }}>No sessions yet — run a scan first.</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82rem" }}>
          <thead>
            <tr>
              {["Email", "Source", "OWASP Tags", "Risk", "Blocked", "Time"].map((h) => (
                <th
                  key={h}
                  style={{
                    textAlign: "left",
                    color: C.muted,
                    fontWeight: 500,
                    padding: "0.35rem 0.75rem",
                    borderBottom: `1px solid ${C.border}`,
                    whiteSpace: "nowrap",
                  }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr
                key={i}
                style={{ borderBottom: `1px solid ${C.border}` }}
                onMouseEnter={(e) =>
                  ((e.currentTarget as HTMLTableRowElement).style.background = C.cardHover)
                }
                onMouseLeave={(e) =>
                  ((e.currentTarget as HTMLTableRowElement).style.background = "transparent")
                }
              >
                <td style={{ padding: "0.6rem 0.75rem", color: C.text, maxWidth: "160px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {row.email}
                </td>
                <td style={{ padding: "0.6rem 0.75rem", color: C.muted, maxWidth: "180px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {row.source}
                </td>
                <td style={{ padding: "0.6rem 0.75rem" }}>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "0.3rem" }}>
                    {row.owasp_tags.length === 0 ? (
                      <span style={{ color: C.muted }}>—</span>
                    ) : (
                      row.owasp_tags.map((tag) => (
                        <span
                          key={tag}
                          style={{
                            fontSize: "0.7rem",
                            padding: "0.15rem 0.45rem",
                            borderRadius: "99px",
                            background: "rgba(52,211,153,0.12)",
                            color: C.accent,
                            border: `1px solid rgba(52,211,153,0.25)`,
                            whiteSpace: "nowrap",
                          }}
                        >
                          {tag}
                        </span>
                      ))
                    )}
                  </div>
                </td>
                <td style={{ padding: "0.6rem 0.75rem" }}>
                  <span
                    style={{
                      fontSize: "0.72rem",
                      fontWeight: 700,
                      padding: "0.2rem 0.55rem",
                      borderRadius: "6px",
                      background: `${riskColor(row.risk_score)}22`,
                      color: riskColor(row.risk_score),
                      border: `1px solid ${riskColor(row.risk_score)}44`,
                      whiteSpace: "nowrap",
                    }}
                  >
                    {row.risk_score > 0 ? `${row.risk_score} · ${riskLabel(row.risk_score)}` : "—"}
                  </span>
                </td>
                <td style={{ padding: "0.6rem 0.75rem", color: row.blocked_count > 0 ? C.danger : C.muted, textAlign: "center" }}>
                  {row.blocked_count > 0 ? row.blocked_count : "—"}
                </td>
                <td style={{ padding: "0.6rem 0.75rem", color: C.muted, whiteSpace: "nowrap" }}>
                  {fmtTimestamp(row.timestamp)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function PulsePage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const fetchData = () => {
    setLoading(true);
    setError(false);
    fetch(`${API_URL}/api/dashboard`)
      .then((r) => {
        if (!r.ok) throw new Error("Non-2xx");
        return r.json();
      })
      .then((d: DashboardData) => {
        setData(d);
        setLastRefresh(new Date());
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
  }, []);

  const empty: DashboardData = {
    total_scans: 0,
    avg_risk_score: 0,
    steps_blocked: 0,
    active_users: 0,
    owasp_breakdown: [],
    enforcement_summary: { allowed: 0, blocked: 0, held: 0 },
    recent_sessions: [],
  };

  const d = data ?? empty;

  return (
    <>
      {/* Inline keyframes — avoids globals.css dependency */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
        @keyframes fade-in { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
        @keyframes pulse-sk { 0%,100% { opacity:0.4; } 50% { opacity:0.8; } }
        .pulse-page * { box-sizing: border-box; }
        .pulse-page { font-family: 'DM Sans', system-ui, sans-serif; }
        .btn-back:hover { background: #1e293b !important; }
        .btn-refresh:hover { background: rgba(52,211,153,0.18) !important; }
      `}</style>

      <div
        className="pulse-page"
        style={{
          minHeight: "100vh",
          background: `
            radial-gradient(ellipse 80% 50% at 50% -20%, rgba(52,211,153,0.12), transparent),
            radial-gradient(ellipse 60% 40% at 100% 0%, rgba(99,102,241,0.07), transparent),
            ${C.bg}
          `,
          color: C.text,
          WebkitFontSmoothing: "antialiased",
        }}
      >
        {/* ── Header ─────────────────────────────────────── */}
        <header
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "1rem 2rem",
            borderBottom: `1px solid ${C.border}`,
            background: "rgba(13,18,32,0.6)",
            backdropFilter: "blur(12px)",
            position: "sticky",
            top: 0,
            zIndex: 10,
            flexWrap: "wrap",
            gap: "0.75rem",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "1.25rem" }}>
            <a
              href="/"
              className="btn-back"
              style={{
                fontSize: "0.82rem",
                color: C.muted,
                textDecoration: "none",
                padding: "0.4rem 0.85rem",
                borderRadius: "8px",
                border: `1px solid ${C.border}`,
                background: "transparent",
                transition: "background 0.2s",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.35rem",
              }}
            >
              ← Back to SecBrief
            </a>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
                <span
                  style={{
                    width: "8px",
                    height: "8px",
                    borderRadius: "50%",
                    background: C.accent,
                    boxShadow: `0 0 8px ${C.accent}`,
                    animation: "pulse-sk 2s ease-in-out infinite",
                    display: "inline-block",
                  }}
                />
                <span style={{ fontWeight: 700, fontSize: "1.05rem" }}>SecBrief Pulse</span>
              </div>
              <p style={{ fontSize: "0.72rem", color: C.muted, marginTop: "0.1rem" }}>
                Live ArmorIQ data
                {lastRefresh && (
                  <> · refreshed {lastRefresh.toLocaleTimeString()}</>
                )}
              </p>
            </div>
          </div>

          <button
            onClick={fetchData}
            disabled={loading}
            className="btn-refresh"
            style={{
              fontSize: "0.8rem",
              color: C.accent,
              background: "rgba(52,211,153,0.08)",
              border: `1px solid rgba(52,211,153,0.3)`,
              borderRadius: "8px",
              padding: "0.4rem 1rem",
              cursor: loading ? "not-allowed" : "pointer",
              opacity: loading ? 0.6 : 1,
              transition: "background 0.2s",
            }}
          >
            {loading ? "Loading…" : "↺ Refresh"}
          </button>
        </header>

        {/* ── Error state ─────────────────────────────────── */}
        {error && (
          <div
            style={{
              margin: "2rem auto",
              maxWidth: "500px",
              padding: "1.25rem 1.5rem",
              background: "rgba(248,113,113,0.08)",
              border: `1px solid rgba(248,113,113,0.3)`,
              borderRadius: "12px",
              color: C.danger,
              fontSize: "0.9rem",
              textAlign: "center",
            }}
          >
            Could not load dashboard data. Make sure the backend is running.
            <br />
            <button
              onClick={fetchData}
              style={{
                marginTop: "0.75rem",
                fontSize: "0.8rem",
                color: C.danger,
                background: "transparent",
                border: `1px solid ${C.danger}`,
                borderRadius: "6px",
                padding: "0.3rem 0.75rem",
                cursor: "pointer",
              }}
            >
              Try again
            </button>
          </div>
        )}

        {/* ── Main content ─────────────────────────────────── */}
        <main
          style={{
            maxWidth: "1200px",
            margin: "0 auto",
            padding: "2rem 1.5rem",
            display: "flex",
            flexDirection: "column",
            gap: "1.5rem",
            animation: "fade-in 0.35s ease-out",
          }}
        >
          {/* Stat cards */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
              gap: "1rem",
            }}
          >
            <StatCard
              label="Total Scans"
              value={d.total_scans}
              sub="all time"
              loading={loading}
            />
            <StatCard
              label="Avg Risk Score"
              value={d.avg_risk_score > 0 ? d.avg_risk_score.toFixed(1) : "—"}
              sub="0–10 scale"
              accent={d.avg_risk_score >= 7 ? C.danger : d.avg_risk_score >= 4 ? C.warn : C.accent}
              loading={loading}
            />
            <StatCard
              label="Steps Blocked"
              value={d.steps_blocked}
              sub="by ArmorIQ policy"
              accent={d.steps_blocked > 0 ? C.danger : C.text}
              loading={loading}
            />
            <StatCard
              label="Active Users"
              value={d.active_users}
              sub="unique emails today"
              accent={C.accent}
              loading={loading}
            />
          </div>

          {/* Charts row */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
              gap: "1rem",
              alignItems: "start",
            }}
          >
            <OWASPChart data={d.owasp_breakdown} loading={loading} />
            <DonutChart data={d.enforcement_summary} loading={loading} />
          </div>

          {/* Sessions table */}
          <SessionsTable rows={d.recent_sessions} loading={loading} />
        </main>

        <footer
          style={{
            textAlign: "center",
            fontSize: "0.7rem",
            color: "#334155",
            padding: "1.5rem",
          }}
        >
          SecBrief Pulse · read-only view · data from local ArmorIQ audit log
        </footer>
      </div>
    </>
  );
}
