# Construir desde la raíz del repo (contexto = .), porque el backend
# importa directamente el código de streamlit_app/ sin reimplementarlo.
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# --- CAPA 1: torch por separado (~200 MB en CPU) ---
# Capa independiente para que Docker la cachee aunque cambien las
# demás dependencias.
RUN pip install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    torch==2.6.0+cpu

# --- CAPA 2: dependencias (streamlit_app/requirements.txt + backend/requirements.txt) ---
COPY streamlit_app/requirements.txt streamlit_app/requirements.txt
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# --- CAPA 3: modelo de embeddings bakeado en la imagen ---
ENV SENTENCE_TRANSFORMERS_HOME=/app/models
RUN python -c "\
from sentence_transformers import SentenceTransformer; \
SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'); \
print('Modelo de embeddings descargado correctamente.')"

# --- CAPA 4: código (cambia frecuentemente, va al final) ---
# streamlit_app/data/ NO se copia: se monta como volumen en runtime
# (index FAISS + CSV de solo lectura, logs de lectura/escritura).
COPY backend/ backend/
COPY streamlit_app/app streamlit_app/app
COPY streamlit_app/rag_langgraph streamlit_app/rag_langgraph
COPY streamlit_app/report_generator streamlit_app/report_generator
COPY streamlit_app/src streamlit_app/src

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
