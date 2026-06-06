import ReactMarkdown from "react-markdown";

interface AnswerMarkdownProps {
  content: string;
}

export const AnswerMarkdown = ({ content }: AnswerMarkdownProps) => {
  const normalised = content.replace(/^⚠️ I'm not fully confident[\s\S]*?Here's what I found:\s*/i, "");

  return (
    <div className="prose-answer text-[15px] leading-8 text-slate-700">
      <ReactMarkdown
        components={{
          p: ({ children }) => <p className="mb-4 last:mb-0">{children}</p>,
          strong: ({ children }) => (
            <strong className="font-semibold text-slate-900">{children}</strong>
          ),
          ol: ({ children }) => (
            <ol className="mb-4 list-decimal space-y-2 pl-5 last:mb-0">{children}</ol>
          ),
          ul: ({ children }) => (
            <ul className="mb-4 list-disc space-y-2 pl-5 last:mb-0">{children}</ul>
          ),
          li: ({ children }) => <li className="leading-7">{children}</li>,
          a: ({ children, href }) => (
            <a
              className="font-medium text-indigo-600 underline decoration-indigo-200 underline-offset-2"
              href={href}
              rel="noreferrer"
              target="_blank"
            >
              {children}
            </a>
          ),
        }}
      >
        {normalised}
      </ReactMarkdown>
    </div>
  );
};
