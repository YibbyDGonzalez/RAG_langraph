import sqlite3

import pandas as pd


def detalle_estudiante(db_path: str, usuario_norm: str, tema_por_pregunta: dict = None) -> dict:
    """
    Detalle mínimo suficiente de un estudiante para el Nivel 4 (vista individual):
    conteos agregados, últimas 3-5 preguntas (no todo el historial), timeline
    diario simple y perfil temático (temas tocados vs. no tocados).

    usuario_norm: usuario en minúsculas. Se compara con LOWER(usuario) porque
    la tabla `consultas` guarda el username con el case original de login,
    que no siempre coincide en mayúsculas con el roster (users.yaml).

    tema_por_pregunta: mapeo pregunta_normalizada -> {"cluster_id", "nombre_tema"}
    (el mismo que retorna topic_analysis.compute_topics_detallado). Si es None
    u está vacío, el perfil temático queda vacío.
    """
    conn = sqlite3.connect(db_path)
    try:
        resumen = pd.read_sql_query(
            "SELECT COUNT(*) AS n_preguntas, COUNT(DISTINCT session_id) AS n_sesiones, "
            "MIN(timestamp) AS primera, MAX(timestamp) AS ultima "
            "FROM consultas WHERE LOWER(usuario) = ?",
            conn, params=(usuario_norm,),
        ).iloc[0]

        ultimas = pd.read_sql_query(
            "SELECT timestamp, session_id, pregunta, respuesta FROM consultas "
            "WHERE LOWER(usuario) = ? ORDER BY timestamp DESC LIMIT 5",
            conn, params=(usuario_norm,),
        )

        timeline = pd.read_sql_query(
            "SELECT DATE(timestamp) AS dia, COUNT(*) AS n FROM consultas "
            "WHERE LOWER(usuario) = ? GROUP BY dia ORDER BY dia",
            conn, params=(usuario_norm,),
        )

        todas_preguntas = pd.read_sql_query(
            "SELECT pregunta FROM consultas WHERE LOWER(usuario) = ?",
            conn, params=(usuario_norm,),
        )
    finally:
        conn.close()

    temas_tocados, temas_no_tocados = [], []
    if tema_por_pregunta:
        vistos = set()
        for p in todas_preguntas["pregunta"].dropna():
            info = tema_por_pregunta.get(p.strip())
            if info:
                vistos.add(info["nombre_tema"])
        temas_tocados = sorted(vistos)
        todos_los_temas = {info["nombre_tema"] for info in tema_por_pregunta.values()}
        temas_no_tocados = sorted(todos_los_temas - vistos)

    return {
        "n_preguntas": int(resumen["n_preguntas"] or 0),
        "n_sesiones": int(resumen["n_sesiones"] or 0),
        "primera_actividad": resumen["primera"],
        "ultima_actividad": resumen["ultima"],
        "ultimas_preguntas": ultimas.to_dict("records"),
        "timeline": timeline.to_dict("records"),
        "temas_tocados": temas_tocados,
        "temas_no_tocados": temas_no_tocados,
    }
