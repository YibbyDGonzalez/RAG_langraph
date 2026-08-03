"use client";

import { useRouter, useSearchParams } from "next/navigation";

import type { Alerta } from "@/lib/report-types";

// El backend no manda severidad explícita; la inferimos del ícono para el
// acento de color, igual de intención que el mockup (info=navy, atención=ámbar).
function accentColor(icono: string): string {
  return icono === "📈" ? "border-l-navy" : "border-l-[oklch(62%_0.13_70)]";
}

export function AlertsSection({ alertas, temasGenerados }: { alertas: Alerta[]; temasGenerados: boolean }) {
  const router = useRouter();
  const searchParams = useSearchParams();

  function verMas(a: Alerta) {
    const params = new URLSearchParams(searchParams.toString());
    params.delete("tema");
    if (a.filtro?.tema) params.set("tema", a.filtro.tema);
    router.push(`/reporte/${a.nivel_destino}?${params.toString()}`);
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="text-base font-semibold text-ink">Qué necesita tu atención</div>
      {alertas.length === 0 ? (
        <div className="bg-[oklch(94%_0.03_170)] rounded-[10px] px-5 py-[18px] text-sm text-navy">
          Todo en orden esta semana.
        </div>
      ) : (
        <div className="flex flex-col gap-2.5">
          {alertas.map((a, i) => (
            <div
              key={i}
              className={`flex items-start gap-3.5 bg-surface border border-border border-l-[3px] ${accentColor(a.icono)} rounded-[10px] px-[18px] py-4`}
            >
              <div className="w-7 h-7 rounded-lg flex items-center justify-center text-base flex-shrink-0">{a.icono}</div>
              <div className="flex-1 text-sm text-ink-soft leading-relaxed">{a.texto}</div>
              <button
                onClick={() => verMas(a)}
                className="whitespace-nowrap text-[13px] font-semibold text-navy bg-transparent border-none cursor-pointer px-1 py-1.5"
              >
                Ver más →
              </button>
            </div>
          ))}
        </div>
      )}
      {!temasGenerados && (
        <div className="text-xs text-ink-muted">
          Análisis de temas no generado para este período — algunas alertas de contenido pueden no estar disponibles todavía.
        </div>
      )}
    </div>
  );
}
