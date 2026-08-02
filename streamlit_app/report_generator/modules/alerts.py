import pandas as pd


def detectar_tema_en_alza(evolucion_semanal: pd.DataFrame, min_delta_pct: float = 30.0):
    """
    Compara las dos últimas semanas de evolucion_semanal_por_tema() y retorna
    el tema con mayor incremento porcentual, si supera min_delta_pct.

    Retorna {"nombre": str, "delta_pct": float} o None si ningún tema sube
    lo suficiente (o no hay al menos 2 semanas de datos).
    """
    if evolucion_semanal is None or evolucion_semanal.empty or len(evolucion_semanal.index) < 2:
        return None

    ultima_semana = evolucion_semanal.iloc[-1]
    semana_anterior = evolucion_semanal.iloc[-2]

    mejor = None
    for tema in evolucion_semanal.columns:
        anterior = semana_anterior[tema]
        actual = ultima_semana[tema]
        if anterior == 0:
            continue
        delta_pct = (actual - anterior) / anterior * 100
        if delta_pct >= min_delta_pct and (mejor is None or delta_pct > mejor["delta_pct"]):
            mejor = {"nombre": tema, "delta_pct": round(delta_pct, 0)}

    return mejor


def generar_alertas(
    tema_en_alza,
    temas_debiles: list,
    nunca_usado: list,
    silenciosos: list,
    concentracion_uso,
    max_alertas: int = 3,
) -> list:
    """
    Arma las 2-3 tarjetas de alerta automática del Nivel 1 (Pulso), priorizando
    señales que requieren atención del docente. Cada alerta indica a qué nivel
    navegar al hacer click.

    Parámetros:
      tema_en_alza: dict de detectar_tema_en_alza() o None.
      temas_debiles: lista de retrieval_quality.temas_con_retrieval_debil()
        (ya viene ordenada del más débil al menos débil).
      nunca_usado: lista de roster.nunca_usado().
      silenciosos: lista de roster.silenciosos().
      concentracion_uso: {"pct": float, "dias": list[str]} si el uso está
        concentrado (>=40% en 2 días), o None.

    Retorna: [{"icono": str, "texto": str, "nivel_destino": "temas"|"estudiantes",
               "filtro": dict|None}, ...] (máximo max_alertas)
    """
    candidatos = []

    if tema_en_alza:
        candidatos.append({
            "icono": "📈",
            "texto": (
                f'Subieron las preguntas sobre "{tema_en_alza["nombre"]}" esta semana '
                f'(+{int(tema_en_alza["delta_pct"])}%).'
            ),
            "nivel_destino": "temas",
            "filtro": {"tema": tema_en_alza["nombre"]},
        })

    if temas_debiles:
        peor = temas_debiles[0]
        candidatos.append({
            "icono": "⚠️",
            "texto": (
                f'"{peor["tema"]}" tiene consultas frecuentes con retrieval débil '
                f'(similitud media {peor["score_medio"]}).'
            ),
            "nivel_destino": "temas",
            "filtro": {"tema": peor["tema"]},
        })

    n_atencion = len(nunca_usado) + len(silenciosos)
    if n_atencion > 0:
        candidatos.append({
            "icono": "😴",
            "texto": f"{n_atencion} estudiante(s) no han usado la herramienta o llevan 2+ semanas sin entrar.",
            "nivel_destino": "estudiantes",
            "filtro": None,
        })

    if concentracion_uso:
        candidatos.append({
            "icono": "🕒",
            "texto": (
                f'El uso se concentra en pocos días: {concentracion_uso["pct"]}% '
                f'en {", ".join(concentracion_uso["dias"])}.'
            ),
            "nivel_destino": "estudiantes",
            "filtro": None,
        })

    return candidatos[:max_alertas]
