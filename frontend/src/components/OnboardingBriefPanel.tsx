import { useState } from "react";
import type { OnboardingBrief } from "../types/api";

interface OnboardingBriefPanelProps {
  brief: OnboardingBrief;
}

const formatBriefForCopy = (brief: OnboardingBrief) => {
  const section = (title: string, bullets: string[]) =>
    `${title}\n${bullets.map((bullet) => `- ${bullet}`).join("\n")}`;

  return [
    "ONBOARDING BRIEF",
    `Role: ${brief.role_focus}`,
    "",
    "WELCOME SUMMARY",
    brief.welcome_summary,
    "",
    section(brief.key_systems.title, brief.key_systems.bullets),
    "",
    section(brief.common_issues.title, brief.common_issues.bullets),
    "",
    section(brief.tools_and_access.title, brief.tools_and_access.bullets),
    "",
    section(brief.who_to_ask.title, brief.who_to_ask.bullets),
    "",
    section(brief.first_week_checklist.title, brief.first_week_checklist.bullets),
    "",
    "ADDITIONAL RESOURCES",
    brief.additional_resources,
  ].join("\n");
};

const BriefSection = ({
  title,
  bullets,
  ordered,
}: {
  title: string;
  bullets: string[];
  ordered?: boolean;
}) => {
  const ListTag = ordered ? "ol" : "ul";
  return (
    <section className="rounded-lg border border-slate-100 bg-slate-50/80 p-4">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-700">{title}</h3>
      <ListTag
        className={`mt-3 space-y-2 pl-5 text-sm leading-6 text-slate-700 ${ordered ? "list-decimal" : "list-disc"}`}
      >
        {bullets.map((bullet) => (
          <li key={`${title}-${bullet}`}>{bullet}</li>
        ))}
      </ListTag>
    </section>
  );
};

export const OnboardingBriefPanel = ({ brief }: OnboardingBriefPanelProps) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    const text = formatBriefForCopy(brief);
    await navigator.clipboard.writeText(text);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="rounded-xl border border-emerald-100 bg-gradient-to-br from-white to-emerald-50/40 p-6 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Onboarding Brief</h2>
          <p className="mt-1 text-sm text-slate-600">
            Ramp-up plan generated from the knowledge base
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold uppercase text-emerald-800 ring-1 ring-emerald-200">
            {brief.role_focus}
          </span>
          <button
            type="button"
            className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            aria-label="Copy onboarding brief to clipboard"
            onClick={handleCopy}
          >
            {copied ? "Copied" : "Copy plan"}
          </button>
        </div>
      </div>

      <p className="mt-4 rounded-lg border border-slate-100 bg-white p-4 text-sm leading-7 text-slate-800">
        {brief.welcome_summary}
      </p>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <BriefSection title={brief.key_systems.title} bullets={brief.key_systems.bullets} />
        <BriefSection title={brief.common_issues.title} bullets={brief.common_issues.bullets} />
        <BriefSection title={brief.tools_and_access.title} bullets={brief.tools_and_access.bullets} />
        <BriefSection title={brief.who_to_ask.title} bullets={brief.who_to_ask.bullets} />
      </div>

      <div className="mt-4 grid gap-4">
        <BriefSection
          title={brief.first_week_checklist.title}
          bullets={brief.first_week_checklist.bullets}
          ordered
        />
        <section className="rounded-lg border border-emerald-100 bg-emerald-50/70 p-4">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-emerald-900">
            Additional Resources
          </h3>
          <p className="mt-2 text-sm leading-6 text-emerald-950">{brief.additional_resources}</p>
        </section>
      </div>
    </section>
  );
};
