import type { QueryRequest, QueryResponse } from "../types/api";

const API_BASE_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(
  /\/$/,
  "",
);
const QUERY_TIMEOUT_MS = 180_000;

interface HealthResponse {
  status: string;
  env: string;
}

const parseErrorMessage = async (response: Response) => {
  try {
    const payload = (await response.json()) as { detail?: string; error?: string };
    return payload.detail ?? payload.error ?? response.statusText;
  } catch {
    return response.statusText;
  }
};

export const fetchHealth = async (): Promise<HealthResponse> => {
  const response = await fetch(`${API_BASE_URL}/health`);

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  return response.json() as Promise<HealthResponse>;
};

export const query = async (request: QueryRequest): Promise<QueryResponse> => {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), QUERY_TIMEOUT_MS);

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(await parseErrorMessage(response));
    }

    return response.json() as Promise<QueryResponse>;
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error(
        `Request timed out after ${QUERY_TIMEOUT_MS / 1000} seconds. The first query can be slow while models warm up — please try again.`,
      );
    }

    throw error;
  } finally {
    window.clearTimeout(timeoutId);
  }
};
