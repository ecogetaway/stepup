interface ConfidenceMeterProps {
  confidence: number;
}

export const ConfidenceMeter = ({ confidence }: ConfidenceMeterProps) => {
  const percentage = Math.round(confidence * 100);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs font-semibold uppercase tracking-wide text-gray-500">
          Confidence
        </span>
        <span className="text-sm font-bold text-gray-900">{percentage}%</span>
      </div>
      <div
        className="h-2 overflow-hidden rounded-full bg-gray-100"
        aria-label={`Confidence ${percentage}%`}
        role="meter"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percentage}
      >
        <div
          className="h-full rounded-full bg-indigo-600 transition-all"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};
