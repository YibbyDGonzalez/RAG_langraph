"use client";

export function TemasGeneratingCard({ fase }: { fase: string }) {
  return (
    <div className="bg-surface border border-border rounded-2xl p-12 flex flex-col items-center text-center gap-3.5 max-w-[640px] mx-auto">
      <div className="w-9 h-9 rounded-full border-[3px] border-border border-t-navy animate-spin" />
      <div className="text-[15px] font-semibold text-ink">{fase}</div>
      <div className="text-[13px] text-ink-muted">
        Esto puede tardar hasta 3 minutos. Puedes seguir usando el resto del reporte mientras tanto.
      </div>
    </div>
  );
}
