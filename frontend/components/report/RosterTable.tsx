import Link from "next/link";

import type { EstudianteFila } from "@/lib/report-types";

export function RosterTable({ tabla, queryString }: { tabla: EstudianteFila[]; queryString: string }) {
  return (
    <div className="bg-surface border border-border rounded-2xl overflow-hidden">
      <div className="px-6 py-5 border-b border-border flex items-baseline justify-between">
        <div className="text-base font-semibold text-ink">Roster del curso</div>
        <div className="text-xs text-ink-muted">Ordenado de menor a mayor uso</div>
      </div>
      <div className="grid grid-cols-[2fr_1fr_1fr_2.2fr_0.8fr] px-6 py-3 text-[11px] font-semibold uppercase tracking-wide text-ink-muted">
        <div>Nombre</div>
        <div>Preguntas</div>
        <div>Sesiones</div>
        <div>Últimos temas</div>
        <div />
      </div>
      {tabla.map((fila, i) => (
        <div
          key={fila.usuario}
          className={`grid grid-cols-[2fr_1fr_1fr_2.2fr_0.8fr] items-center px-6 py-3.5 border-b border-border last:border-b-0 ${
            i % 2 === 1 ? "bg-surface-alt" : ""
          }`}
        >
          <div className="text-sm font-medium text-ink">{fila.nombre}</div>
          <div className="text-sm text-ink">{fila.n_preguntas}</div>
          <div className="text-sm text-ink">{fila.n_sesiones}</div>
          <div className="flex gap-1.5 flex-wrap">
            {fila.ultimos_temas.length === 0 ? (
              <span className="text-ink-muted text-sm">—</span>
            ) : (
              fila.ultimos_temas.map((t) => (
                <span key={t} className="text-[11px] bg-surface-selected text-navy px-2 py-0.5 rounded-full">
                  {t}
                </span>
              ))
            )}
          </div>
          <Link
            href={`/reporte/estudiantes/${fila.usuario}?${queryString}`}
            className="justify-self-end text-[13px] font-semibold text-navy border border-border rounded-md px-3.5 py-1.5"
          >
            Ver
          </Link>
        </div>
      ))}
    </div>
  );
}
