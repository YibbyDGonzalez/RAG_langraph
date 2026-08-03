"use client";

import type { SparklinePoint } from "@/lib/report-types";

export function WeeklyChart({ data }: { data: SparklinePoint[] }) {
  const values = data.map((d) => d.n_preguntas);
  const max = Math.max(...values, 1);
  const avg = values.length ? values.reduce((a, b) => a + b, 0) / values.length : 0;
  const avgLineTopPct = 100 - Math.round((avg / max) * 100);

  const last = values[values.length - 1] ?? 0;
  const prev = values[values.length - 2] ?? 0;
  const deltaPct = prev === 0 ? null : Math.round(((last - prev) / prev) * 100);

  return (
    <div className="bg-surface border border-border rounded-2xl px-[26px] py-6">
      <div className="flex items-baseline justify-between mb-5">
        <div>
          <div className="text-base font-semibold text-ink">Actividad — últimas 4 semanas</div>
          <div className="text-xs text-ink-muted mt-0.5">Preguntas por semana, independiente del período elegido</div>
        </div>
        {deltaPct !== null && (
          <div className="text-[13px] font-semibold text-teal">
            {deltaPct >= 0 ? "+" : ""}
            {deltaPct}% vs semana anterior
          </div>
        )}
      </div>
      <div className="relative h-[180px] flex items-end gap-5 pr-[56px]">
        <div
          className="absolute left-0 right-[56px] border-t border-dashed border-[oklch(70%_0.01_250)]"
          style={{ top: `${avgLineTopPct}%` }}
        />
        <div
          className="absolute right-0 text-[11px] text-ink-muted -translate-y-1/2"
          style={{ top: `${avgLineTopPct}%` }}
        >
          prom. {avg.toFixed(1)}
        </div>
        {data.map((d, i) => (
          <div key={d.semana} className="flex-1 flex flex-col items-center gap-2 h-full justify-end">
            <div className="text-xs font-semibold text-ink">{d.n_preguntas}</div>
            <div
              className="w-full max-w-[48px] bg-navy rounded-t-md"
              style={{ height: `${Math.round((d.n_preguntas / max) * 100)}%` }}
            />
            <div className="text-[11px] text-ink-muted">Sem {i + 1}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
