"use client";

import { EvolutionChart } from "@/components/report/EvolutionChart";
import type { EvolucionSemanalPunto, Tema } from "@/lib/report-types";

interface TemasResultadoProps {
  temas: Tema[];
  evolucion: EvolucionSemanalPunto[];
  expandido: Record<string, boolean>;
  onToggle: (nombre: string) => void;
}

export function TemasResultado({ temas, evolucion, expandido, onToggle }: TemasResultadoProps) {
  if (temas.length === 0) {
    return (
      <div className="text-sm text-ink-soft">
        No se encontraron grupos temáticos con los datos del período seleccionado.
      </div>
    );
  }

  const maxCount = Math.max(...temas.map((t) => t.n_preguntas), 1);

  return (
    <div className="flex flex-col gap-[22px]">
      <div className="text-sm text-ink-soft">
        {temas.length} grupos temáticos identificados en el período seleccionado.
      </div>

      <div className="bg-surface border border-border rounded-2xl px-[26px] py-6">
        <div className="text-base font-semibold text-ink mb-[18px]">Volumen por tema</div>
        <div className="flex flex-col gap-3">
          {temas.map((t) => (
            <div key={t.nombre} className="flex items-center gap-3">
              <div className="w-[220px] text-[13px] text-ink flex-shrink-0">{t.nombre}</div>
              <div className="flex-1 bg-surface-selected rounded-md h-[22px] relative">
                <div
                  className="h-full rounded-md bg-navy"
                  style={{ width: `${Math.round((t.n_preguntas / maxCount) * 100)}%` }}
                />
              </div>
              <div className="w-20 text-right text-xs text-ink-soft flex-shrink-0">
                {t.n_preguntas} ({t.pct}%)
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-2.5">
        {temas.map((t) => {
          const abierto = !!expandido[t.nombre];
          return (
            <div key={t.nombre} className="bg-surface border border-border rounded-xl overflow-hidden">
              <button
                onClick={() => onToggle(t.nombre)}
                className="w-full flex items-center justify-between px-[18px] py-4 bg-transparent border-none cursor-pointer text-left"
              >
                <div className="flex items-center gap-2.5">
                  <span className="text-sm font-semibold text-ink">{t.nombre}</span>
                  <span className="text-xs text-ink-muted">
                    {t.n_preguntas} preguntas · {t.pct}%
                  </span>
                </div>
                <span className="text-[13px] text-ink-soft">{abierto ? "Ocultar ejemplos ▲" : "Ver ejemplos ▼"}</span>
              </button>
              {abierto && (
                <div className="px-[18px] pb-4 pt-3 border-t border-border flex flex-col gap-2">
                  {t.ejemplos.map((ej, i) => (
                    <div key={i} className="text-[13px] text-ink-soft px-3 py-2 bg-surface-alt rounded-lg">
                      &quot;{ej}&quot;
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="bg-surface border border-border rounded-2xl px-[26px] py-6">
        <div className="text-base font-semibold text-ink mb-1.5">Evolución semanal — top 3 temas</div>
        <div className="text-xs text-ink-muted mb-4">Solo se muestran los temas de mayor volumen para no saturar</div>
        <EvolutionChart evolucion={evolucion} temas={temas} />
      </div>
    </div>
  );
}
