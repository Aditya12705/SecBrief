import type { Decision, DemoRepo, IntentReceipt } from "./types";

/** Empty = same origin (Hugging Face all-in-one deploy). */
export const API_BASE = (((globalThis as any).process?.env?.NEXT_PUBLIC_API_URL ?? "http://localhost:8000") as string).replace(
  /\/$/,
  ""
);

async function parseResponse<T>(r: Response): Promise<T> {
  const text = await r.text();
  if (!r.ok) {
    let detail = r.statusText || `HTTP ${r.status}`;
    if (text) {
      try {
        const err = JSON.parse(text) as { detail?: string | unknown };
        if (typeof err.detail === "string") detail = err.detail;
        else if (err.detail) detail = JSON.stringify(err.detail);
        else detail = text.slice(0, 200);
      } catch {
        detail = text.slice(0, 200);
      }
    }
    if (r.status === 0 || detail === "Failed to fetch") {
      throw new Error(
        `Cannot reach backend at ${API_BASE}. Start it with: cd backend && python -m uvicorn main:app --reload --port 8000`
      );
    }
    throw new Error(detail);
  }
  if (!text.trim()) {
    throw new Error(
      `Empty response from server. Check CORS (frontend port) and that the backend is running on ${API_BASE}.`
    );
  }
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new Error(`Invalid JSON from server: ${text.slice(0, 120)}`);
  }
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseResponse<T>(r);
}

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`);
  return parseResponse<T>(r);
}

export async function fetchDemoRepos(): Promise<{ repos: DemoRepo[] }> {
  return get("/api/demo-repos");
}

export async function fetchSampleAlert(): Promise<{ text: string }> {
  return get("/api/sample-alert");
}

export async function parseUpload(file: File) {
  const form = new FormData();
  form.append("file", file);
  const r = await fetch(`${API_BASE}/api/parse-upload`, { method: "POST", body: form });
  return parseResponse<{
    format: string;
    alert_text: string;
    title: string;
    finding_count: number;
    cve_ids?: string[];
  }>(r);
}

export function explainAlert(email: string, alert_text: string, session_id?: string) {
  return post<{
    analysis: Record<string, unknown>;
    explanation: string;
    source: string;
    session_id: string;
    cve_ids?: string[];
  }>("/api/explain", { email, alert_text, session_id });
}

export function auditCode(email: string, code: string, session_id?: string) {
  return post<{
    analysis: Record<string, unknown>;
    explanation: string;
    source: string;
    session_id: string;
  }>("/api/audit-code", { email, code, session_id });
}

export function scanGithub(
  email: string,
  repo_url: string,
  session_id?: string,
  deep_scan = true
) {
  return post<{
    scan: Record<string, unknown>;
    analysis: Record<string, unknown>;
    analysis_source: string;
    session_id: string;
  }>("/api/github/scan", { email, repo_url, session_id, deep_scan });
}

export function planFix(
  email: string,
  alert_text: string,
  opts?: {
    user_request?: string;
    session_id?: string;
    simulate_attack?: boolean;
    use_delegation_demo?: boolean;
  }
) {
  return post<{
    plan: { goal: string; steps: { action: string; description?: string }[] };
    decisions: Decision[];
    summary: string;
    armoriq_live: boolean;
    intent_receipt: IntentReceipt;
    plan_source: string;
    session_id: string;
    delegation_demo?: { scenario: string; message: string }[];
  }>("/api/plan-fix", {
    email,
    alert_text,
    user_request: opts?.user_request || "Create a safe remediation plan",
    session_id: opts?.session_id,
    simulate_attack: opts?.simulate_attack ?? false,
    use_delegation_demo: opts?.use_delegation_demo ?? false,
  });
}

export async function exportBrief(body: {
  email: string;
  session_id?: string;
  alert_text?: string;
  analysis?: Record<string, unknown> | null;
  plan?: { goal: string; steps: unknown[] } | null;
  decisions?: Decision[];
  receipt?: IntentReceipt | null;
}) {
  const r = await fetch(`${API_BASE}/api/export-brief`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const text = await r.text();
  if (!r.ok) {
    throw new Error(text || "Export failed");
  }
  return text;
}

export function authSignup(email: string) {
  return post<{
    email: string;
    api_key: string;
    plan: string;
    install_snippet: string;
  }>("/api/auth/signup", { email });
}

export function authMe(apiKey: string) {
  return fetch(`${API}/api/auth/me`, {
    headers: { Authorization: `Bearer ${apiKey}` },
  }).then(parseResponse<{ email: string; plan: string; created_at: string }>);
}
