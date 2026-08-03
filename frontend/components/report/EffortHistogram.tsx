import type { Histograma } from "@/lib/report-types";

const BINS: { key: keyof Histograma; label: string; color: string }[] = [
  { key: "0", label: "0 preguntas", color: "oklch(52% 0.14 25)" },
  { key: "1-5", label: "1–5", color: "oklch(62% 0.13 70)" },
  { key: "6-20", label: "6–20", color: "oklch(52% 0.09 170)" },
  { key: "20+", label: "> 20", color: "var(--color-navy)" },
];

export function EffortHistogram({ histograma }: { histograma: Histograma }) {
  const max = Math.max(...BINS.map((b) => histograma[b.key]), 1);

  return (
    <div className="bg-surface border border-border rounded-2xl px-[26px] py-6">
      <div className="text-base font-semibold text-ink mb-1">Histograma de esfuerzo</div>
      <div className="text-xs text-ink-muted mb-[18px]">
        Estudiantes por rango de preguntas hechas en el período — la señal de equidad más importante
      </div>
      <div className="flex items-end gap-6 h-[140px]">
        {BINS.map((b) => (
          <div key={b.key} className="flex-1 flex flex-col items-center gap-2 h-full justify-end">
            <div className="text-sm font-semibold text-ink">{histograma[b.key]}</div>
            <div
              className="w-full max-w-20 rounded-t-md"
              style={{ height: `${Math.round((histograma[b.key] / max) * 100)}%`, background: b.color }}
            />
            <div className="text-xs text-ink-muted">{b.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
