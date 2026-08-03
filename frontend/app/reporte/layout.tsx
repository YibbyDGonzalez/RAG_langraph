import { redirect } from "next/navigation";

import { ReportSidebar } from "@/components/report/ReportSidebar";
import { ReportTopBar } from "@/components/report/ReportTopBar";
import { fetchMeReport, fetchReportMeta } from "@/lib/report-api";

export default async function ReporteLayout({ children }: { children: React.ReactNode }) {
  const me = await fetchMeReport();
  if (!me) redirect("/login");

  if (me.role !== "Docente") {
    return (
      <div className="min-h-screen w-full flex items-center justify-center bg-surface p-10">
        <div className="max-w-md text-center flex flex-col gap-3">
          <div className="text-lg font-semibold text-ink">Sin permisos</div>
          <p className="text-sm text-ink-soft">
            No tienes permisos para acceder al Reporte de Monitoreo. Esta sección es exclusiva para Docentes.
          </p>
        </div>
      </div>
    );
  }

  const meta = await fetchReportMeta();

  return (
    <div className="flex min-h-screen w-full text-ink bg-surface">
      <ReportSidebar teacherName={me.name} minDate={meta?.min_date ?? null} maxDate={meta?.max_date ?? null} />
      <main className="flex-1 flex flex-col gap-7 p-10 max-w-[1280px]">
        <ReportTopBar />
        {children}
      </main>
    </div>
  );
}
