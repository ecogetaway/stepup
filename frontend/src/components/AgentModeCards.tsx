import type { KeyboardEvent } from "react";
import type { AgentMode } from "../types/api";

interface AgentOption {
  value: AgentMode;
  label: string;
  description: string;
}

const agentOptions: AgentOption[] = [
  {
    value: "auto",
    label: "Auto",
    description: "Routes factual and analytical questions automatically.",
  },
  {
    value: "react",
    label: "ReAct",
    description: "Direct answers from SOPs and runbooks.",
  },
  {
    value: "plan_execute",
    label: "Plan Execute",
    description: "Multi-step ticket and incident analysis.",
  },
];

interface AgentModeCardsProps {
  value: AgentMode;
  onChange: (mode: AgentMode) => void;
}

export const AgentModeCards = ({ value, onChange }: AgentModeCardsProps) => {
  const handleSelect = (mode: AgentMode) => {
    onChange(mode);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLButtonElement>, mode: AgentMode) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onChange(mode);
    }
  };

  return (
    <div className="space-y-3">
      <span className="text-sm font-semibold text-slate-700">Agent mode</span>
      <div className="grid gap-2">
        {agentOptions.map((option) => {
          const isSelected = value === option.value;
          return (
            <button
              key={option.value}
              type="button"
              aria-pressed={isSelected}
              aria-label={`${option.label} agent mode`}
              className={`rounded-xl border p-3 text-left transition focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 ${
                isSelected
                  ? "border-indigo-500 bg-indigo-50 shadow-sm ring-2 ring-indigo-200"
                  : "border-slate-200 bg-white hover:border-indigo-200 hover:bg-slate-50"
              }`}
              onClick={() => handleSelect(option.value)}
              onKeyDown={(event) => handleKeyDown(event, option.value)}
            >
              <span
                className={`text-sm font-semibold ${isSelected ? "text-indigo-800" : "text-slate-900"}`}
              >
                {option.label}
              </span>
              <p className="mt-1 text-xs leading-5 text-slate-500">{option.description}</p>
            </button>
          );
        })}
      </div>
    </div>
  );
};
