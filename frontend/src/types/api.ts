export interface Citation {
  source_title: string;
  source_url: string;
  chunk_text: string;
  overlap_score: number;
  doc_type: string;
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
}

export type AgentMode = "auto" | "react" | "plan_execute";
