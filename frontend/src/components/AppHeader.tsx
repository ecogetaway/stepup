interface AppHeaderProps {
  healthStatus: "checking" | "ok" | "error";
  backendEnv: string | null;
}

export const AppHeader = ({ healthStatus, backendEnv }: AppHeaderProps) => {
  const healthClasses = {
    checking: "bg-amber-100 text-amber-800 ring-amber-200",
    ok: "bg-emerald-100 text-emerald-800 ring-emerald-200",
    error: "bg-red-100 text-red-800 ring-red-200",
  }[healthStatus];

  const healthLabel = {
    checking: "Checking backend",
    ok: `Healthy${backendEnv ? ` · ${backendEnv}` : ""}`,
    error: "Backend unavailable",
  }[healthStatus];

  return (
    <header className="border-b border-slate-200/80 bg-white/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 lg:px-8">
        <div className="flex items-center gap-3">
          <div
            aria-hidden="true"
            className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 text-sm font-bold text-white shadow-md shadow-indigo-200"
          >
            EKC
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-slate-900">
              Enterprise Knowledge Copilot
            </h1>
            <p className="text-xs font-medium text-slate-500">Team Vipers · RAG + Agentic Workflows</p>
          </div>
        </div>

        <span
          className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold ring-1 ${healthClasses}`}
          aria-live="polite"
        >
          <span
            className={`h-2 w-2 rounded-full ${
              healthStatus === "ok"
                ? "bg-emerald-500"
                : healthStatus === "checking"
                  ? "animate-pulse bg-amber-500"
                  : "bg-red-500"
            }`}
          />
          {healthLabel}
        </span>
      </div>
    </header>
  );
};
