import type { QueryResponse } from "../types/api";
import { AnswerMarkdown } from "./AnswerMarkdown";
import { BridgeBriefPanel } from "./BridgeBriefPanel";
import { CitationList } from "./CitationList";
import { EscalationBanner } from "./EscalationBanner";
import { MetricsRow } from "./MetricsRow";
import { TraceViewer } from "./TraceViewer";

interface AnswerPanelProps {
  response: QueryResponse | null;
  isLoading: boolean;
}

const LoadingSkeleton = () => (
  <div
    className="space-y-4 rounded-xl border border-slate-100 bg-white p-6 shadow-sm"
    aria-label="Loading answer"
  >
    <p className="text-sm text-slate-600">
      Routing query → retrieving sources → synthesizing cited answer…
    </p>
    <div className="h-5 w-48 animate-pulse rounded bg-slate-200" />
    <div className="space-y-3">
      <div className="h-4 animate-pulse rounded bg-slate-200" />
      <div className="h-4 w-11/12 animate-pulse rounded bg-slate-200" />
      <div className="h-4 w-3/4 animate-pulse rounded bg-slate-200" />
    </div>
    <div className="grid gap-3 sm:grid-cols-3">
      <div className="h-20 animate-pulse rounded-xl bg-slate-100" />
      <div className="h-20 animate-pulse rounded-xl bg-slate-100" />
      <div className="h-20 animate-pulse rounded-xl bg-slate-100" />
    </div>
  </div>
);

export const AnswerPanel = ({ response, isLoading }: AnswerPanelProps) => {
  if (isLoading) return <LoadingSkeleton />;

  if (!response) {
    return (
      <section className="rounded-xl border border-dashed border-slate-200 bg-white/70 p-10 text-center shadow-sm">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 text-2xl">
          💬
        </div>
        <h2 className="mt-4 text-lg font-semibold text-slate-900">Ready for a question</h2>
        <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">
          Ask about SOPs, incidents, tickets, or runbooks — or pick a suggestion below to
          start the demo.
        </p>
      </section>
    );
  }

  return (
    <div className="space-y-6">
      {response.bridge_brief ? <BridgeBriefPanel brief={response.bridge_brief} /> : null}

      <section className="rounded-xl border border-slate-100 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Answer</h2>
        <div className="mt-4">
          <AnswerMarkdown content={response.answer} />
        </div>
      </section>

      <MetricsRow
        agent={response.agent_used}
        confidence={response.confidence}
        latencyMs={response.retrieval_ms}
      />

      <EscalationBanner response={response} />
      <CitationList citations={response.citations} />
      <TraceViewer trace={response.trace} />
    </div>
  );
};
