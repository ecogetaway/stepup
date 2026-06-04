import { useState } from "react";

interface TraceViewerProps {
  trace: Record<string, any>;
}

export const TraceViewer = ({ trace }: TraceViewerProps) => {
  const [isOpen, setIsOpen] = useState(false);

  const handleToggle = () => {
    setIsOpen((currentValue) => !currentValue);
  };

  return (
    <section className="rounded-xl bg-white p-5 shadow-sm">
      <button
        type="button"
        className="flex w-full items-center justify-between gap-3 text-left text-lg font-semibold text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        aria-expanded={isOpen}
        aria-controls="agent-trace"
        onClick={handleToggle}
      >
        <span>Agent Trace</span>
        <span className="text-sm font-medium text-gray-500">
          {isOpen ? "Hide JSON" : "Show JSON"}
        </span>
      </button>

      {isOpen ? (
        <pre
          id="agent-trace"
          className="mt-4 max-h-96 rounded-lg bg-gray-900 p-4 font-mono text-xs leading-6 text-green-400 overflow-auto"
        >
          {JSON.stringify(trace, null, 2)}
        </pre>
      ) : null}
    </section>
  );
};
