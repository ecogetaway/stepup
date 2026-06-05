import type { QueryResponse } from "../types/api";
import { AgentBadge } from "./AgentBadge";
import { CitationList } from "./CitationList";
import { ConfidenceMeter } from "./ConfidenceMeter";
import { EscalationBanner } from "./EscalationBanner";
import { TraceViewer } from "./TraceViewer";

interface AnswerPanelProps {
  response: QueryResponse | null;
  isLoading: boolean;
}

const LoadingSkeleton = () => (
  <div className="space-y-4 rounded-xl bg-white p-5 shadow-sm" aria-label="Loading answer">
    <p className="text-sm text-gray-600">
      Retrieving documents and generating a cited answer. Usually under 30 seconds.
    </p>
    <div className="h-5 w-40 animate-pulse rounded bg-gray-200" />
    <div className="space-y-3">
      <div className="h-4 animate-pulse rounded bg-gray-200" />
      <div className="h-4 w-11/12 animate-pulse rounded bg-gray-200" />
      <div className="h-4 w-3/4 animate-pulse rounded bg-gray-200" />
    </div>
    <div className="grid gap-3 sm:grid-cols-3">
      <div className="h-20 animate-pulse rounded-lg bg-gray-100" />
      <div className="h-20 animate-pulse rounded-lg bg-gray-100" />
      <div className="h-20 animate-pulse rounded-lg bg-gray-100" />
    </div>
  </div>
);

export const AnswerPanel = ({ response, isLoading }: AnswerPanelProps) => {
  if (isLoading) return <LoadingSkeleton />;

  if (!response) {
    return (
      <section className="rounded-xl bg-white p-8 text-center shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900">Ready for a question</h2>
        <p className="mt-2 text-sm leading-6 text-gray-500">
          Ask about SOPs, incidents, tickets, or runbooks to get a cited answer.
        </p>
      </section>
    );
  }

  return (
    <div className="space-y-6">
      <section className="rounded-xl bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900">Answer</h2>
        <p className="mt-4 whitespace-pre-wrap text-sm leading-7 text-gray-700">
          {response.answer}
        </p>
      </section>

      <CitationList citations={response.citations} />

      <section className="grid gap-4 rounded-xl bg-white p-5 shadow-sm sm:grid-cols-3">
        <ConfidenceMeter confidence={response.confidence} />
        <div className="space-y-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">
            Agent
          </span>
          <div>
            <AgentBadge agent={response.agent_used} />
          </div>
        </div>
        <div className="space-y-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">
            Latency ms
          </span>
          <p className="text-2xl font-bold text-gray-900">{response.retrieval_ms}</p>
        </div>
      </section>

      <EscalationBanner isEscalated={response.escalated} />
      <TraceViewer trace={response.trace} />
    </div>
  );
};
