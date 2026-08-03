import { authHeader, fastapiUrl } from "@/lib/fastapi";
import type { EstudiantesData, MeInfo, PulsoData, ReportMeta, RolFiltro, TemasEstado } from "@/lib/report-types";

export async function fetchMeReport(): Promise<MeInfo | null> {
  const auth = await authHeader();
  if (!auth) return null;
  const res = await fetch(fastapiUrl("/api/auth/me"), { headers: auth, cache: "no-store" });
  if (!res.ok) return null;
  return (await res.json()) as MeInfo;
}

export async function fetchReportMeta(): Promise<ReportMeta | null> {
  const auth = await authHeader();
  if (!auth) return null;
  const res = await fetch(fastapiUrl("/api/report/meta"), { headers: auth, cache: "no-store" });
  if (!res.ok) return null;
  return (await res.json()) as ReportMeta;
}

interface Periodo {
  desde: string;
  hasta: string;
  rol: RolFiltro;
}

export async function fetchPulso(periodo: Periodo): Promise<PulsoData | null> {
  const auth = await authHeader();
  if (!auth) return null;
  const qs = new URLSearchParams({ desde: periodo.desde, hasta: periodo.hasta, rol: periodo.rol }).toString();
  const res = await fetch(fastapiUrl(`/api/report/pulso?${qs}`), { headers: auth, cache: "no-store" });
  if (!res.ok) return null;
  return (await res.json()) as PulsoData;
}

export async function fetchTemasEstado(periodo: Periodo): Promise<TemasEstado | null> {
  const auth = await authHeader();
  if (!auth) return null;
  const qs = new URLSearchParams({ desde: periodo.desde, hasta: periodo.hasta, rol: periodo.rol }).toString();
  const res = await fetch(fastapiUrl(`/api/report/temas?${qs}`), { headers: auth, cache: "no-store" });
  if (!res.ok) return null;
  return (await res.json()) as TemasEstado;
}

export async function fetchEstudiantes(periodo: Periodo): Promise<EstudiantesData | null> {
  const auth = await authHeader();
  if (!auth) return null;
  const qs = new URLSearchParams({ desde: periodo.desde, hasta: periodo.hasta, rol: periodo.rol }).toString();
  const res = await fetch(fastapiUrl(`/api/report/estudiantes?${qs}`), { headers: auth, cache: "no-store" });
  if (!res.ok) return null;
  return (await res.json()) as EstudiantesData;
}
