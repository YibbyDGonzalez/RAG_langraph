import { formatFechaCorta } from "@/lib/report-format";
import type { UltimaPregunta } from "@/lib/report-types";

export function StudentQuestions({ preguntas }: { preguntas: UltimaPregunta[] }) {
  return (
    <div>
      <div className="text-base font-semibold text-ink mb-3.5">Últimas preguntas</div>
      {preguntas.length === 0 ? (
        <div className="text-sm text-ink-muted">Sin preguntas registradas.</div>
      ) : (
        <div className="flex flex-col gap-2.5">
          {preguntas.map((p, i) => (
            <div
              key={i}
              className="bg-surface-alt rounded-[10px] px-4 py-3 flex justify-between gap-4"
            >
              <span className="text-[13px] text-ink">&quot;{p.pregunta}&quot;</span>
              <span className="text-xs text-ink-muted whitespace-nowrap">{formatFechaCorta(p.timestamp)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
