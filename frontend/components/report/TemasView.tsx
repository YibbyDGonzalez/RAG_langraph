"use client";

import { useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { TemasGeneratingCard } from "@/components/report/TemasGeneratingCard";
import { TemasIdleCard } from "@/components/report/TemasIdleCard";
import { TemasResultado } from "@/components/report/TemasResultado";
import type { EvolucionSemanalPunto, Tema, TemasEstado } from "@/lib/report-types";

const FASES = [
  "Agrupando preguntas por significado...",
  "Nombrando cada grupo temático...",
  "Calculando evolución semanal...",
];

interface TemasViewProps {
  initialEstado: TemasEstado;
  desde: string;
  hasta: string;
}

export function TemasView({ initialEstado, desde, hasta }: TemasViewProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const focoTema = searchParams.get("tema");

  const [status, setStatus] = useState<"idle" | "generando" | "generado">(
    initialEstado.status === "generado" ? "generado" : "idle",
  );
  const [temas, setTemas] = useState<Tema[]>(initialEstado.temas ?? []);
  const [evolucion, setEvolucion] = useState<EvolucionSemanalPunto[]>(initialEstado.evolucion_semanal ?? []);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [fase, setFase] = useState(FASES[0]);
  const [expandido, setExpandido] = useState<Record<string, boolean>>(
    focoTema ? { [focoTema]: true } : {},
  );
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  async function generar() {
    setStatus("generando");
    setErrorMsg(null);
    setFase(FASES[0]);
    let i = 0;
    intervalRef.current = setInterval(() => {
      i = Math.min(i + 1, FASES.length - 1);
      setFase(FASES[i]);
    }, 4000);

    try {
      const qs = new URLSearchParams({ desde, hasta }).toString();
      const res = await fetch(`/api/report/temas/generate?${qs}`, { method: "POST" });
      const data = await res.json();

      if (!res.ok) {
        setErrorMsg(data.detail ?? "No se pudo generar el análisis.");
        setStatus("idle");
        return;
      }

      setTemas(data.temas ?? []);
      setEvolucion(data.evolucion_semanal ?? []);
      setStatus("generado");
      if (focoTema) setExpandido((prev) => ({ ...prev, [focoTema]: true }));
    } catch {
      setErrorMsg("No se pudo generar el análisis. Intenta de nuevo.");
      setStatus("idle");
    } finally {
      if (intervalRef.current) clearInterval(intervalRef.current);
    }
  }

  function quitarFoco() {
    const params = new URLSearchParams(searchParams.toString());
    params.delete("tema");
    const qs = params.toString();
    router.push(`/reporte/temas${qs ? `?${qs}` : ""}`);
  }

  return (
    <div className="flex flex-col gap-[22px]">
      {focoTema && (
        <div className="flex items-center justify-between bg-surface-selected rounded-[10px] px-[18px] py-3 text-[13px] text-navy">
          <span>
            Foco desde alerta: <strong>{focoTema}</strong>
          </span>
          <button
            onClick={quitarFoco}
            className="bg-transparent border-none text-navy font-semibold cursor-pointer text-[13px]"
          >
            Quitar foco ✕
          </button>
        </div>
      )}

      {status === "idle" && <TemasIdleCard onGenerate={() => void generar()} errorMsg={errorMsg} />}
      {status === "generando" && <TemasGeneratingCard fase={fase} />}
      {status === "generado" && (
        <TemasResultado
          temas={temas}
          evolucion={evolucion}
          expandido={expandido}
          onToggle={(nombre) => setExpandido((prev) => ({ ...prev, [nombre]: !prev[nombre] }))}
        />
      )}
    </div>
  );
}
