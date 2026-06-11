export interface SlaStatus {
  state: string;
  due_at: string;
  remaining_minutes: number;
  elapsed_pct: number;
}

export interface Citation {
  source_title: string;
  source_url: string;
  chunk_text: string;
  overlap_score: number;
  doc_type: string;
  sla?: SlaStatus | null;
  full_text?: string;
}

export interface BridgeBriefSection {
  title: string;
  bullets: string[];
}

export interface IncidentBridgeBrief {
  incident_id?: string | null;
  severity: string;
  status: string;
  executive_summary: string;
  impact: BridgeBriefSection;
  timeline: BridgeBriefSection;
  current_actions: BridgeBriefSection;
  customer_comms: BridgeBriefSection;
  decisions_needed: BridgeBriefSection;
  next_update: string;
}

export interface QueryRequest {
  query: string;
  top_k?: number;
  force_agent?: "react" | "plan_execute" | null;
  session_id?: string | null;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  confidence: number;
  escalated: boolean;
  agent_used: string;
  trace: Record<string, any>;
  retrieval_ms: number;
  generation_ms?: number;
  sla_summary?: Record<string, any> | null;
  bridge_brief?: IncidentBridgeBrief | null;
  out_of_scope?: boolean;
  blocked?: boolean;
}

export type AgentMode = "auto" | "react" | "plan_execute";
