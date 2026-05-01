FROM python:3.11-slim

WORKDIR /app

# System deps needed by faiss, sentence-transformers and pdfplumber
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (CPU-only torch kept lean)
COPY requirements.txt .
RUN pip install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt

# Bake the embedding model into the image so it runs 100% offline
RUN python -c "\
from sentence_transformers import SentenceTransformer; \
SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"

# Copy application code (data/ is volume-mounted at runtime, not copied here)
COPY app/ ./app/
COPY rag_langgraph/ ./rag_langgraph/
COPY src/ ./src/

EXPOSE 8501

CMD ["streamlit", "run", "app/app.py", \
     "--server.address=0.0.0.0", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false"]
