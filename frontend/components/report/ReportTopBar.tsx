"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

const TABS = [
  { id: "pulso", label: "Pulso" },
  { id: "temas", label: "Temas" },
  { id: "estudiantes", label: "Estudiantes" },
];

const TITLES: Record<string, string> = {
  pulso: "Pulso del curso",
  temas: "Temas",
  estudiantes: "Estudiantes",
};

export function ReportTopBar() {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const segmentos = pathname.split("/").filter(Boolean); // ["reporte", "estudiantes", "usuario"?]
  const tab = segmentos[1] ?? "pulso";
  const esDetalleEstudiante = segmentos.length > 2;

  if (esDetalleEstudiante) return null;

  const qs = searchParams.toString();

  return (
    <div className="flex flex-col gap-[18px]">
      <div>
        <div className="text-[13px] font-semibold text-ink-soft uppercase tracking-wide">Reporte de uso</div>
        <div className="text-2xl font-semibold text-ink mt-1">{TITLES[tab] ?? ""}</div>
      </div>
      <div className="flex gap-1 border-b border-border">
        {TABS.map((t) => {
          const active = tab === t.id;
          return (
            <Link
              key={t.id}
              href={`/reporte/${t.id}${qs ? `?${qs}` : ""}`}
              className={`px-4 py-2.5 -mb-px text-sm font-semibold border-b-2 ${
                active ? "border-navy text-navy" : "border-transparent text-ink-soft"
              }`}
            >
              {t.label}
            </Link>
          );
        })}
      </div>
    </div>
  );
}
