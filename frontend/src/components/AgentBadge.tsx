interface AgentBadgeProps {
  agent: string;
}

const formatAgentLabel = (agent: string) => {
  if (!agent) return "Unknown";
  return agent
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
};

export const AgentBadge = ({ agent }: AgentBadgeProps) => (
  <span className="inline-flex rounded-full bg-indigo-50 px-3 py-1 text-sm font-semibold text-indigo-700">
    {formatAgentLabel(agent)}
  </span>
);
