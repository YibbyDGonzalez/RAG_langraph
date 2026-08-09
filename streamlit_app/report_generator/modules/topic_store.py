"""
topic_store.py — persistencia y clasificación incremental de "Temas" (Nivel 2).

A diferencia de topic_analysis.compute_topics_detallado() (batch, stateless,
recalcula todo desde cero cada vez), este módulo mantiene una asignación
pregunta -> tema persistente en SQLite: una pregunta ya clasificada en un
tema nombrado nunca cambia de tema; las preguntas nuevas se clasifican
contra los temas existentes por similitud de embeddings, o se acumulan en
un tema residual ("Preguntas variadas") que se intenta sub-clusterizar
cuando crece lo suficiente — esa es la única circunstancia en la que una
pregunta cambia de tema_id.

`rol` ('todos'/'docentes'/'estudiantes') particiona el corpus: cada scope
tiene su propia taxonomía de temas, sus propios centroides y su propio
cursor de avance (mismo comportamiento que la caché por rol de hoy, ahora
persistente).
"""
import json
import os
import re
import sqlite3
import sys

import numpy as np
import pandas as pd
from groq import Groq

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

from .roles import filtrar_por_rol
from .topic_analysis import (
    _clusterizar_embeddings,
    _crear_completion_con_reintento,
    _nombrar_clusters,
    generar_embeddings,
)

TEMA_RESIDUAL_NOMBRE = "Preguntas variadas"


