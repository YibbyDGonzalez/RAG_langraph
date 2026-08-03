import type { EstudianteInactivo } from "@/lib/report-types";

export function SilenciososCard({ silenciosos }: { silenciosos: EstudianteInactivo[] }) {
  return (
    <div className="bg-surface border border-border rounded-2xl px-6 py-[22px]">
      <div className="text-[15px] font-semibold text-ink mb-3.5">
        Silenciosos <span className="font-normal text-ink-muted text-xs">— histórico completo</span>
      </div>
      {silenciosos.length === 0 ? (
        <div className="text-[13px] text-teal">Todos los estudiantes han tenido actividad reciente.</div>
      ) : (
        <div className="flex flex-col gap-2.5">
          {silenciosos.map((s) => (
            <div key={s.usuario} className="flex justify-between text-[13px]">
              <span className="text-ink">{s.nombre}</span>
              <span className="text-[oklch(62%_0.13_70)]">{s.dias_inactivo} días</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
