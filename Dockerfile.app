FROM python:3.11-slim

WORKDIR /app

# System deps necesarios para faiss, sentence-transformers y pdfplumber
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# --- CAPA 1: torch por separado (~700 MB) ---
# Capa independiente para que Docker la cachee aunque cambien
# otras dependencias en requirements.txt
RUN pip install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    torch==2.6.0+cpu

# --- CAPA 2: resto de dependencias Python ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- CAPA 3: modelo de embeddings bakeado en la imagen (~500 MB) ---
# Ruta fija para estabilizar el layer cache de Docker
ENV SENTENCE_TRANSFORMERS_HOME=/app/models

# PYTHONPATH=/app garantiza que Python resuelva 'app' como el paquete /app/app/
# y no como el modulo /app/app/app.py (conflicto de nombre)
ENV PYTHONPATH=/app

RUN python -c "\
from sentence_transformers import SentenceTransformer; \
model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'); \
print('Modelo de embeddings descargado correctamente.')"

# --- CAPA 4: codigo de la aplicacion (cambia frecuentemente, va al final) ---
# data/ se monta como volumen en runtime, no se copia aqui
COPY app/ ./app/
COPY rag_langgraph/ ./rag_langgraph/
COPY src/ ./src/

EXPOSE 8501

CMD ["streamlit", "run", "app/app.py", \
     "--server.address=0.0.0.0", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false"]
