import { useState } from "react";
import type { IncidentBridgeBrief } from "../types/api";

interface BridgeBriefPanelProps {
  brief: IncidentBridgeBrief;
}

const formatBriefForCopy = (brief: IncidentBridgeBrief) => {
  const section = (title: string, bullets: string[]) =>
    `${title}\n${bullets.map((bullet) => `- ${bullet}`).join("\n")}`;

  return [
    "INCIDENT BRIDGE BRIEF",
    `Severity: ${brief.severity}`,
    `Status: ${brief.status}`,
    brief.incident_id ? `Incident ID: ${brief.incident_id}` : null,
    "",
    "EXECUTIVE SUMMARY",
    brief.executive_summary,
    "",
    section(brief.impact.title, brief.impact.bullets),
    "",
    section(brief.timeline.title, brief.timeline.bullets),
    "",
    section(brief.current_actions.title, brief.current_actions.bullets),
    "",
    section(brief.customer_comms.title, brief.customer_comms.bullets),
    "",
    section(brief.decisions_needed.title, brief.decisions_needed.bullets),
    "",
    "NEXT UPDATE",
    brief.next_update,
  ]
    .filter(Boolean)
    .join("\n");
};

const BriefSection = ({
  title,
  bullets,
}: {
  title: string;
  bullets: string[];
}) => (
  <section className="rounded-lg border border-slate-100 bg-slate-50/80 p-4">
    <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-700">{title}</h3>
    <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-slate-700">
      {bullets.map((bullet) => (
        <li key={`${title}-${bullet}`}>{bullet}</li>
      ))}
    </ul>
  </section>
);

export const BridgeBriefPanel = ({ brief }: BridgeBriefPanelProps) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    const text = formatBriefForCopy(brief);
    await navigator.clipboard.writeText(text);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="rounded-xl border border-indigo-100 bg-gradient-to-br from-white to-indigo-50/40 p-6 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Incident Bridge Brief</h2>
          <p className="mt-1 text-sm text-slate-600">
            Structured output for management bridge calls
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full bg-red-100 px-3 py-1 text-xs font-semibold uppercase text-red-800 ring-1 ring-red-200">
            {brief.severity}
          </span>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700 ring-1 ring-slate-200">
            {brief.status}
          </span>
          <button
            type="button"
            className="rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            aria-label="Copy bridge brief to clipboard"
            onClick={handleCopy}
          >
            {copied ? "Copied" : "Copy brief"}
          </button>
        </div>
      </div>

      <p className="mt-4 rounded-lg border border-slate-100 bg-white p-4 text-sm leading-7 text-slate-800">
        {brief.executive_summary}
      </p>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <BriefSection title={brief.impact.title} bullets={brief.impact.bullets} />
        <BriefSection title={brief.timeline.title} bullets={brief.timeline.bullets} />
        <BriefSection
          title={brief.current_actions.title}
          bullets={brief.current_actions.bullets}
        />
        <BriefSection
          title={brief.customer_comms.title}
          bullets={brief.customer_comms.bullets}
        />
      </div>

      <div className="mt-4 grid gap-4">
        <BriefSection
          title={brief.decisions_needed.title}
          bullets={brief.decisions_needed.bullets}
        />
        <section className="rounded-lg border border-amber-100 bg-amber-50/70 p-4">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-amber-900">
            Next Update
          </h3>
          <p className="mt-2 text-sm leading-6 text-amber-950">{brief.next_update}</p>
        </section>
      </div>
    </section>
  );
};
