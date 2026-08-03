"use client";

import { useState } from "react";

import { formatDuracion } from "@/lib/report-format";
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

export function DayDistCard({ temporal }: { temporal: Temporal }) {
  const [showDetail, setShowDetail] = useState(false);
  const max = Math.max(...DIAS.map((d) => temporal.por_dia[d] ?? 0), 1);

  return (
    <div className="bg-surface border border-border rounded-2xl px-[26px] py-6">
      <div className="text-base font-semibold text-ink mb-[18px]">Preguntas por día de la semana</div>
      <div className="flex items-end gap-3 h-[130px]">
        {DIAS.map((dia) => (
          <div key={dia} className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end">
            <div
              className="w-full max-w-8 bg-surface-selected rounded-t-[5px]"
              style={{ height: `${Math.round(((temporal.por_dia[dia] ?? 0) / max) * 100)}%` }}
            />
            <div className="text-[11px] text-ink-muted">{DIAS_CORTO[dia]}</div>
          </div>
        ))}
      </div>
      <button
        onClick={() => setShowDetail((v) => !v)}
        className="mt-4 bg-transparent border-none p-0 text-[13px] font-semibold text-navy cursor-pointer"
      >
        {showDetail ? "Ocultar detalle de horario" : "Ver detalle de horario"}
      </button>
      {showDetail && (
        <div className="mt-3.5 pt-3.5 border-t border-border flex flex-col gap-2 text-[13px] text-ink-soft">
          <div>
            Duración promedio de sesión: <strong className="text-ink">{formatDuracion(temporal.duracion_promedio_min)}</strong>
          </div>
          <div>
            Concentración en los 2 días más activos ({temporal.top2_dias.join(", ")}):{" "}
            <strong className="text-ink">{temporal.top2_dias_pct}%</strong>
          </div>
          {temporal.top2_dias_pct >= 40 && (
            <div className="text-[oklch(62%_0.13_70)] font-medium">Uso muy concentrado en pocos días.</div>
          )}
        </div>
      )}
    </div>
  );
}
