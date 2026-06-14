const suggestions = [
  "How do I deploy a Kafka consumer?",
  "Kafka consumer कैसे deploy करें?",
  "What are the Docker security runbook requirements?",
  "What is the VPN setup procedure?",
  "Summarize all P1 deployment tickets this month",
  "Which P1 tickets are at risk of SLA breach?",
  "Generate incident bridge brief for open P1 tickets",
  "Generate an onboarding brief for a new Application Support engineer",
];

interface SuggestionChipsProps {
  onSelect: (suggestion: string) => void;
}

export const SuggestionChips = ({ onSelect }: SuggestionChipsProps) => {
  const handleSuggestionClick = (suggestion: string) => {
    onSelect(suggestion);
  };

  return (
    <div className="rounded-2xl border border-slate-100 bg-white/80 p-4 shadow-sm">
      <h2 className="text-sm font-semibold text-slate-700">Try asking</h2>
      <div className="mt-3 flex flex-wrap gap-2">
        {suggestions.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            className="rounded-full border border-indigo-100 bg-indigo-50/80 px-4 py-2 text-left text-xs font-medium text-indigo-800 transition hover:border-indigo-200 hover:bg-indigo-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            aria-label={`Use suggestion: ${suggestion}`}
            onClick={() => handleSuggestionClick(suggestion)}
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
};
