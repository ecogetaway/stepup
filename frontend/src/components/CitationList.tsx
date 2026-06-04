import type { Citation } from "../types/api";

interface CitationListProps {
  citations: Citation[];
}

const getScoreDotClass = (score: number) => {
  if (score >= 0.7) return "bg-green-500";
  if (score >= 0.5) return "bg-amber-500";
  return "bg-red-500";
};

const truncateText = (text: string, maxLength = 180) => {
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength).trim()}...`;
};

export const CitationList = ({ citations }: CitationListProps) => {
  if (citations.length === 0) {
    return (
      <section className="rounded-xl bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900">Citations</h2>
        <p className="mt-3 text-sm text-gray-500">No citations returned.</p>
      </section>
    );
  }

  return (
    <section className="rounded-xl bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-gray-900">Citations</h2>
      <div className="mt-4 space-y-3">
        {citations.map((citation, index) => (
          <article
            key={`${citation.source_title}-${index}`}
            className="rounded-lg border border-gray-100 bg-gray-50 p-4"
          >
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={`h-3 w-3 rounded-full ${getScoreDotClass(citation.overlap_score)}`}
                aria-label={`Overlap score ${citation.overlap_score.toFixed(2)}`}
                title={`Overlap score ${citation.overlap_score.toFixed(2)}`}
              />
              <h3 className="text-sm font-semibold text-gray-900">
                {citation.source_title}
              </h3>
              <span className="rounded-full bg-white px-2 py-1 text-xs font-semibold uppercase tracking-wide text-gray-600 ring-1 ring-gray-200">
                {citation.doc_type}
              </span>
              <span className="text-xs font-medium text-gray-500">
                {citation.overlap_score.toFixed(2)}
              </span>
            </div>
            <p className="mt-3 text-sm leading-6 text-gray-600">
              {truncateText(citation.chunk_text)}
            </p>
            {citation.source_url ? (
              <p className="mt-2 truncate text-xs text-gray-400">{citation.source_url}</p>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
};
