"use client";

import Image from "next/image";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { TeamCredits } from "@/components/TeamCredits";

interface ReportSidebarProps {
  teacherName: string;
  minDate: string | null;
  maxDate: string | null;
}

export function ReportSidebar({ teacherName, minDate, maxDate }: ReportSidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();

  const desde = searchParams.get("desde") ?? minDate ?? "";
  const hasta = searchParams.get("hasta") ?? maxDate ?? "";

  function updateParams(patch: Record<string, string>) {
    const params = new URLSearchParams(searchParams.toString());
    for (const [k, v] of Object.entries(patch)) params.set(k, v);
    router.push(`${pathname}?${params.toString()}`);
  }

  async function logout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }

  return (
    <aside className="w-[280px] min-w-[280px] bg-surface-alt border-r border-border flex flex-col p-7 gap-8">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-surface border border-border flex items-center justify-center p-1 flex-shrink-0">
          <Image src="/javeriana-crest.png" alt="Javeriana" width={32} height={32} className="w-full h-full object-contain" />
        </div>
        <div>
          <div className="text-[13px] font-semibold text-ink">Asistente MBE</div>
          <div className="text-xs text-ink-soft">Reporte docente</div>
        </div>
      </div>

      <div className="flex flex-col gap-2 p-3.5 bg-surface border border-border rounded-[10px]">
        <div className="text-[11px] font-semibold tracking-[0.04em] uppercase text-ink-muted">Docente</div>
        <div className="text-sm font-semibold text-ink">{teacherName}</div>
        <button
          onClick={() => void logout()}
          className="self-start text-[13px] font-medium text-ink-soft bg-transparent border-none p-0 cursor-pointer"
        >
          Cerrar sesión
        </button>
      </div>

      <div className="flex flex-col gap-2.5">
        <div className="text-[11px] font-semibold tracking-[0.04em] uppercase text-ink-muted">Período</div>
        <label className="flex flex-col gap-1 text-xs text-ink-soft">
          Desde
          <input
            type="date"
            value={desde}
            min={minDate ?? undefined}
            max={maxDate ?? undefined}
            onChange={(e) => updateParams({ desde: e.target.value })}
            className="border border-border rounded-lg px-2.5 py-2 text-[13px] font-sans text-ink bg-surface"
          />
        </label>
        <label className="flex flex-col gap-1 text-xs text-ink-soft">
          Hasta
          <input
            type="date"
            value={hasta}
            min={minDate ?? undefined}
            max={maxDate ?? undefined}
            onChange={(e) => updateParams({ hasta: e.target.value })}
            className="border border-border rounded-lg px-2.5 py-2 text-[13px] font-sans text-ink bg-surface"
          />
        </label>
      </div>

      <div className="mt-auto flex flex-col gap-3">
        <div className="text-[11px] text-ink-muted leading-relaxed">
          Vistas agregadas (Niveles 1–3). No incluyen identificación individual salvo tutoría explícita.
        </div>
        <TeamCredits />
      </div>
    </aside>
  );
}
