"use client";

import type { EvolucionSemanalPunto, Tema } from "@/lib/report-types";

const COLORES = ["var(--color-navy)", "var(--color-teal)", "oklch(62% 0.13 70)"];
const W = 560;
const H = 150;

export function EvolutionChart({ evolucion, temas }: { evolucion: EvolucionSemanalPunto[]; temas: Tema[] }) {
  if (evolucion.length < 2) {
    return (
      <div className="text-xs text-ink-muted">
        No hay suficientes semanas en el rango seleccionado para mostrar una tendencia.
      </div>
    );
  }

  const topNombres = temas.slice(0, 3).map((t) => t.nombre);
  const max = Math.max(...evolucion.flatMap((p) => topNombres.map((n) => Number(p[n] ?? 0))), 1);

  function toPoints(nombre: string): string {
    return evolucion
      .map((p, i) => {
        const x = (i / (evolucion.length - 1)) * (W - 20) + 10;
        const y = H - (Number(p[nombre] ?? 0) / max) * (H - 10);
        return `${x},${y}`;
      })
      .join(" ");
  }

  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-[160px]">
        {topNombres.map((nombre, i) => (
          <polyline key={nombre} points={toPoints(nombre)} fill="none" stroke={COLORES[i]} strokeWidth={2.5} />
        ))}
      </svg>
      <div className="flex gap-[18px] mt-2.5 flex-wrap">
        {topNombres.map((nombre, i) => (
          <div key={nombre} className="flex items-center gap-1.5 text-xs text-ink-soft">
            <div className="w-2.5 h-2.5 rounded-full" style={{ background: COLORES[i] }} />
            {nombre}
          </div>
        ))}
      </div>
    </div>
  );
}
