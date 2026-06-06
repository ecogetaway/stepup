import { useState } from "react";

interface TraceViewerProps {
  trace: Record<string, unknown>;
}

interface TraceStep {
  step?: string;
  tool?: string;
  query?: string;
  chunks_used?: number;
  count?: number;
  total_chunks?: number;
  reused?: boolean;
  sub_queries?: string[];
}

const getToolMeta = (tool?: string) => {
  if (tool === "ticket_lookup") {
    return { icon: "🎫", color: "bg-sky-500", label: "Ticket Lookup" };
  }
  if (tool === "document_search") {
    return { icon: "📄", color: "bg-violet-500", label: "Document Search" };
  }
  if (tool === "summarizer") {
    return { icon: "✨", color: "bg-indigo-500", label: "Summarizer" };
  }
  return { icon: "⚙️", color: "bg-slate-400", label: tool ?? "Step" };
};

const getStepTitle = (step: TraceStep): string => {
  if (step.step === "plan" && Array.isArray(step.sub_queries)) {
    return `Plan — ${step.sub_queries.length} sub-queries`;
  }
  if (step.step === "tool_call" && step.tool) {
    return getToolMeta(step.tool).label;
  }
  if (step.step === "context_built") {
    return `Context built (${step.chunks_used ?? 0} chunks)`;
  }
  if (step.step === "citations_attached") {
    return `Citations attached (${step.count ?? 0})`;
  }
  if (step.step === "aggregated") {
    return `Aggregated ${step.total_chunks ?? 0} chunks`;
  }
  return step.step ?? "Step";
};

const getStepDetail = (step: TraceStep): string | null => {
  if (step.step === "tool_call" && step.query) {
    const truncated =
      step.query.length > 56 ? `${step.query.slice(0, 56)}…` : step.query;
    return `${truncated}${step.reused ? " · reused" : ""}`;
  }
  if (step.step === "plan" && Array.isArray(step.sub_queries)) {
    return step.sub_queries.slice(0, 2).join(" · ");
  }
  return null;
};

const getTraceSteps = (trace: Record<string, unknown>): TraceStep[] => {
  const steps = trace.steps;
  if (Array.isArray(steps)) {
    return steps as TraceStep[];
  }
  return [];
};

export const TraceViewer = ({ trace }: TraceViewerProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const traceSteps = getTraceSteps(trace);

  const handleToggle = () => {
    setIsOpen((currentValue) => !currentValue);
  };

  return (
    <section className="rounded-xl border border-slate-100 bg-white p-5 shadow-sm">
      <button
        type="button"
        className="flex w-full items-center justify-between gap-3 text-left text-lg font-semibold text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        aria-expanded={isOpen}
        aria-controls="agent-trace"
        onClick={handleToggle}
      >
        <span>Agent Trace</span>
        <span className="text-sm font-medium text-slate-500">
          {isOpen ? "Hide raw JSON" : "Show raw JSON"}
        </span>
      </button>

      {traceSteps.length > 0 ? (
        <ol className="relative mt-6 space-y-0">
          {traceSteps.map((step, index) => {
            const isLast = index === traceSteps.length - 1;
            const meta =
              step.step === "tool_call" ? getToolMeta(step.tool) : getToolMeta(step.step);
            const detail = getStepDetail(step);

            return (
              <li key={`${step.step ?? "step"}-${step.tool ?? index}`} className="relative flex gap-4 pb-6">
                {!isLast ? (
                  <span
                    aria-hidden="true"
                    className="absolute left-[15px] top-8 h-[calc(100%-8px)] w-0.5 bg-slate-200"
                  />
                ) : null}
                <span
                  aria-hidden="true"
                  className={`relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm text-white ${meta.color}`}
                >
                  {meta.icon}
                </span>
                <div className="min-w-0 pt-0.5">
                  <p className="text-sm font-semibold text-slate-900">{getStepTitle(step)}</p>
                  {detail ? <p className="mt-1 text-xs leading-5 text-slate-500">{detail}</p> : null}
                </div>
              </li>
            );
          })}
        </ol>
      ) : null}

      {isOpen ? (
        <pre
          id="agent-trace"
          className="mt-2 max-h-96 overflow-auto rounded-lg bg-slate-900 p-4 font-mono text-xs leading-6 text-emerald-400"
        >
          {JSON.stringify(trace, null, 2)}
        </pre>
      ) : null}
    </section>
  );
};
