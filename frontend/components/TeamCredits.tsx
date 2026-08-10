interface TeamMember {
  name: string;
  email: string;
}

const ESTUDIANTES: TeamMember[] = [
  { name: "Yibby Gonzalez", email: "gonzalez_yibby@javeriana.edu.co" },
  { name: "Sebastian Ruiz", email: "juan.ruizc@javeriana.edu.co" },
];

const DOCENTES: TeamMember[] = [
  { name: "Juan Pajaro", email: "juanpajaro@javeriana.edu.co" },
  { name: "Fabian Gil", email: "fgil@javeriana.edu.co" },
];

function iniciales(nombre: string): string {
  return nombre
    .split(" ")
    .map((parte) => parte[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function GrupoEquipo({
  titulo,
  miembros,
  tono,
}: {
  titulo: string;
  miembros: TeamMember[];
  tono: "navy" | "teal";
}) {
  const badge = tono === "navy" ? "bg-navy text-white" : "bg-teal text-white";
  return (
    <div className="flex flex-col gap-1.5">
      <div className="text-[9px] font-semibold uppercase tracking-[0.06em] text-ink-muted">{titulo}</div>
      {miembros.map((m) => (
        <div key={m.email} className="flex items-center gap-2">
          <div
            className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-semibold flex-shrink-0 ${badge}`}
          >
            {iniciales(m.name)}
          </div>
          <div className="min-w-0">
            <div className="text-[11px] font-medium text-ink truncate">{m.name}</div>
            <div className="text-[10px] text-ink-muted truncate">{m.email}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

export function TeamCredits() {
  return (
    <div className="flex flex-col gap-3 border-t border-border pt-3">
      <div className="text-[10px] font-semibold uppercase tracking-[0.04em] text-ink-muted">Equipo</div>
      <GrupoEquipo titulo="Estudiantes" miembros={ESTUDIANTES} tono="navy" />
      <GrupoEquipo titulo="Docentes" miembros={DOCENTES} tono="teal" />
    </div>
  );
}
