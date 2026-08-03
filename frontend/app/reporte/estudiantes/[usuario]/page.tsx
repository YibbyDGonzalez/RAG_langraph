import Link from "next/link";

// Nivel 4 (Estudiante individual) se implementa en la Fase 4e. Placeholder
// para que el botón "Ver" del roster navegue sin 404 mientras tanto.
export default async function EstudianteDetallePage({
  params,
}: {
  params: Promise<{ usuario: string }>;
}) {
  const { usuario } = await params;

  return (
    <div className="bg-surface border border-border rounded-2xl px-[26px] py-12 text-center text-sm text-ink-soft flex flex-col items-center gap-4">
      <div>
        El detalle individual de <strong>{usuario}</strong> se implementa en la Fase 4e.
      </div>
      <Link href="/reporte/estudiantes" className="text-navy font-semibold text-[13px]">
        ← Volver a Estudiantes
      </Link>
    </div>
  );
}
