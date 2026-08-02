"use client";

interface ChatInputProps {
  draft: string;
  onDraftChange: (value: string) => void;
  onSend: () => void;
  onStop: () => void;
  isGenerating: boolean;
}

export function ChatInput({ draft, onDraftChange, onSend, onStop, isGenerating }: ChatInputProps) {
  const sendDisabled = !draft.trim() || isGenerating;

  return (
    <div className="px-10 pt-[18px] pb-[26px] border-t border-border">
      <div className="max-w-[720px] mx-auto flex items-end gap-2.5 bg-surface border border-border rounded-2xl py-2.5 pr-2.5 pl-[18px]">
        <textarea
          rows={1}
          value={draft}
          onChange={(e) => onDraftChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSend();
            }
          }}
          disabled={isGenerating}
          placeholder="Escribe tu pregunta sobre Medicina Basada en Evidencia..."
          className="flex-1 border-none outline-none resize-none font-sans text-sm text-ink bg-transparent py-1.5 max-h-[120px]"
        />
        {isGenerating && (
          <button
            onClick={onStop}
            className="px-4 py-2.5 border border-border rounded-[9px] text-[13px] font-semibold cursor-pointer bg-surface text-ink-soft"
          >
            Detener
          </button>
        )}
        <button
          onClick={onSend}
          disabled={sendDisabled}
          className={`px-[18px] py-2.5 border-none rounded-[9px] text-sm font-semibold ${
            sendDisabled
              ? "cursor-not-allowed bg-border text-ink-muted"
              : "cursor-pointer bg-navy text-surface"
          }`}
        >
          Enviar
        </button>
      </div>
    </div>
  );
}
