interface DuplicateIncidentBannerProps {
  groups: string[][];
}

export const DuplicateIncidentBanner = ({ groups }: DuplicateIncidentBannerProps) => {
  if (!groups || groups.length === 0) return null;

  return (
    <div
      className="rounded-xl border border-sky-200 bg-gradient-to-r from-sky-50 to-cyan-50 p-4 text-sm font-medium text-sky-900 shadow-sm"
      role="status"
      aria-live="polite"
    >
      <span className="font-semibold">🔁 Possible duplicate incident{groups.length > 1 ? "s" : ""} detected</span>
      <ul className="mt-2 space-y-1 text-sky-800">
        {groups.map((group) => (
          <li key={group.join("-")}>
            {group.join(" and ")} appear to describe the same underlying issue — computed
            from source-text similarity, not by the model.
          </li>
        ))}
      </ul>
    </div>
  );
};
