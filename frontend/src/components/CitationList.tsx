import { useState } from "react";
import type { Citation } from "../types/api";

interface CitationListProps {
  citations: Citation[];
}

const VISIBLE_LIMIT = 5;

const getDocTypeStyles = (docType: string) => {
  if (docType === "ticket") {
    return {
      border: "border-l-4 border-l-sky-500",
      badge: "bg-sky-100 text-sky-800 ring-sky-200",
      label: "Ticket",
    };
  }
  if (docType === "sop") {
    return {
      border: "border-l-4 border-l-violet-500",
      badge: "bg-violet-100 text-violet-800 ring-violet-200",
      label: "SOP",
    };
  }
  return {
    border: "border-l-4 border-l-slate-400",
    badge: "bg-slate-100 text-slate-700 ring-slate-200",
    label: docType || "Doc",
  };
};

const getScoreDotClass = (score: number) => {
  if (score >= 0.7) return "bg-emerald-500";
  if (score >= 0.5) return "bg-amber-500";
  return "bg-red-500";
};

const truncateText = (text: string, maxLength = 180) => {
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength).trim()}...`;
};

export const CitationList = ({ citations }: CitationListProps) => {
  const [showAll, setShowAll] = useState(false);

  if (citations.length === 0) {
    return (
      <section className="rounded-xl border border-slate-100 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Citations</h2>
        <p className="mt-3 text-sm text-slate-500">No citations returned.</p>
      </section>
    );
  }

  const visibleCitations = showAll ? citations : citations.slice(0, VISIBLE_LIMIT);
  const hiddenCount = citations.length - VISIBLE_LIMIT;

  const handleToggle = () => {
    setShowAll((current) => !current);
  };

  return (
    <section className="rounded-xl border border-slate-100 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-slate-900">Citations</h2>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
          {citations.length} sources
        </span>
      </div>

      <div className="mt-4 space-y-3">
        {visibleCitations.map((citation, index) => {
          const typeStyles = getDocTypeStyles(citation.doc_type);
          return (
            <article
              key={`${citation.source_title}-${citation.source_url}-${index}`}
              className={`rounded-lg border border-slate-100 bg-slate-50/80 p-4 ${typeStyles.border}`}
            >
              <div className="flex flex-wrap items-center gap-2">
                <span
                  className={`h-2.5 w-2.5 rounded-full ${getScoreDotClass(citation.overlap_score)}`}
                  aria-label={`Overlap score ${citation.overlap_score.toFixed(2)}`}
                  title={`Overlap score ${citation.overlap_score.toFixed(2)}`}
                />
                <h3 className="text-sm font-semibold text-slate-900">
                  {citation.source_title}
                </h3>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-semibold uppercase tracking-wide ring-1 ${typeStyles.badge}`}
                >
                  {typeStyles.label}
                </span>
                <span className="text-xs font-medium text-slate-500">
                  {citation.overlap_score.toFixed(2)}
                </span>
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-600">
                {truncateText(citation.chunk_text)}
              </p>
              {citation.source_url ? (
                <p className="mt-2 truncate text-xs text-slate-400">{citation.source_url}</p>
              ) : null}
            </article>
          );
        })}
      </div>

      {hiddenCount > 0 ? (
        <button
          type="button"
          className="mt-4 text-sm font-semibold text-indigo-600 hover:text-indigo-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          aria-expanded={showAll}
          onClick={handleToggle}
        >
          {showAll ? "Show fewer citations" : `Show ${hiddenCount} more citations`}
        </button>
      ) : null}
    </section>
  );
};
