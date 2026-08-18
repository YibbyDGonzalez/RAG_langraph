"use client";

import Image from "next/image";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
}

const markdownComponents = {
  p: ({ children }: { children?: React.ReactNode }) => (
    <p className="mb-2.5 last:mb-0">{children}</p>
  ),
  ul: ({ children }: { children?: React.ReactNode }) => (
    <ul className="list-disc pl-5 mb-2.5 last:mb-0 space-y-1">{children}</ul>
  ),
  ol: ({ children }: { children?: React.ReactNode }) => (
    <ol className="list-decimal pl-5 mb-2.5 last:mb-0 space-y-1">{children}</ol>
  ),
  li: ({ children }: { children?: React.ReactNode }) => <li className="leading-[1.7]">{children}</li>,
  strong: ({ children }: { children?: React.ReactNode }) => (
    <strong className="font-semibold text-ink">{children}</strong>
  ),
  em: ({ children }: { children?: React.ReactNode }) => <em className="italic">{children}</em>,
  a: ({ href, children }: { href?: string; children?: React.ReactNode }) => (
    <a href={href} target="_blank" rel="noopener noreferrer" className="text-teal underline underline-offset-2">
      {children}
    </a>
  ),
  code: ({ children }: { children?: React.ReactNode }) => (
    <code className="bg-surface-selected rounded px-1 py-0.5 text-[0.9em]">{children}</code>
  ),
  blockquote: ({ children }: { children?: React.ReactNode }) => (
    <blockquote className="border-l-2 border-border pl-3 italic text-ink-soft mb-2.5 last:mb-0">
      {children}
    </blockquote>
  ),
  h1: ({ children }: { children?: React.ReactNode }) => (
    <h1 className="text-[1.05em] font-semibold mb-2 mt-1 first:mt-0">{children}</h1>
  ),
  h2: ({ children }: { children?: React.ReactNode }) => (
    <h2 className="text-[1.02em] font-semibold mb-2 mt-1 first:mt-0">{children}</h2>
  ),
  h3: ({ children }: { children?: React.ReactNode }) => (
    <h3 className="font-semibold mb-1.5 mt-1 first:mt-0">{children}</h3>
  ),
};

export function MessageBubble({ role, content, streaming }: MessageBubbleProps) {
  if (role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] bg-surface-selected text-ink px-4 py-3 rounded-tl-[14px] rounded-tr-[14px] rounded-bl-[14px] rounded-br-[4px] text-sm leading-relaxed">
          <div className="whitespace-pre-wrap">{content}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start items-start gap-2.5">
      <div
        className={`w-14 h-14 rounded-2xl overflow-hidden flex-shrink-0 border border-border ${
          streaming ? "doctor-thinking" : ""
        }`}
      >
        <Image src="/Doctor.png" alt="Asistente MBE" width={56} height={56} className="w-full h-full object-cover" />
      </div>
      <div className="max-w-[75%] bg-surface text-ink px-[18px] py-3.5 border border-border rounded-tl-[14px] rounded-tr-[14px] rounded-bl-[4px] rounded-br-[14px] text-[15px] leading-[1.7]">
        <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
          {content}
        </ReactMarkdown>
        {streaming && (
          <span className="inline-block w-[7px] h-[15px] bg-ink-soft ml-0.5 align-text-bottom cursor-blink" />
        )}
      </div>
    </div>
  );
}
