import type { SlaStatus } from "../types/api";

interface SlaBadgeProps {
  sla: SlaStatus;
}

const getSlaStyles = (state: string) => {
  if (state === "ok") {
    return {
      label: "On track",
      className: "bg-emerald-100 text-emerald-800 ring-emerald-200",
    };
  }
  if (state === "at_risk") {
    return {
      label: "At risk",
      className: "bg-amber-100 text-amber-800 ring-amber-200",
    };
  }
  if (state === "critical") {
    return {
      label: "Critical",
      className: "bg-orange-100 text-orange-800 ring-orange-200",
    };
  }
  if (state === "breached") {
    return {
      label: "Breached",
      className: "bg-red-100 text-red-800 ring-red-200",
    };
  }
  return {
    label: "Resolved",
    className: "bg-slate-100 text-slate-700 ring-slate-200",
  };
};

const getSlaDetail = (sla: SlaStatus) => {
  if (sla.state === "resolved") {
    return "SLA closed";
  }
  if (sla.state === "breached") {
    return `${sla.elapsed_pct}% elapsed`;
  }
  if (sla.remaining_minutes <= 60) {
    return `${sla.remaining_minutes}m left`;
  }
  return `${sla.elapsed_pct}% elapsed`;
};

export const SlaBadge = ({ sla }: SlaBadgeProps) => {
  const styles = getSlaStyles(sla.state);
  const detail = getSlaDetail(sla);

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ${styles.className}`}
      aria-label={`SLA status ${styles.label}, ${detail}`}
      title={`Due ${sla.due_at}`}
    >
      <span>{styles.label}</span>
      <span className="font-medium opacity-80">· {detail}</span>
    </span>
  );
};
