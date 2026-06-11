import type { QueryResponse } from "../types/api";

interface EscalationBannerProps {
  response: QueryResponse;
}

export const EscalationBanner = ({ response }: EscalationBannerProps) => {
  if (response.blocked) {
    return (
      <div
        className="rounded-xl border border-red-200 bg-gradient-to-r from-red-50 to-rose-50 p-4 text-sm font-medium text-red-900 shadow-sm"
        role="status"
        aria-live="polite"
      >
        <span className="font-semibold">🛡️ Blocked by security guardrail</span>
        <p className="mt-1 leading-6 text-red-800">
          This query asks for restricted or sensitive information. No answer was
          generated; the request was logged and routed to the security team.
        </p>
      </div>
    );
  }

  if (response.out_of_scope) {
    return (
      <div
        className="rounded-xl border border-sky-200 bg-gradient-to-r from-sky-50 to-indigo-50 p-4 text-sm font-medium text-sky-900 shadow-sm"
        role="status"
        aria-live="polite"
      >
        <span className="font-semibold">📚 Outside the knowledge base</span>
        <p className="mt-1 leading-6 text-sky-800">
          No sufficiently relevant sources were found, so no answer was invented.
          Escalated to a human agent and logged as a knowledge gap.
        </p>
      </div>
    );
  }

  if (!response.escalated) return null;

  return (
    <div
      className="rounded-xl border border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50 p-4 text-sm font-medium text-amber-900 shadow-sm"
      role="status"
      aria-live="polite"
    >
      <span className="font-semibold">Escalated to human support</span>
      <p className="mt-1 leading-6 text-amber-800">
        Confidence is below the configured threshold. A support agent should review
        this response.
      </p>
    </div>
  );
};
