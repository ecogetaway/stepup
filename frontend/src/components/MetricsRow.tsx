import { AgentBadge } from "./AgentBadge";
import { ConfidenceMeter } from "./ConfidenceMeter";

interface MetricsRowProps {
  confidence: number;
  agent: string;
  latencyMs: number;
}

const getLatencyClass = (latencyMs: number) => {
  if (latencyMs < 1000) return "text-emerald-600";
  if (latencyMs < 3000) return "text-amber-600";
  return "text-red-600";
};

export const MetricsRow = ({ confidence, agent, latencyMs }: MetricsRowProps) => {
  return (
    <section className="grid gap-4 sm:grid-cols-3">
      <article className="rounded-xl border border-slate-100 bg-white p-4 shadow-sm">
        <ConfidenceMeter confidence={confidence} />
      </article>

      <article className="rounded-xl border border-slate-100 bg-white p-4 shadow-sm">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Agent
        </span>
        <div className="mt-3">
          <AgentBadge agent={agent} />
        </div>
      </article>

      <article className="rounded-xl border border-slate-100 bg-white p-4 shadow-sm">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Latency
        </span>
        <p className={`mt-2 text-2xl font-bold ${getLatencyClass(latencyMs)}`}>
          {latencyMs}
          <span className="ml-1 text-sm font-medium text-slate-400">ms</span>
        </p>
      </article>
    </section>
  );
};
