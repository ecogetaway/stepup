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
}

const formatStepLabel = (step: TraceStep, index: number): string => {
  if (step.step === "plan" && Array.isArray((step as { sub_queries?: string[] }).sub_queries)) {
    const subQueries = (step as { sub_queries: string[] }).sub_queries;
    return `${index + 1}. Plan — ${subQueries.length} sub-queries`;
  }
  if (step.step === "tool_call" && step.tool) {
    const querySuffix = step.query ? ` ("${step.query.slice(0, 48)}${step.query.length > 48 ? "…" : ""}")` : "";
    const reusedSuffix = step.reused ? " [reused]" : "";
    return `${index + 1}. Tool — ${step.tool}${querySuffix}${reusedSuffix}`;
  }
  if (step.step === "context_built") {
    return `${index + 1}. Context built — ${step.chunks_used ?? 0} chunks`;
  }
  if (step.step === "citations_attached") {
    return `${index + 1}. Citations attached — ${step.count ?? 0}`;
  }
  if (step.step === "aggregated") {
    return `${index + 1}. Aggregated — ${step.total_chunks ?? 0} chunks`;
  }
  return `${index + 1}. ${step.step ?? "step"}`;
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
    <section className="rounded-xl bg-white p-5 shadow-sm">
      <button
        type="button"
        className="flex w-full items-center justify-between gap-3 text-left text-lg font-semibold text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        aria-expanded={isOpen}
        aria-controls="agent-trace"
        onClick={handleToggle}
      >
        <span>Agent Trace</span>
        <span className="text-sm font-medium text-gray-500">
          {isOpen ? "Hide details" : "Show details"}
        </span>
      </button>

      {traceSteps.length > 0 ? (
        <ol className="mt-4 list-decimal space-y-2 pl-5 text-sm text-gray-700">
          {traceSteps.map((step, index) => (
            <li key={`${step.step ?? "step"}-${step.tool ?? index}`}>
              {formatStepLabel(step, index)}
            </li>
          ))}
        </ol>
      ) : null}

      {isOpen ? (
        <pre
          id="agent-trace"
          className="mt-4 max-h-96 overflow-auto rounded-lg bg-gray-900 p-4 font-mono text-xs leading-6 text-green-400"
        >
          {JSON.stringify(trace, null, 2)}
        </pre>
      ) : null}
    </section>
  );
};
