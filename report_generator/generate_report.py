#!/usr/bin/env python3
"""
Generador de reporte HTML de uso del Asistente MBE para docentes.

Uso básico:
    python generate_report.py

Con parámetros:
    python generate_report.py \\
        --db data/logs/mbe_logs.db \\
        --desde 2026-05-01 \\
        --hasta 2026-06-13 \\
        --salida reporte_junio.html

La API key de Groq se lee de la variable de entorno GROQ_API_KEY
o puede pasarse con --groq-key.
"""
import argparse
import os
import sys
from datetime import datetime

# Permite ejecutar el script desde cualquier directorio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.data_loader import load_data
from modules.usage_stats import compute_usage_stats
from modules.temporal_analysis import compute_temporal_stats
from modules.topic_analysis import compute_topics
from modules.html_renderer import render_report
import config


def _parse_args():
    p = argparse.ArgumentParser(
        description="Genera un reporte HTML de uso del Asistente MBE para docentes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--db",
        default=config.DB_PATH_DEFAULT,
        help=f"Ruta al archivo .db de logs (por defecto: {config.DB_PATH_DEFAULT})",
    )
    p.add_argument(
        "--desde",
        default=None,
        metavar="YYYY-MM-DD",
        help="Fecha de inicio del período (inclusive). Si se omite, desde el primer registro.",
    )
    p.add_argument(
        "--hasta",
        default=None,
        metavar="YYYY-MM-DD",
        help="Fecha de fin del período (inclusive). Si se omite, hasta el último registro.",
    )
    p.add_argument(
        "--salida",
        default="reporte_mbe.html",
        help="Nombre o ruta del archivo HTML de salida (por defecto: reporte_mbe.html)",
    )
    p.add_argument(
        "--groq-key",
        default=None,
        help="API key de Groq. Alternativa a la variable de entorno GROQ_API_KEY.",
    )
    return p.parse_args()


def main():
    args = _parse_args()

    # ── Validar API key ──────────────────────────────────────────────────────
    groq_key = args.groq_key or os.environ.get("GROQ_API_KEY")
    if not groq_key:
        print(
            "\nERROR: Se requiere la API key de Groq para nombrar los temas.\n"
            "  Opción A (recomendada): export GROQ_API_KEY=gsk_...\n"
            "  Opción B:               --groq-key gsk_...\n"
        )
        sys.exit(1)

    # ── Validar DB ───────────────────────────────────────────────────────────
    if not os.path.exists(args.db):
        print(f"\nERROR: No se encontró la base de datos: {args.db}\n")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("  Generador de reporte MBE")
    print("=" * 50)
    print(f"  Base de datos : {os.path.abspath(args.db)}")
    print(f"  Período       : {args.desde or '(inicio)'} → {args.hasta or '(hoy)'}")
    print(f"  Archivo salida: {args.salida}")
    print()

    # ── 1. Cargar datos ──────────────────────────────────────────────────────
    print("[1/4] Cargando y filtrando datos...")
    df = load_data(args.db, args.desde, args.hasta)
    if df.empty:
        print("\nERROR: No hay datos para el período indicado.\n")
        sys.exit(1)
    print(
        f"  → {len(df)} preguntas de {df['usuario'].nunique()} estudiante(s), "
        f"{df['session_id'].nunique()} sesión/sesiones.\n"
    )

    # ── 2. Estadísticas de uso ───────────────────────────────────────────────
    print("[2/4] Calculando estadísticas de uso...")
    uso = compute_usage_stats(df)
    print(
        f"  → Promedio {uso['promedio_preguntas_por_sesion']} preguntas/sesión.\n"
    )

    # ── 3. Análisis temporal ─────────────────────────────────────────────────
    print("[3/4] Analizando distribución temporal...")
    temporal = compute_temporal_stats(df)
    print(
        f"  → Duración promedio de sesión: {temporal['duracion_promedio_min']} min. "
        f"Top-2 días: {temporal['top2_dias_pct']}% del uso.\n"
    )

    # ── 4. Análisis de temas ─────────────────────────────────────────────────
    print("[4/4] Analizando temas (embeddings + clustering + Groq)...")
    temas = compute_topics(list(df["pregunta"]), groq_key)
    if temas:
        print(f"  → {len(temas)} grupo(s) temático(s) identificado(s).\n")
    else:
        print("  → Sin suficientes preguntas para agrupar por temas.\n")

    # ── Generar HTML ─────────────────────────────────────────────────────────
    desde_str = args.desde or df["timestamp"].min().strftime("%Y-%m-%d")
    hasta_str = args.hasta or df["timestamp"].max().strftime("%Y-%m-%d")
    generado_en = datetime.now().strftime("%d de %B de %Y a las %H:%M")

    print(f"Generando reporte HTML → {args.salida}")
    html = render_report(uso, temporal, temas, desde_str, hasta_str, generado_en)

    with open(args.salida, "w", encoding="utf-8") as f:
        f.write(html)

    ruta_abs = os.path.abspath(args.salida)
    print(f"\n✓ Reporte guardado en:\n  {ruta_abs}")
    print("  Ábrelo en cualquier navegador web para verlo.\n")


if __name__ == "__main__":
    main()