def init_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS temas (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                rol             TEXT NOT NULL,
                nombre          TEXT NOT NULL,
                es_residual     INTEGER NOT NULL DEFAULT 0,
                centroide       TEXT NOT NULL,
                n_preguntas     INTEGER NOT NULL DEFAULT 0,
                creado_en       DATETIME DEFAULT CURRENT_TIMESTAMP,
                actualizado_en  DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tema_preguntas (
                id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                rol                  TEXT NOT NULL,
                pregunta_norm        TEXT NOT NULL,
                tema_id              INTEGER NOT NULL REFERENCES temas(id),
                embedding            TEXT NOT NULL,
                primera_consulta_id  INTEGER NOT NULL,
                creado_en            DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(rol, pregunta_norm)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS temas_scope_estado (
                rol                 TEXT PRIMARY KEY,
                ultimo_consulta_id  INTEGER NOT NULL DEFAULT 0,
                ultima_corrida_en   DATETIME,
                destacadas_json     TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _leer_cursor(conn, rol: str) -> int:
    row = conn.execute(
        "SELECT ultimo_consulta_id FROM temas_scope_estado WHERE rol = ?", (rol,)
    ).fetchone()
    return row[0] if row else 0


def _preguntas_nuevas(conn, rol: str, cursor: int) -> pd.DataFrame:
    df = pd.read_sql_query(
        "SELECT id, usuario, pregunta FROM consultas WHERE id > ? ORDER BY id",
        conn, params=(cursor,),
    )
    df = df.dropna(subset=["pregunta"])
    df = df[df["pregunta"].str.strip() != ""]
    return filtrar_por_rol(df, rol)


def _normalizadas_existentes(conn, rol: str) -> set:
    filas = conn.execute(
        "SELECT pregunta_norm FROM tema_preguntas WHERE rol = ?", (rol,)
    ).fetchall()
    return {f[0] for f in filas}


def _pendientes_dedup(conn, rol: str) -> tuple:
    """Retorna (pendientes: list[(pregunta_norm, primera_consulta_id)], max_id_visto: int)."""
    cursor = _leer_cursor(conn, rol)
    candidatas = _preguntas_nuevas(conn, rol, cursor)
    max_id_visto = int(candidatas["id"].max()) if not candidatas.empty else cursor

    existentes = _normalizadas_existentes(conn, rol)
    vistas_en_batch = set()
    pendientes = []
    for _, fila in candidatas.iterrows():
        norm = fila["pregunta"].strip()
        if norm in existentes or norm in vistas_en_batch:
            continue
        vistas_en_batch.add(norm)
        pendientes.append((norm, int(fila["id"])))
    return pendientes, max_id_visto


def contar_pendientes(rol: str, db_path: str) -> int:
    conn = sqlite3.connect(db_path)
    try:
        pendientes, _ = _pendientes_dedup(conn, rol)
        return len(pendientes)
    finally:
        conn.close()


def estado_scope(rol: str, db_path: str) -> dict:
    conn = sqlite3.connect(db_path)
    try:
        existe = conn.execute(
            "SELECT 1 FROM temas WHERE rol = ? AND es_residual = 0 LIMIT 1", (rol,)
        ).fetchone() is not None
        row = conn.execute(
            "SELECT ultima_corrida_en, destacadas_json FROM temas_scope_estado WHERE rol = ?", (rol,)
        ).fetchone()
        ultima_actualizacion = row[0] if row else None
        destacadas = json.loads(row[1]) if row and row[1] else []
    finally:
        conn.close()
    return {
        "existe": existe,
        "pendientes": contar_pendientes(rol, db_path),
        "ultima_actualizacion": ultima_actualizacion,
        "destacadas": destacadas,
    }


def mapeo_pregunta_tema(rol: str, db_path: str) -> dict:
    conn = sqlite3.connect(db_path)
    try:
        filas = conn.execute(
            "SELECT tp.pregunta_norm, tp.tema_id, t.nombre "
            "FROM tema_preguntas tp JOIN temas t ON t.id = tp.tema_id "
            "WHERE tp.rol = ?", (rol,),
        ).fetchall()
    finally:
        conn.close()
    return {
        pregunta_norm: {"cluster_id": tema_id, "nombre_tema": nombre}
        for pregunta_norm, tema_id, nombre in filas
    }


def _cargar_temas(conn, rol: str) -> dict:
    filas = conn.execute(
        "SELECT id, nombre, es_residual, centroide, n_preguntas FROM temas WHERE rol = ?", (rol,)
    ).fetchall()
    return {
        fid: {
            "nombre": nombre,
            "es_residual": bool(es_residual),
            "centroide": np.array(json.loads(centroide), dtype=float),
            "n_preguntas": n_preguntas,
        }
        for fid, nombre, es_residual, centroide, n_preguntas in filas
    }


def _asegurar_residual(conn, rol: str, temas_actuales: dict, dim: int) -> int:
    for tid, t in temas_actuales.items():
        if t["es_residual"]:
            return tid
    centroide_inicial = np.zeros(dim)
    cur = conn.execute(
        "INSERT INTO temas (rol, nombre, es_residual, centroide, n_preguntas) VALUES (?, ?, 1, ?, 0)",
        (rol, TEMA_RESIDUAL_NOMBRE, json.dumps(centroide_inicial.tolist())),
    )
    tema_id = cur.lastrowid
    temas_actuales[tema_id] = {
        "nombre": TEMA_RESIDUAL_NOMBRE,
        "es_residual": True,
        "centroide": centroide_inicial,
        "n_preguntas": 0,
    }
    return tema_id


def _cos_sim(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _subclusterizar_residual(conn, rol: str, residual_id: int, groq_api_key: str) -> tuple:
    """Intenta partir el bucket residual en temas nuevos nombrados. Retorna
    (temas_nuevos, preguntas_reasignadas). Los miembros que sigan sin
    encajar (ruido de HDBSCAN) permanecen en el residual."""
    filas = conn.execute(
        "SELECT id, pregunta_norm, embedding FROM tema_preguntas WHERE rol = ? AND tema_id = ?",
        (rol, residual_id),
    ).fetchall()
    if len(filas) < config.TEMAS_MIN_PREGUNTAS_NUEVAS:
        return 0, 0

    embeddings = np.array([json.loads(f[2]) for f in filas], dtype=float)
    labels = _clusterizar_embeddings(embeddings)
    labels_validos = sorted(set(labels) - {-1})
    if not labels_validos:
        return 0, 0

    clusters_para_llm = [
        (label, [filas[i][1] for i in range(len(filas)) if labels[i] == label][:8])
        for label in labels_validos
    ]
    nombres_map = _nombrar_clusters(clusters_para_llm, Groq(api_key=groq_api_key))

    reasignadas = 0
    for label in labels_validos:
        indices = [i for i in range(len(filas)) if labels[i] == label]
        centroide = embeddings[indices].mean(axis=0)
        nombre = nombres_map.get(label) or f"Tema {label + 1}"
        cur = conn.execute(
            "INSERT INTO temas (rol, nombre, es_residual, centroide, n_preguntas) VALUES (?, ?, 0, ?, ?)",
            (rol, nombre, json.dumps(centroide.tolist()), len(indices)),
        )
        nuevo_tema_id = cur.lastrowid
        conn.executemany(
            "UPDATE tema_preguntas SET tema_id = ? WHERE id = ?",
            [(nuevo_tema_id, filas[i][0]) for i in indices],
        )
        reasignadas += len(indices)

    restantes = [i for i in range(len(filas)) if labels[i] == -1]
    if restantes:
        centroide_residual = embeddings[restantes].mean(axis=0)
    else:
        centroide_residual = np.zeros(embeddings.shape[1])
    conn.execute(
        "UPDATE temas SET centroide = ?, n_preguntas = ?, actualizado_en = CURRENT_TIMESTAMP WHERE id = ?",
        (json.dumps(centroide_residual.tolist()), len(restantes), residual_id),
    )
    return len(labels_validos), reasignadas


def _refrescar_destacadas(conn, rol: str, textos_nuevos: list, groq_api_key: str) -> list:
    row = conn.execute(
        "SELECT destacadas_json FROM temas_scope_estado WHERE rol = ?", (rol,)
    ).fetchone()
    previas = json.loads(row[0]) if row and row[0] else []
    candidatas = (previas + textos_nuevos)[:80]
    if not candidatas:
        return previas

    lista = "\n".join(f"  - {p}" for p in candidatas)
    prompt = (
        "Eres un asistente académico. De la siguiente lista de preguntas formuladas "
        "por estudiantes de medicina, selecciona hasta "
        f"{config.MAX_PREGUNTAS_DESTACADAS} que estén especialmente bien formuladas "
        "(claras, específicas, que reflejen buen razonamiento clínico) para que el "
        "docente las use como ejemplo en clase. Cítalas EXACTAMENTE como aparecen.\n\n"
        f"Preguntas:\n{lista}\n\n"
        'Devuelve ÚNICAMENTE un JSON sin texto adicional: {"destacadas": ["...", "..."]}'
    )
    try:
        client = Groq(api_key=groq_api_key)
        resp = _crear_completion_con_reintento(
            client,
            model=config.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.3,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
        data = json.loads(raw)
        destacadas = [str(d).strip() for d in data.get("destacadas", []) if str(d).strip()]
        return destacadas[: config.MAX_PREGUNTAS_DESTACADAS] or previas
    except Exception as e:
        print(f"    Advertencia al refrescar destacadas: {e}")
        return previas


def actualizar_scope(rol: str, groq_api_key: str, db_path: str) -> dict:
    """
    Bootstrap (scope nuevo, sin temas) y actualización incremental son la
    MISMA operación: un scope nuevo tiene 100% del corpus "pendiente", que
    cae en el residual y se sub-clusteriza igual que cualquier acumulación
    posterior. No hay dos rutas de código que mantener.
    """
    conn = sqlite3.connect(db_path, isolation_level=None)
    try:
        conn.execute("BEGIN IMMEDIATE")

        pendientes, max_id_visto = _pendientes_dedup(conn, rol)
        if len(pendientes) < config.TEMAS_MIN_PREGUNTAS_NUEVAS:
            conn.execute("ROLLBACK")
            return {"procesadas": 0, "temas_nuevos": 0, "reasignadas_desde_residual": 0}

        textos = [p[0] for p in pendientes]
        embeddings = generar_embeddings(textos)
        dim = embeddings.shape[1]

        temas_actuales = _cargar_temas(conn, rol)
        residual_id = _asegurar_residual(conn, rol, temas_actuales, dim)

        asignaciones = []
        fue_a_residual = False
        for (norm, primer_id), emb in zip(pendientes, embeddings):
            mejor_id, mejor_sim = None, -1.0
            for tid, t in temas_actuales.items():
                if t["es_residual"]:
                    continue
                sim = _cos_sim(emb, t["centroide"])
                if sim > mejor_sim:
                    mejor_sim, mejor_id = sim, tid

            if mejor_id is not None and mejor_sim >= config.TEMAS_SIMILITUD_UMBRAL:
                tema_id = mejor_id
            else:
                tema_id = residual_id
                fue_a_residual = True

            t = temas_actuales[tema_id]
            n_nuevo = t["n_preguntas"] + 1
            t["centroide"] = (t["centroide"] * t["n_preguntas"] + emb) / n_nuevo
            t["n_preguntas"] = n_nuevo
            asignaciones.append((norm, tema_id, emb, primer_id))

        for norm, tema_id, emb, primer_id in asignaciones:
            conn.execute(
                "INSERT INTO tema_preguntas (rol, pregunta_norm, tema_id, embedding, primera_consulta_id) "
                "VALUES (?, ?, ?, ?, ?)",
                (rol, norm, tema_id, json.dumps(emb.tolist()), primer_id),
            )

        for tid, t in temas_actuales.items():
            if tid == residual_id:
                continue
            conn.execute(
                "UPDATE temas SET centroide = ?, n_preguntas = ?, actualizado_en = CURRENT_TIMESTAMP WHERE id = ?",
                (json.dumps(t["centroide"].tolist()), t["n_preguntas"], tid),
            )

        temas_nuevos, reasignadas = 0, 0
        residual = temas_actuales[residual_id]
        if fue_a_residual and residual["n_preguntas"] >= config.TEMAS_MIN_PREGUNTAS_NUEVAS:
            temas_nuevos, reasignadas = _subclusterizar_residual(conn, rol, residual_id, groq_api_key)
        else:
            conn.execute(
                "UPDATE temas SET centroide = ?, n_preguntas = ?, actualizado_en = CURRENT_TIMESTAMP WHERE id = ?",
                (json.dumps(residual["centroide"].tolist()), residual["n_preguntas"], residual_id),
            )

        destacadas = _refrescar_destacadas(conn, rol, textos, groq_api_key)

        conn.execute(
            "INSERT INTO temas_scope_estado (rol, ultimo_consulta_id, ultima_corrida_en, destacadas_json) "
            "VALUES (?, ?, CURRENT_TIMESTAMP, ?) "
            "ON CONFLICT(rol) DO UPDATE SET "
            "ultimo_consulta_id = excluded.ultimo_consulta_id, "
            "ultima_corrida_en = excluded.ultima_corrida_en, "
            "destacadas_json = excluded.destacadas_json",
            (rol, max_id_visto, json.dumps(destacadas)),
        )
        conn.execute("COMMIT")
        return {
            "procesadas": len(pendientes),
            "temas_nuevos": temas_nuevos,
            "reasignadas_desde_residual": reasignadas,
        }
    except Exception:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def recalcular_todo(rol: str, groq_api_key: str, db_path: str) -> dict:
    """Reemplaza por completo el estado persistido de un scope y vuelve a
    correr actualizar_scope sobre el histórico completo — permite que los
    temas se reorganicen. Es intencional y separado del flujo incremental
    normal, disparado solo cuando el docente lo pide explícitamente."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DELETE FROM tema_preguntas WHERE rol = ?", (rol,))
        conn.execute("DELETE FROM temas WHERE rol = ?", (rol,))
        conn.execute("DELETE FROM temas_scope_estado WHERE rol = ?", (rol,))
        conn.commit()
    finally:
        conn.close()
    return actualizar_scope(rol, groq_api_key, db_path)
