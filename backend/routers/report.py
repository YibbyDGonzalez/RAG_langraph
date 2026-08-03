from fastapi import APIRouter, Depends, HTTPException, Query, Request

from backend.dependencies import require_role
from backend.services import report_service
from report_generator.modules.roles import ROL_DOCENTE

router = APIRouter(prefix="/report", dependencies=[Depends(require_role(ROL_DOCENTE))])


@router.get("/meta")
async def meta():
    return report_service.rango_fechas()


@router.get("/pulso")
async def pulso(
    request: Request,
    desde: str = Query(...),
    hasta: str = Query(...),
    rol: str = Query("todos"),
):
    return report_service.pulso(desde, hasta, rol, request.app.state.temas_cache)


@router.post("/temas/generate")
async def generar_temas(
    request: Request,
    desde: str = Query(...),
    hasta: str = Query(...),
    rol: str = Query("todos"),
):
    groq_key = report_service.groq_disponible()
    if not groq_key:
        raise HTTPException(
            status_code=503,
            detail="GROQ_API_KEY no configurada; el análisis de temas no está disponible.",
        )
    try:
        report_service.generar_temas(desde, hasta, rol, groq_key, request.app.state.temas_cache)
    except report_service.DatosInsuficientes as e:
        raise HTTPException(
            status_code=422,
            detail=f"Se necesitan al menos 5 preguntas para el análisis (período actual: {e.n}).",
        )
    # Mismo shape que GET /temas (incluye evolucion_semanal), ya con la caché poblada.
    return report_service.estado_temas(desde, hasta, rol, request.app.state.temas_cache)


@router.get("/temas")
async def estado_temas(
    request: Request,
    desde: str = Query(...),
    hasta: str = Query(...),
    rol: str = Query("todos"),
):
    return report_service.estado_temas(desde, hasta, rol, request.app.state.temas_cache)


@router.get("/estudiantes")
async def estudiantes(
    request: Request,
    desde: str = Query(...),
    hasta: str = Query(...),
    rol: str = Query("todos"),
):
    return report_service.estudiantes(desde, hasta, rol, request.app.state.temas_cache)


@router.get("/estudiantes/{usuario}")
async def estudiante_detalle(
    usuario: str,
    request: Request,
    desde: str = Query(...),
    hasta: str = Query(...),
    rol: str = Query("todos"),
):
    return report_service.estudiante_detalle(usuario, desde, hasta, rol, request.app.state.temas_cache)
