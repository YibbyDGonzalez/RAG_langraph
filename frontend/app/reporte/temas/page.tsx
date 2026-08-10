import { TemasView } from "@/components/report/TemasView";
import { fetchReportMeta, fetchTemasEstado } from "@/lib/report-api";

interface TemasPageProps {
  searchParams: Promise<{ desde?: string; hasta?: string }>;
}

export default async function TemasPage({ searchParams }: TemasPageProps) {
  const params = await searchParams;
  const meta = await fetchReportMeta();

  const desde = params.desde ?? meta?.min_date ?? "";
  const hasta = params.hasta ?? meta?.max_date ?? "";

  if (!desde || !hasta) {
    return <div className="text-sm text-ink-soft">No hay datos disponibles todavía.</div>;
  }

  const estado = await fetchTemasEstado({ desde, hasta });
  if (!estado) {
    return <div className="text-sm text-danger">No se pudo cargar el estado del análisis de temas.</div>;
  }

  return <TemasView initialEstado={estado} desde={desde} hasta={hasta} />;
}
