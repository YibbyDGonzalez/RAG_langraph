"use client";

import Image from "next/image";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
}

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
        <div className="whitespace-pre-wrap">{content}</div>
        {streaming && (
          <span className="inline-block w-[7px] h-[15px] bg-ink-soft ml-0.5 align-text-bottom cursor-blink" />
        )}
      </div>
    </div>
  );
}
