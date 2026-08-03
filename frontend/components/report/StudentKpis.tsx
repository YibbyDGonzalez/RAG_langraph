import { formatFechaLarga } from "@/lib/report-format";

interface StudentKpisProps {
  totalPreguntas: number;
  totalSesiones: number;
  ultimaActividad: string | null;
}

export function StudentKpis({ totalPreguntas, totalSesiones, ultimaActividad }: StudentKpisProps) {
  const cards = [
    { label: "Total de preguntas", note: "(histórico)", value: String(totalPreguntas) },
    { label: "Total de sesiones", note: "(histórico)", value: String(totalSesiones) },
    { label: "Última actividad", note: null, value: formatFechaLarga(ultimaActividad) },
  ];

  return (
    <div className="grid grid-cols-3 gap-[18px]">
      {cards.map((c) => (
        <div key={c.label} className="bg-surface border border-border rounded-2xl px-[22px] py-5">
          <div className="text-xs text-ink-muted">
            {c.label} {c.note && <span className="text-[10px]">{c.note}</span>}
          </div>
          <div className="text-[32px] font-semibold text-ink mt-1">{c.value}</div>
        </div>
      ))}
    </div>
  );
}
