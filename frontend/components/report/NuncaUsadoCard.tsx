import type { EstudianteRoster } from "@/lib/report-types";

export function NuncaUsadoCard({ nuncaUsado }: { nuncaUsado: EstudianteRoster[] }) {
  return (
    <div className="bg-surface border border-border rounded-2xl px-6 py-[22px]">
      <div className="text-[15px] font-semibold text-ink mb-3.5">Nunca han usado la herramienta</div>
      {nuncaUsado.length === 0 ? (
        <div className="text-[13px] text-teal">Todo el curso ha usado la herramienta al menos una vez.</div>
      ) : (
        <div className="flex flex-col gap-2.5">
          {nuncaUsado.map((n) => (
            <div key={n.usuario} className="text-[13px] text-ink">
              {n.nombre}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
