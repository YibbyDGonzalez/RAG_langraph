import json
import os

import plotly.graph_objects as go
import plotly.utils
from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")
DIAS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# Paleta consistente con el estilo de la app
_AZUL_OSCURO = "#1B4F72"
_AZUL_MEDIO  = "#2E86AB"
_VERDE       = "#17A589"
_GRID        = "#eef2f7"
_FONT        = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"


def _fig_json(fig: go.Figure) -> str:
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def _format_duracion(minutos: float) -> str:
    if minutos < 1:
        return "menos de 1 minuto"
    if minutos < 60:
        return f"{minutos:.0f} minutos"
    h = int(minutos // 60)
    m = int(minutos % 60)
    return f"{h} hora{'s' if h != 1 else ''} {m} min"


def _chart_temas(temas: list) -> str:
    if not temas:
        return ""
    nombres = [t["nombre"] for t in reversed(temas)]
    conteos = [t["n_preguntas"] for t in reversed(temas)]
    fig = go.Figure(go.Bar(
        x=conteos,
        y=nombres,
        orientation="h",
        marker_color=_VERDE,
        text=[f"  {c}" for c in conteos],
        textposition="outside",
        hovertemplate="%{y}: %{x} preguntas<extra></extra>",
    ))
    fig.update_layout(
        margin=dict(l=10, r=70, t=10, b=20),
        height=max(200, len(temas) * 52),
        xaxis_title="Número de preguntas",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family=_FONT, size=13),
    )
    fig.update_xaxes(gridcolor=_GRID, zeroline=False)
    fig.update_yaxes(tickfont=dict(size=12))
    return _fig_json(fig)


def _chart_heatmap(temporal: dict) -> str:
    hm = temporal["heatmap"]
    z = [[hm[dia].get(h, 0) for h in range(24)] for dia in DIAS_ES]
    fig = go.Figure(go.Heatmap(
        z=z,
        x=[f"{h:02d}:00" for h in range(24)],
        y=DIAS_ES,
        colorscale=[[0, "#EBF5FB"], [1, _AZUL_OSCURO]],
        showscale=True,
        colorbar=dict(title="Preguntas", thickness=12, len=0.85),
        hovertemplate="%{y} a las %{x}: %{z} preguntas<extra></extra>",
    ))
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=45),
        height=280,
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family=_FONT, size=12),
        xaxis=dict(title="Hora del día", tickangle=-45),
    )
    return _fig_json(fig)


def _chart_hora(temporal: dict) -> str:
    ph = temporal["por_hora"]
    conteos = [ph.get(h, 0) for h in range(24)]
    fig = go.Figure(go.Bar(
        x=[f"{h:02d}:00" for h in range(24)],
        y=conteos,
        marker_color=_AZUL_MEDIO,
        hovertemplate="%{x}: %{y} preguntas<extra></extra>",
    ))
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=50),
        height=240,
        xaxis=dict(title="Hora", tickangle=-45),
        yaxis=dict(title="Preguntas", gridcolor=_GRID),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family=_FONT, size=11),
    )
    return _fig_json(fig)


def _chart_dia(temporal: dict) -> str:
    pd_ = temporal["por_dia"]
    conteos = [pd_.get(dia, 0) for dia in DIAS_ES]
    fig = go.Figure(go.Bar(
        x=DIAS_ES,
        y=conteos,
        marker_color=_AZUL_OSCURO,
        hovertemplate="%{x}: %{y} preguntas<extra></extra>",
    ))
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=40),
        height=240,
        xaxis=dict(title="Día de la semana"),
        yaxis=dict(title="Preguntas", gridcolor=_GRID),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family=_FONT, size=11),
    )
    return _fig_json(fig)


def render_report(
    uso: dict,
    temporal: dict,
    temas: list,
    desde: str,
    hasta: str,
    generado_en: str,
) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("report_template.html")

    ctx = {
        # Período y metadata
        "desde": desde,
        "hasta": hasta,
        "generado_en": generado_en,
        # Sección 1: cuánto se usa
        "n_preguntas": uso["n_preguntas"],
        "n_usuarios": uso["n_usuarios"],
        "n_sesiones": uso["n_sesiones"],
        "promedio_preguntas": uso["promedio_preguntas_por_sesion"],
        # Sección 2: temas
        "temas": temas,
        "temas_chart_json": _chart_temas(temas),
        # Sección 3: temporal
        "duracion_promedio_str": _format_duracion(temporal["duracion_promedio_min"]),
        "top2_pct": temporal["top2_dias_pct"],
        "top2_dias": temporal["top2_dias"],
        "hay_concentracion": temporal["top2_dias_pct"] >= 40,
        "heatmap_json": _chart_heatmap(temporal),
        "hora_json": _chart_hora(temporal),
        "dia_json": _chart_dia(temporal),
    }
    return template.render(**ctx)
