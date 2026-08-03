"use client";

import { useState } from "react";

import type { Temporal } from "@/lib/report-types";

const DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];
const DIAS_CORTO: Record<string, string> = {
  Lunes: "Lun",
  Martes: "Mar",
  Miércoles: "Mié",
  Jueves: "Jue",
  Viernes: "Vie",
  Sábado: "Sáb",
  Domingo: "Dom",
};

// Franjas horarias agregadas para no saturar el mapa (madrugada/mañana/tarde/noche).
const FRANJAS: { label: string; horas: number[] }[] = [
  { label: "Madrugada", horas: [0, 1, 2, 3, 4, 5] },
  { label: "Mañana", horas: [6, 7, 8, 9, 10, 11] },
  { label: "Tarde", horas: [12, 13, 14, 15, 16, 17] },
  { label: "Noche", horas: [18, 19, 20, 21, 22, 23] },
];

export function HeatmapCard({ temporal }: { temporal: Temporal }) {
  const [show, setShow] = useState(true);

  const rows = DIAS.map((dia) => {
    const porHora = temporal.heatmap[dia] ?? {};
    return FRANJAS.map((f) => f.horas.reduce((sum, h) => sum + (porHora[String(h)] ?? 0), 0));
  });
  const max = Math.max(...rows.flat(), 1);

  return (
    <div className="bg-surface border border-border rounded-2xl px-[26px] py-6">
      <div className="flex items-center justify-between mb-3.5">
        <div className="text-base font-semibold text-ink">Mapa de calor — día × franja</div>
        <button
          onClick={() => setShow((v) => !v)}
          className="bg-transparent border-none text-xs font-semibold text-ink-soft cursor-pointer"
        >
          {show ? "Colapsar" : "Expandir"}
        </button>
      </div>
      {show && (
        <div className="flex flex-col gap-1">
          {DIAS.map((dia, i) => (
            <div key={dia} className="flex items-center gap-1.5">
              <div className="w-[26px] text-[10px] text-ink-muted">{DIAS_CORTO[dia]}</div>
              <div className="flex gap-1 flex-1">
                {rows[i].map((v, j) => (
                  <div
                    key={j}
                    className="flex-1 h-4 rounded-[3px]"
                    style={{ background: `oklch(32% 0.09 250 / ${Math.min(1, v / max)})` }}
                  />
                ))}
              </div>
            </div>
          ))}
          <div className="flex gap-1.5 mt-1.5 pl-[32px]">
            {FRANJAS.map((f) => (
              <div key={f.label} className="flex-1 text-[9px] text-ink-muted text-center">
                {f.label}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
