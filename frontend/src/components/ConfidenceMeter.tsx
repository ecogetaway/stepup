interface ConfidenceMeterProps {
  confidence: number;
}

const getConfidenceStyles = (percentage: number) => {
  if (percentage >= 85) {
    return { bar: "bg-emerald-500", text: "text-emerald-700", label: "High" };
  }
  if (percentage >= 65) {
    return { bar: "bg-amber-500", text: "text-amber-700", label: "Moderate" };
  }
  return { bar: "bg-red-500", text: "text-red-700", label: "Low" };
};

export const ConfidenceMeter = ({ confidence }: ConfidenceMeterProps) => {
  const percentage = Math.round(confidence * 100);
  const styles = getConfidenceStyles(percentage);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Confidence
        </span>
        <span className={`text-sm font-bold ${styles.text}`}>
          {percentage}% · {styles.label}
        </span>
      </div>
      <div
        className="h-2.5 overflow-hidden rounded-full bg-slate-100"
        aria-label={`Confidence ${percentage}%`}
        role="meter"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percentage}
      >
        <div
          className={`h-full rounded-full transition-all duration-500 ${styles.bar}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};
