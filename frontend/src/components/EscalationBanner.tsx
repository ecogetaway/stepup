interface EscalationBannerProps {
  isEscalated: boolean;
}

export const EscalationBanner = ({ isEscalated }: EscalationBannerProps) => {
  if (!isEscalated) return null;

  return (
    <div
      className="rounded-xl border border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50 p-4 text-sm font-medium text-amber-900 shadow-sm"
      role="status"
      aria-live="polite"
    >
      <span className="font-semibold">Escalated to human support</span>
      <p className="mt-1 leading-6 text-amber-800">
        Confidence is below the configured threshold. A support agent should review this
        response.
      </p>
    </div>
  );
};
