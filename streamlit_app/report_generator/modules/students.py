import pandas as pd


def tabla_estudiantes(df: pd.DataFrame, tema_por_pregunta: dict, roster: dict) -> list:
    """
    Una fila por cada cuenta del roster, con su actividad en el periodo
    seleccionado (df ya viene filtrado por fecha). Estudiantes sin actividad
    en el periodo aparecen igual, con 0 preguntas/sesiones.

    Orden por defecto: ascendente por número de preguntas (criterio
    pedagógico — quién menos ha usado la herramienta encabeza la lista),
    NO alfabético.

    Retorna: [{"usuario": str, "nombre": str, "n_preguntas": int,
               "n_sesiones": int, "ultimos_temas": list[str]}, ...]
    """
    agregado = {}
    if not df.empty:
        df = df.copy()
        df["usuario_norm"] = df["usuario"].astype(str).str.lower()

        if tema_por_pregunta:
            df["tema"] = df["pregunta"].str.strip().map(
                lambda p: tema_por_pregunta.get(p, {}).get("nombre_tema")
            )
        else:
            df["tema"] = None

        for usuario_norm, grupo in df.groupby("usuario_norm"):
            grupo_ordenado = grupo.sort_values("timestamp", ascending=False)
            ultimos_temas = []
            for tema in grupo_ordenado["tema"]:
                if tema and tema not in ultimos_temas:
                    ultimos_temas.append(tema)
                if len(ultimos_temas) >= 3:
                    break
            agregado[usuario_norm] = {
                "n_preguntas": int(len(grupo)),
                "n_sesiones": int(grupo["session_id"].nunique()),
                "ultimos_temas": ultimos_temas,
            }

    filas = []
    for usuario_norm, nombre in roster.items():
        datos = agregado.get(usuario_norm, {"n_preguntas": 0, "n_sesiones": 0, "ultimos_temas": []})
        filas.append({
            "usuario": usuario_norm,
            "nombre": nombre,
            "n_preguntas": datos["n_preguntas"],
            "n_sesiones": datos["n_sesiones"],
            "ultimos_temas": datos["ultimos_temas"],
        })

    filas.sort(key=lambda f: f["n_preguntas"])
    return filas


def histograma_esfuerzo(tabla_estudiantes_: list) -> dict:
    """Cuenta estudiantes por bin de esfuerzo: 0 / 1-5 / 6-20 / 20+ preguntas."""
    bins = {"0": 0, "1-5": 0, "6-20": 0, "20+": 0}
    for fila in tabla_estudiantes_:
        n = fila["n_preguntas"]
        if n == 0:
            bins["0"] += 1
        elif n <= 5:
            bins["1-5"] += 1
        elif n <= 20:
            bins["6-20"] += 1
        else:
            bins["20+"] += 1
    return bins
