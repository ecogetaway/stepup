import { useEffect, useState } from "react";
import { AgentModeCards } from "./components/AgentModeCards";
import { AnswerPanel } from "./components/AnswerPanel";
import { AppHeader } from "./components/AppHeader";
import { QueryInput } from "./components/QueryInput";
import { SuggestionChips } from "./components/SuggestionChips";
import type { AgentMode } from "./types/api";
import { fetchHealth } from "./utils/api";
import { useQuery } from "./hooks/useQuery";

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

  const handleSubmit = async () => {
    await submitQuery(queryText, topK, agentMode);
  };

  const handleSuggestionSelect = (suggestion: string) => {
    setQueryText(suggestion);
    void submitQuery(suggestion, topK, agentMode);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50 text-slate-900">
      <AppHeader backendEnv={backendEnv} healthStatus={healthStatus} />

      <main className="mx-auto max-w-7xl px-4 py-6 lg:px-8 lg:py-8">
        <div className="flex flex-col gap-6 lg:flex-row">
          <aside className="w-full shrink-0 lg:w-[30%]">
            <section className="sticky top-6 space-y-6 rounded-2xl border border-slate-100 bg-white/90 p-6 shadow-sm backdrop-blur-sm">
              <div className="space-y-1">
                <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                  Configuration
                </h2>
                <p className="text-sm leading-6 text-slate-600">
                  Tune retrieval and choose how the agent reasons over your knowledge
                  base.
                </p>
              </div>

              <AgentModeCards value={agentMode} onChange={setAgentMode} />

              <label className="block space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-slate-700">Top K sources</span>
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
                <p className="text-xs text-slate-500">Retrieve between 1 and 10 citations.</p>
              </label>
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

            <SuggestionChips onSelect={handleSuggestionSelect} />

            <AnswerPanel isLoading={isLoading} response={data} />
          </section>
        </div>
      </main>
    </div>
  );
};

export default App;
