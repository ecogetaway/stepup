interface EscalationBannerProps {
  isEscalated: boolean;
}

export const EscalationBanner = ({ isEscalated }: EscalationBannerProps) => {
  if (!isEscalated) return null;

  return (
    <div
      className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm font-medium text-amber-800 shadow-sm"
      role="status"
      aria-live="polite"
    >
      This answer was escalated because confidence is below the configured threshold.
      A human support agent should review the response.
    </div>
  );
};
