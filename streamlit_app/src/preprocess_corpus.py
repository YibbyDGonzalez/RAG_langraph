import re
import pdfplumber
import pandas as pd
from pathlib import Path

# ========================================
# CONFIG
# ========================================
DATA_RAW = Path("data/raw")
DATA_PROCESSED = Path("data/processed")
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 100          # tamaño aproximado de chunk (en tokens aprox)
CHUNK_OVERLAP = 0.2       # 20% de solapamiento
MIN_CHARS = 50           # longitud mínima para aceptar un chunk

# Referencia bibliográfica completa por PDF fuente, para citar en las
# respuestas del Asistente MBE. Curada a mano (solo 2 libros) en vez de
# parsear metadata del PDF, que es poco confiable (uno de los dos no trae
# título/autor embebido).
BIBLIOGRAFIA = {
    "Painless Evidence-Based Medicine.pdf":
        "Dans AL et al. Painless Evidence-Based Medicine, 2017",
    "Users Guides to the medical literature_A Manual for Evidence Based cience.pdf":
        "Guyatt G et al. Users' Guides to the Medical Literature, 2015",
}

# El PDF de "Painless Evidence-Based Medicine.pdf" tal como esta en data/raw/
# trae, por un error operativo al generarlo, una copia completa del libro de
# Guyatt ("Users Guides...") pegada a partir de la pagina 168 (el libro real
# de Dans termina en su indice, paginas 166-167). Sin este limite, esas
# paginas se indexaban dos veces bajo la referencia bibliografica equivocada
# (citadas como "Dans... Painless EBM" cuando en realidad son de Guyatt).
PAGINA_LIMITE = {
    "Painless Evidence-Based Medicine.pdf": 167,
}


# ========================================
# 1. EXTRAER TEXTO DE PDF
# ========================================
def extract_pages(pdf_path: Path) -> list[str]:
    """Texto por página (índice 0 = página 1), en vez de un solo string
    concatenado — así cada chunk puede quedar atado a la página de la que
    salió, para poder citarla."""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for p in pdf.pages:
            txt = p.extract_text() or ""
            pages.append(txt)
            # sin esto, pdfplumber acumula en memoria los objetos parseados
            # (chars/rects/curvas) de cada página ya procesada — en libros de
            # +1000 páginas eso agota la RAM disponible (visto: proceso matado
            # con OOM en un sandbox de 3.7GB)
            p.close()
    return pages


# ========================================
# 2. NORMALIZACIÓN DE TEXTO
# ========================================
def clean_text(text: str) -> str:
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text.strip()


# ========================================
# 3. CHUNKING UNIVERSAL POR VENTANA
# ========================================
def chunk_by_window(text: str, pagina: int,
                    chunk_size: int = CHUNK_SIZE,
                    overlap_ratio: float = CHUNK_OVERLAP) -> pd.DataFrame:
    """Chunking por ventana de palabras, acotado a una sola página: cada
    chunk queda con una página de origen inequívoca (`pagina`), necesaria
    para poder citarla en las respuestas."""

    words = text.split()
    total_words = len(words)

    step = int(chunk_size * (1 - overlap_ratio))

    chunks = []
    start = 0

    while start < total_words:
        end = min(start + chunk_size, total_words)
        chunk_words = words[start:end]
        chunk = " ".join(chunk_words).strip()

        # evitar chunks muy pequeños
        if len(chunk) > MIN_CHARS:
            chunks.append(chunk)

        start += step

    df = pd.DataFrame({
        "texto": chunks,
        "tipo": ["ventana"] * len(chunks),
        "pagina": [pagina] * len(chunks),
    })

    return df


# ========================================
# 4. MAIN LOOP
# ========================================
def main():
    all_rows = []

    for pdf_path in sorted(DATA_RAW.glob("*.pdf")):
        print(f"Procesando: {pdf_path.name}")
        paginas_raw = extract_pages(pdf_path)
        limite = PAGINA_LIMITE.get(pdf_path.name)
        if limite is not None:
            print(f"   ↳ limitado a las primeras {limite} paginas ({len(paginas_raw)} totales en el PDF)")
            paginas_raw = paginas_raw[:limite]

        chunks_doc = []
        for num_pagina, texto_pagina in enumerate(paginas_raw, start=1):
            texto_limpio = clean_text(texto_pagina)
            if not texto_limpio:
                continue
            chunks_doc.append(chunk_by_window(texto_limpio, pagina=num_pagina))

        if not chunks_doc:
            continue

        df = pd.concat(chunks_doc, ignore_index=True)
        df["fuente_pdf"] = pdf_path.name
        referencia = BIBLIOGRAFIA.get(pdf_path.name)
        if referencia is None:
            print(f"⚠️  Sin referencia bibliográfica para {pdf_path.name!r} — agrégala a BIBLIOGRAFIA")
            referencia = pdf_path.stem
        df["referencia"] = referencia
        all_rows.append(df)

    final_df = pd.concat(all_rows, ignore_index=True)
    final_df.insert(0, "chunk_id", range(len(final_df)))
    # pd.concat sube "pagina" a float64 si algún grupo concatenado quedó
    # vacío (dtype object/float por defecto en una lista vacía) — sin este
    # cast, las citas mostrarían "pág. 45.0" en vez de "pág. 45".
    final_df["pagina"] = final_df["pagina"].astype(int)
    final_df.to_csv(DATA_PROCESSED / "articulos_total.csv", index=False)

    print("=====================================")
    print(f"✔ Total chunks generados: {len(final_df)}")
    print("✔ Guardado en data/processed/articulos_total.csv")
    print("=====================================")


if __name__ == "__main__":
    main()
