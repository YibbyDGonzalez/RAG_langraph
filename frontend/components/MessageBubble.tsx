"use client";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
}

export function MessageBubble({ role, content, streaming }: MessageBubbleProps) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={
          isUser
            ? "max-w-[75%] bg-surface-selected text-ink px-4 py-3 rounded-tl-[14px] rounded-tr-[14px] rounded-bl-[14px] rounded-br-[4px] text-sm leading-relaxed"
            : "max-w-[75%] bg-surface text-ink px-[18px] py-3.5 border border-border rounded-tl-[14px] rounded-tr-[14px] rounded-bl-[4px] rounded-br-[14px] text-[15px] leading-[1.7]"
        }
      >
        <div className="whitespace-pre-wrap">{content}</div>
        {streaming && (
          <span className="inline-block w-[7px] h-[15px] bg-ink-soft ml-0.5 align-text-bottom cursor-blink" />
        )}
      </div>
    </div>
  );
}
