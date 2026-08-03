import Link from "next/link";

import { StudentBanner } from "@/components/report/StudentBanner";
import { StudentKpis } from "@/components/report/StudentKpis";
import { StudentQuestions } from "@/components/report/StudentQuestions";
import { StudentSparkline } from "@/components/report/StudentSparkline";
import { StudentTopicProfile } from "@/components/report/StudentTopicProfile";
import { fetchEstudianteDetalle, fetchReportMeta } from "@/lib/report-api";
import type { RolFiltro } from "@/lib/report-types";

interface EstudianteDetallePageProps {
  params: Promise<{ usuario: string }>;
  searchParams: Promise<{ desde?: string; hasta?: string; rol?: string }>;
}

export default async function EstudianteDetallePage({ params, searchParams }: EstudianteDetallePageProps) {
  const { usuario } = await params;
  const sp = await searchParams;
  const meta = await fetchReportMeta();

  const desde = sp.desde ?? meta?.min_date ?? "";
  const hasta = sp.hasta ?? meta?.max_date ?? "";
  const rol = (sp.rol as RolFiltro) ?? "todos";
  const backQs = new URLSearchParams({ desde, hasta, rol }).toString();

  if (!desde || !hasta) {
    return <div className="text-sm text-ink-soft">No hay datos disponibles todavía.</div>;
  }

  const detalle = await fetchEstudianteDetalle(usuario, { desde, hasta, rol });
  if (!detalle) {
    return <div className="text-sm text-danger">No se pudo cargar el detalle del estudiante.</div>;
  }

  return (
    <div className="flex flex-col gap-[22px]">
      <StudentBanner />

      <Link href={`/reporte/estudiantes?${backQs}`} className="self-start text-sm font-semibold text-navy">
        ‹ Volver a Estudiantes
      </Link>

      <div>
        <div className="text-[13px] font-semibold text-ink-muted uppercase tracking-wide">Estudiante</div>
        <div className="text-[26px] font-semibold text-ink mt-1">{detalle.nombre}</div>
      </div>

      <StudentKpis
        totalPreguntas={detalle.n_preguntas}
        totalSesiones={detalle.n_sesiones}
        ultimaActividad={detalle.ultima_actividad}
      />

      <div className="bg-surface border border-border rounded-2xl px-[26px] py-6">
        <StudentSparkline timeline={detalle.timeline} />
      </div>

      <div className="bg-surface border border-border rounded-2xl px-[26px] py-6">
        <StudentQuestions preguntas={detalle.ultimas_preguntas} />
      </div>

      <div className="bg-surface border border-border rounded-2xl px-[26px] py-6">
        <StudentTopicProfile tocados={detalle.temas_tocados} noTocados={detalle.temas_no_tocados} />
      </div>
    </div>
  );
}
