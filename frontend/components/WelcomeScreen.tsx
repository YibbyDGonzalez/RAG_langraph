"use client";

interface Suggestion {
  glyph: string;
  text: string;
}

const SUGGESTIONS: Suggestion[] = [
  { glyph: "P", text: "¿Qué es la medicina basada en la evidencia y cuáles son sus pasos principales?" },
  { glyph: "G", text: "¿Cuál es la diferencia entre un estudio observacional y un ensayo clínico aleatorizado?" },
  { glyph: "R", text: "¿Qué significa el nivel de evidencia de un estudio y cómo se clasifica?" },
];

interface WelcomeScreenProps {
  userName: string;
  onSelectSuggestion: (text: string) => void;
}

export function WelcomeScreen({ userName, onSelectSuggestion }: WelcomeScreenProps) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-10 gap-7 overflow-y-auto">
      <div className="text-center max-w-[560px]">
        <div className="text-[28px] font-semibold text-ink leading-tight">
          Hola, {userName}. ¿Sobre qué quieres estudiar hoy?
        </div>
      </div>
      <div className="flex flex-col gap-2.5 w-full max-w-[560px]">
        {SUGGESTIONS.map((sug) => (
          <button
            key={sug.text}
            onClick={() => onSelectSuggestion(sug.text)}
            className="flex items-center gap-3.5 text-left px-[18px] py-4 bg-surface border border-border rounded-xl cursor-pointer"
          >
            <div className="w-8 h-8 rounded-lg bg-surface-selected text-navy flex items-center justify-center text-[13px] font-bold shrink-0 font-mono">
              {sug.glyph}
            </div>
            <span className="text-sm text-ink">{sug.text}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
