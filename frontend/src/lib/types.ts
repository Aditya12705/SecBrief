export type Decision = {
  action: string;
  mcp: string;
  status: string;
  message: string;
  simulated: boolean;
  csrg_path?: string;
  in_signed_plan?: boolean;
};

export type IntentReceipt = {
  plan_hash: string;
  token_id: string;
  merkle_root?: string;
  total_steps: number;
  expires_in_seconds?: number;
  step_proofs_count?: number;
  armoriq_live?: boolean;
};

export type Analysis = {
  title?: string;
  severity?: string;
  risk_score?: number;
  summary?: string;
  formatted?: string;
  repo?: string;
  owasp_category?: string;
  cwe_id?: string;
  soc2_controls?: string[];
  financial_impact_inr?: string;
  heuristic_findings?: { signal: string; note: string; severity: string }[];
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  text: string;
  analysis?: Analysis;
  decisions?: Decision[];
  receipt?: IntentReceipt;
  meta?: string;
};

export type DemoRepo = {
  url: string;
  label: string;
  stack: string;
  why: string;
};

export type InputMode = "github" | "paste" | "code" | "demo";

export type WorkflowStep = "input" | "analyze" | "plan" | "enforce";
