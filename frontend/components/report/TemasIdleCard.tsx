"use client";

interface TemasIdleCardProps {
  onGenerate: () => void;
  errorMsg: string | null;
}

export function TemasIdleCard({ onGenerate, errorMsg }: TemasIdleCardProps) {
  return (
    <div className="bg-surface border border-border rounded-2xl p-12 flex flex-col items-center text-center gap-4 max-w-[640px] mx-auto">
      <div className="text-lg font-semibold text-ink">Análisis de temas</div>
      <div className="text-sm text-ink-soft leading-relaxed">
        Agrupa automáticamente las preguntas del período por similitud de significado, les da nombre y
        muestra su evolución semana a semana. Puede tardar de 1 a 3 minutos.
      </div>
      {errorMsg && <div className="text-sm text-danger">{errorMsg}</div>}
      <button
        onClick={onGenerate}
        className="mt-2 px-7 py-3 bg-navy text-surface border-none rounded-[9px] text-sm font-semibold cursor-pointer"
      >
        Generar análisis
      </button>
    </div>
  );
}
