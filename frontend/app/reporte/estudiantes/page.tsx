import { EffortHistogram } from "@/components/report/EffortHistogram";
import { NuncaUsadoCard } from "@/components/report/NuncaUsadoCard";
import { RosterTable } from "@/components/report/RosterTable";
import { SilenciososCard } from "@/components/report/SilenciososCard";
import { fetchEstudiantes, fetchReportMeta } from "@/lib/report-api";

interface EstudiantesPageProps {
  searchParams: Promise<{ desde?: string; hasta?: string }>;
}

export default async function EstudiantesPage({ searchParams }: EstudiantesPageProps) {
  const params = await searchParams;
  const meta = await fetchReportMeta();

  const desde = params.desde ?? meta?.min_date ?? "";
  const hasta = params.hasta ?? meta?.max_date ?? "";

  if (!desde || !hasta) {
    return <div className="text-sm text-ink-soft">No hay datos disponibles todavía.</div>;
  }

  const data = await fetchEstudiantes({ desde, hasta });
  if (!data) {
    return <div className="text-sm text-danger">No se pudo cargar la vista de Estudiantes.</div>;
  }

  const queryString = new URLSearchParams({ desde, hasta }).toString();

  return (
    <div className="flex flex-col gap-[22px]">
      <EffortHistogram histograma={data.histograma} />
      <div className="grid grid-cols-2 gap-[18px]">
        <SilenciososCard silenciosos={data.silenciosos} />
        <NuncaUsadoCard nuncaUsado={data.nunca_usado} />
      </div>
      <RosterTable tabla={data.tabla} queryString={queryString} />
    </div>
  );
}
