"use client";

import { formatDeltaPct, formatDuracion } from "@/lib/report-format";
import type { PulsoData } from "@/lib/report-types";

interface CardDef {
  label: string;
  value: string;
  deltaPct: number | null;
  note?: string;
}

export function KpiGrid({ data }: { data: PulsoData }) {
  const cards: CardDef[] = [
    { label: "Total de estudiantes", value: String(data.total_estudiantes), deltaPct: null, note: "roster completo" },
    { label: "Estudiantes activos", value: String(data.kpis.estudiantes.valor), deltaPct: data.kpis.estudiantes.delta_pct },
    { label: "Total de chats", value: String(data.kpis.sesiones.valor), deltaPct: data.kpis.sesiones.delta_pct },
    { label: "Total de preguntas", value: String(data.kpis.preguntas.valor), deltaPct: data.kpis.preguntas.delta_pct },
    {
      label: "Preguntas por estudiante",
      value: String(data.kpis.preguntas_por_estudiante.valor),
      deltaPct: data.kpis.preguntas_por_estudiante.delta_pct,
    },
    {
      label: "Tiempo prom. por sesión",
      value: data.kpis.tiempo_promedio_sesion.valor_fmt ?? formatDuracion(data.kpis.tiempo_promedio_sesion.valor),
      deltaPct: data.kpis.tiempo_promedio_sesion.delta_pct,
    },
  ];

  return (
    <div className="grid grid-cols-3 gap-[18px]">
      {cards.map((c) => {
        const { text, colorClass } = formatDeltaPct(c.deltaPct);
        return (
          <div key={c.label} className="bg-surface border border-border rounded-2xl px-6 py-[22px] flex flex-col gap-1.5">
            <div className="text-[13px] font-medium text-ink-soft">{c.label}</div>
            <div className="text-[40px] font-semibold text-ink tracking-tight leading-tight">{c.value}</div>
            <div className={`text-[13px] font-semibold ${colorClass}`}>{c.deltaPct === null ? c.note : text}</div>
          </div>
        );
      })}
    </div>
  );
}
