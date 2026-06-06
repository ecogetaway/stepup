import type { KeyboardEvent } from "react";

interface QueryInputProps {
  queryText: string;
  isLoading: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
}

export const QueryInput = ({
  queryText,
  isLoading,
  onChange,
  onSubmit,
}: QueryInputProps) => {
  const isSubmitDisabled = queryText.trim().length === 0 || isLoading;

  const handleSubmit = () => {
    if (isSubmitDisabled) return;
    onSubmit();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      handleSubmit();
    }
  };

  return (
    <section className="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
      <label className="block space-y-3">
        <span className="text-sm font-semibold text-slate-700">Ask a question</span>
        <textarea
          className="min-h-36 w-full resize-y rounded-xl border border-slate-200 bg-slate-50/50 p-4 text-base leading-7 text-slate-900 shadow-inner outline-none transition placeholder:text-slate-400 focus:border-indigo-500 focus:bg-white focus:ring-2 focus:ring-indigo-100"
          placeholder="Ask about SOPs, runbooks, tickets, or deployment procedures..."
          value={queryText}
          aria-label="Enterprise knowledge query"
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={handleKeyDown}
        />
      </label>

      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-xs text-slate-500">Press Cmd+Enter or Ctrl+Enter to submit.</p>
        <button
          type="button"
          className="inline-flex min-h-11 items-center justify-center rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-6 py-2.5 text-sm font-semibold text-white shadow-md shadow-indigo-200 transition hover:from-indigo-700 hover:to-violet-700 disabled:cursor-not-allowed disabled:from-slate-300 disabled:to-slate-300 disabled:shadow-none focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          disabled={isSubmitDisabled}
          aria-disabled={isSubmitDisabled}
          onClick={handleSubmit}
        >
          {isLoading ? "Fetching answer..." : "Get Answer"}
        </button>
      </div>
    </section>
  );
};
