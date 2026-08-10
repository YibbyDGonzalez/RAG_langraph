export interface KpiValor {
  valor: number;
  delta_pct: number | null;
  valor_fmt?: string;
}

export interface Kpis {
  preguntas: KpiValor;
  estudiantes: KpiValor;
  sesiones: KpiValor;
  preguntas_por_estudiante: KpiValor;
  tiempo_promedio_sesion: KpiValor;
}

export interface SparklinePoint {
  semana: string;
  n_preguntas: number;
}

export interface Temporal {
  por_hora: Record<string, number>;
  por_dia: Record<string, number>;
  heatmap: Record<string, Record<string, number>>;
  duracion_promedio_min: number;
  top2_dias_pct: number;
  top2_dias: string[];
}

export interface Alerta {
  icono: string;
  texto: string;
  nivel_destino: "temas" | "estudiantes";
  filtro: { tema?: string } | null;
}

export interface PulsoData {
  kpis: Kpis;
  sparkline: SparklinePoint[];
  temporal: Temporal | null;
  alertas: Alerta[];
  temas_generados: boolean;
  total_estudiantes: number;
}

export interface Tema {
  nombre: string;
  n_preguntas: number;
  pct: number;
  ejemplos: string[];
}

export interface EvolucionSemanalPunto {
  semana: string;
  [tema: string]: string | number;
}

export interface TemasEstado {
  status: "idle" | "generado";
  temas?: Tema[];
  preguntas_destacadas?: string[];
  evolucion_semanal?: EvolucionSemanalPunto[];
}

export interface EstudianteRoster {
  usuario: string;
  nombre: string;
}

export interface EstudianteFila extends EstudianteRoster {
  n_preguntas: number;
  n_sesiones: number;
  ultimos_temas: string[];
}

export interface EstudianteInactivo extends EstudianteRoster {
  ultima_actividad: string | null;
  dias_inactivo: number;
}

export interface Histograma {
  "0": number;
  "1-5": number;
  "6-20": number;
  "20+": number;
}

export interface EstudiantesData {
  tabla: EstudianteFila[];
  histograma: Histograma;
  nunca_usado: EstudianteRoster[];
  silenciosos: EstudianteInactivo[];
}

export interface UltimaPregunta {
  timestamp: string;
  session_id: string;
  pregunta: string;
  respuesta: string;
}

export interface TimelinePunto {
  dia: string;
  n: number;
}

export interface EstudianteDetalle {
  usuario: string;
  nombre: string;
  n_preguntas: number;
  n_sesiones: number;
  primera_actividad: string | null;
  ultima_actividad: string | null;
  ultimas_preguntas: UltimaPregunta[];
  timeline: TimelinePunto[];
  temas_tocados: string[];
  temas_no_tocados: string[];
}

export interface ReportMeta {
  min_date: string | null;
  max_date: string | null;
}

export interface MeInfo {
  user_id: string;
  role: string;
  name: string;
}
