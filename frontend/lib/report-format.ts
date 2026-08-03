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

// El backend manda fechas como "YYYY-MM-DD HH:MM:SS" (formato SQLite, sin
// zona horaria) o "YYYY-MM-DD"; se parsea como texto para no arrastrar
// desfaces de timezone al convertir a Date.
export function formatFechaLarga(valor: string | null): string {
  if (!valor) return "—";
  const [fecha] = valor.split(" ");
  const [anio, mes, dia] = fecha.split("-");
  return `${dia}/${mes}/${anio}`;
}

export function formatFechaCorta(valor: string): string {
  const [fecha] = valor.split(" ");
  const [, mes, dia] = fecha.split("-");
  return `${dia}/${mes}`;
}
