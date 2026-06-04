import { useMemo, useState } from "react";
import type { AgentMode, QueryResponse } from "../types/api";
import { query as queryApi } from "../utils/api";

const SESSION_STORAGE_KEY = "enterprise-copilot-session-id";

const createSessionId = () => {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;
};

const getSessionId = () => {
  const existingSessionId = window.localStorage.getItem(SESSION_STORAGE_KEY);

  if (existingSessionId) return existingSessionId;

  const sessionId = createSessionId();
  window.localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  return sessionId;
};

export interface QueryState {
  data: QueryResponse | null;
  error: string | null;
  isLoading: boolean;
  submitQuery: (queryText: string, topK: number, agentMode: AgentMode) => Promise<void>;
}

export const useQuery = (): QueryState => {
  const [data, setData] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const sessionId = useMemo(getSessionId, []);

  const submitQuery = async (queryText: string, topK: number, agentMode: AgentMode) => {
    const trimmedQuery = queryText.trim();

    if (!trimmedQuery) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await queryApi({
        query: trimmedQuery,
        top_k: topK,
        force_agent: agentMode === "auto" ? null : agentMode,
        session_id: sessionId,
      });

      setData(response);
    } catch (caughtError) {
      const message =
        caughtError instanceof Error ? caughtError.message : "Something went wrong.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return { data, error, isLoading, submitQuery };
};
