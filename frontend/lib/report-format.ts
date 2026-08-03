export function formatDeltaPct(pct: number | null): { text: string; colorClass: string } {
  if (pct === null) return { text: "", colorClass: "text-ink-muted" };
  const sign = pct >= 0 ? "+" : "";
  const colorClass = pct >= 0 ? "text-teal" : "text-danger";
  return { text: `${sign}${Math.trunc(pct)}% vs período anterior`, colorClass };
}

export function formatDuracion(minutos: number): string {
  if (minutos < 1) return "< 1 minuto";
  if (minutos < 60) return `${Math.round(minutos)} min`;
  const horas = Math.floor(minutos / 60);
  const resto = Math.round(minutos % 60);
  return `${horas}h ${resto}min`;
}
