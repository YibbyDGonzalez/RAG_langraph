import { PulsoView } from "@/components/report/PulsoView";
import { fetchPulso, fetchReportMeta } from "@/lib/report-api";
import type { RolFiltro } from "@/lib/report-types";

interface PulsoPageProps {
  searchParams: Promise<{ desde?: string; hasta?: string; rol?: string }>;
}

export default async function PulsoPage({ searchParams }: PulsoPageProps) {
  const params = await searchParams;
  const meta = await fetchReportMeta();

  const desde = params.desde ?? meta?.min_date ?? "";
  const hasta = params.hasta ?? meta?.max_date ?? "";
  const rol = (params.rol as RolFiltro) ?? "todos";

  if (!desde || !hasta) {
    return <div className="text-sm text-ink-soft">No hay datos disponibles todavía.</div>;
  }

  const data = await fetchPulso({ desde, hasta, rol });
  if (!data) {
    return <div className="text-sm text-danger">No se pudo cargar el Pulso del curso.</div>;
  }

  return <PulsoView data={data} />;
}
