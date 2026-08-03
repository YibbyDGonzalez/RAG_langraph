import type { TimelinePunto } from "@/lib/report-types";

const W = 560;
const H = 80;

export function StudentSparkline({ timeline }: { timeline: TimelinePunto[] }) {
  if (timeline.length === 0) {
    return <div className="text-sm text-ink-muted">Sin actividad registrada.</div>;
  }

  const max = Math.max(...timeline.map((t) => t.n), 1);
  const coords = timeline.map((t, i) => ({
    x: timeline.length > 1 ? (i / (timeline.length - 1)) * (W - 20) + 10 : W / 2,
    y: H - 10 - (t.n / max) * (H - 20),
  }));
  const points = coords.map((c) => `${c.x},${c.y}`).join(" ");

  return (
    <div>
      <div className="text-base font-semibold text-ink mb-3.5">Actividad diaria — histórico completo</div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-20">
        <polyline points={points} fill="none" stroke="var(--color-navy)" strokeWidth={2} />
        {coords.map((c, i) => (
          <circle key={i} cx={c.x} cy={c.y} r={2.5} fill="var(--color-navy)" />
        ))}
      </svg>
    </div>
  );
}
