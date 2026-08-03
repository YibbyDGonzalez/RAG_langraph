interface StudentTopicProfileProps {
  tocados: string[];
  noTocados: string[];
}

export function StudentTopicProfile({ tocados, noTocados }: StudentTopicProfileProps) {
  return (
    <div>
      <div className="text-base font-semibold text-ink mb-3.5">Perfil temático</div>
      {tocados.length === 0 && noTocados.length === 0 ? (
        <div className="text-sm text-ink-muted">
          Genera el análisis de temas en la pestaña Temas para ver el perfil temático.
        </div>
      ) : (
        <div className="flex gap-2 flex-wrap">
          {tocados.map((t) => (
            <span
              key={t}
              className="text-xs font-medium bg-[oklch(94%_0.03_170)] text-[oklch(35%_0.09_170)] px-3 py-1.5 rounded-full"
            >
              {t}
            </span>
          ))}
          {noTocados.map((t) => (
            <span key={t} className="text-xs bg-surface-alt text-ink-muted px-3 py-1.5 rounded-full">
              {t}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
