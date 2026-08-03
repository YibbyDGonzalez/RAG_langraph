import { AlertsSection } from "@/components/report/AlertsSection";
import { DayDistCard } from "@/components/report/DayDistCard";
import { HeatmapCard } from "@/components/report/HeatmapCard";
import { KpiGrid } from "@/components/report/KpiGrid";
import { WeeklyChart } from "@/components/report/WeeklyChart";
import type { PulsoData } from "@/lib/report-types";

export function PulsoView({ data }: { data: PulsoData }) {
  return (
    <div className="flex flex-col gap-7">
      <KpiGrid data={data} />
      <AlertsSection alertas={data.alertas} temasGenerados={data.temas_generados} />
      <WeeklyChart data={data.sparkline} />
      {data.temporal && (
        <div className="grid grid-cols-[1.3fr_1fr] gap-[18px] items-start">
          <DayDistCard temporal={data.temporal} />
          <HeatmapCard temporal={data.temporal} />
        </div>
      )}
    </div>
  );
}
