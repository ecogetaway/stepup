import { useEffect, useState } from "react";
import { AnswerPanel } from "./components/AnswerPanel";
import { QueryInput } from "./components/QueryInput";
import { SuggestionChips } from "./components/SuggestionChips";
import type { AgentMode } from "./types/api";
import { fetchHealth } from "./utils/api";
import { useQuery } from "./hooks/useQuery";

const agentOptions: Array<{
  value: AgentMode;
  label: string;
  explanation: string;
}> = [
  {
    value: "auto",
    label: "Auto",
    explanation: "Routes factual and analytical questions automatically.",
  },
  {
    value: "react",
    label: "ReAct",
    explanation: "Best for direct SOP, runbook, and procedure answers.",
  },
  {
    value: "plan_execute",
    label: "Plan Execute",
    explanation: "Best for comparisons, ticket analysis, and multi-step questions.",
  },
];

const App = () => {
  const [queryText, setQueryText] = useState("");
  const [topK, setTopK] = useState(5);
  const [agentMode, setAgentMode] = useState<AgentMode>("auto");
  const [healthStatus, setHealthStatus] = useState<"checking" | "ok" | "error">(
    "checking",
  );
  const [backendEnv, setBackendEnv] = useState<string | null>(null);
  const { data, error, isLoading, submitQuery } = useQuery();

  useEffect(() => {
    let isMounted = true;

    const pollHealth = async () => {
      try {
        const health = await fetchHealth();
        if (!isMounted) return;
        setHealthStatus(health.status === "ok" ? "ok" : "error");
        setBackendEnv(health.env);
      } catch {
        if (!isMounted) return;
        setHealthStatus("error");
        setBackendEnv(null);
      }
    };

    void pollHealth();
    const intervalId = window.setInterval(pollHealth, 10_000);

    return () => {
      isMounted = false;
      window.clearInterval(intervalId);
    };
  }, []);

  const selectedAgent = agentOptions.find((option) => option.value === agentMode);

  const handleSubmit = async () => {
    await submitQuery(queryText, topK, agentMode);
  };

  const handleSuggestionSelect = (suggestion: string) => {
    setQueryText(suggestion);
  };

  const healthClasses = {
    checking: "bg-amber-100 text-amber-700",
    ok: "bg-green-100 text-green-700",
    error: "bg-red-100 text-red-700",
  }[healthStatus];

  const healthLabel = {
    checking: "Checking backend",
    ok: `Backend healthy${backendEnv ? ` (${backendEnv})` : ""}`,
    error: "Backend unavailable",
  }[healthStatus];

  return (
    <main className="min-h-screen bg-gray-50 text-gray-900">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col gap-6 p-4 lg:flex-row lg:p-8">
        <aside className="w-full shrink-0 lg:w-[30%]">
          <section className="sticky top-8 space-y-6 rounded-xl bg-white p-6 shadow-sm">
            <div className="space-y-2">
              <h1 className="text-2xl font-bold tracking-tight">
                🔍 Enterprise Knowledge Copilot
              </h1>
              <p className="text-sm leading-6 text-gray-600">
                Source-cited answers from documents, SOPs, and tickets
              </p>
            </div>

            <div className="rounded-lg border border-gray-100 bg-gray-50 p-3">
              <span
                className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${healthClasses}`}
                aria-live="polite"
              >
                {healthLabel}
              </span>
            </div>

            <label className="block space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-gray-700">Top K</span>
                <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
                  {topK}
                </span>
              </div>
              <input
                aria-label="Top K retrieval count"
                className="w-full accent-indigo-600"
                max={10}
                min={1}
                type="range"
                value={topK}
                onChange={(event) => setTopK(Number(event.target.value))}
              />
              <p className="text-xs text-gray-500">Retrieve between 1 and 10 citations.</p>
            </label>

            <label className="block space-y-2">
              <span className="text-sm font-semibold text-gray-700">Agent mode</span>
              <select
                aria-label="Agent mode"
                className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                value={agentMode}
                onChange={(event) => setAgentMode(event.target.value as AgentMode)}
              >
                {agentOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <p className="text-xs leading-5 text-gray-500">{selectedAgent?.explanation}</p>
            </label>

            <SuggestionChips onSelect={handleSuggestionSelect} />
          </section>
        </aside>

        <section className="flex w-full flex-col gap-6 lg:w-[70%]">
          {error ? (
            <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm font-medium text-red-700">
              {error}
            </div>
          ) : null}

          <QueryInput
            isLoading={isLoading}
            queryText={queryText}
            onChange={setQueryText}
            onSubmit={handleSubmit}
          />

          <AnswerPanel response={data} isLoading={isLoading} />
        </section>
      </div>
    </main>
  );
};

export default App;
