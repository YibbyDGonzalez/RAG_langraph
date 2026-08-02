"""
roles.py — Distingue Docente vs Estudiante a partir del username.

No existe un campo de rol explícito en users.yaml: el rol se infiere del
prefijo del username (ej. 'Docente3' -> Docente, 'Estudiante1' -> Estudiante),
tal como se acordó al crear las cuentas de estudiante.
"""

ROL_DOCENTE = "Docente"
ROL_ESTUDIANTE = "Estudiante"


def rol_de_usuario(usuario: str) -> str:
    """Infiere el rol a partir del prefijo del username (case-insensitive).

    Cualquier username que no empiece por 'docente' se trata como Estudiante,
    para que el acceso a secciones restringidas a Docente sea deny-by-default.
    """
    u = (usuario or "").strip().lower()
    if u.startswith("docente"):
        return ROL_DOCENTE
    return ROL_ESTUDIANTE
