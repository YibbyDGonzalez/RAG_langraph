# Asistente MBE — Medicina Basada en la Evidencia
### Pontificia Universidad Javeriana · Facultad de Medicina

Sistema conversacional de **Recuperación Aumentada con Generación (RAG)** especializado en Medicina Basada en la Evidencia, diseñado para que estudiantes y profesionales de la salud puedan consultar artículos científicos en lenguaje natural y recibir respuestas fundamentadas, precisas y sin alucinaciones.

> **Autores:** Yibby González · Juan Ruiz  
> **Profesores:** Juan Pablo Pájaro · Fabián Gil

---

## Índice

1. [Descripción general](#1-descripción-general)
2. [Arquitectura del sistema](#2-arquitectura-del-sistema)
3. [Componentes en detalle](#3-componentes-en-detalle)
4. [Flujo completo de una consulta](#4-flujo-completo-de-una-consulta)
5. [Preprocesamiento del corpus (offline)](#5-preprocesamiento-del-corpus-offline)
6. [Estructura del repositorio](#6-estructura-del-repositorio)
7. [Instalación y puesta en marcha](#7-instalación-y-puesta-en-marcha)
8. [Variables de entorno](#8-variables-de-entorno)
9. [Observabilidad y logs](#9-observabilidad-y-logs)
10. [Stack tecnológico](#10-stack-tecnológico)

---

## 1. Descripción general

El **Asistente MBE** es una aplicación web que permite realizar preguntas clínicas en lenguaje natural sobre un corpus de artículos de Medicina Basada en la Evidencia. El sistema recupera los fragmentos más relevantes del corpus mediante búsqueda semántica y genera una respuesta contextualizada usando un modelo de lenguaje (LLM), garantizando que la respuesta provenga **únicamente** del material científico disponible, sin inventar información.

### Características principales

- **Búsqueda semántica** sobre corpus de artículos MBE usando FAISS y embeddings multilingües.
- **Generación fundamentada** con LLaMA 3.1 (8B) vía Groq API, con temperature baja (0.2) para maximizar precisión.
- **Streaming de tokens** en tiempo real: el usuario ve la respuesta mientras se genera.
- **Interfaz multi-conversación** con historial persistido por sesión.
- **Autenticación por usuario** con cookies de sesión.
- **Observabilidad completa**: cada consulta registra pregunta, artículos recuperados, scores de similitud y latencias por etapa.
- **Despliegue containerizado** con Docker.

---

## 2. Arquitectura del sistema

El sistema se organiza en seis capas funcionales:

```
┌─────────────────────────────────────────────────────────────┐
│                    Usuario / Navegador                       │
└──────────────────────────┬──────────────────────────────────┘
                           │ consulta clínica
┌──────────────────────────▼──────────────────────────────────┐
│              Interfaz Web — Streamlit (app/app.py)           │
│   Chat · Historial multi-sesión · Sidebar · Autenticación   │
└────────────┬────────────────────────────────────────────────┘
             │ query string
┌────────────▼────────────────────────────────────────────────┐
│         Pipeline RAG — LangGraph (rag_langgraph/)           │
│                                                              │
│   ┌──────────────────┐       ┌──────────────────────────┐   │
│   │  Nodo: retrieve  │──────▶│    Nodo: generate        │   │
│   │  SentenceTransf. │context│    Prompt + LLM (Groq)   │   │
│   │  + FAISS top-3   │       │    Streaming de tokens   │   │
│   └────────┬─────────┘       └────────────┬─────────────┘   │
└────────────│────────────────────────────── │ ───────────────┘
             │                               │
┌────────────▼──────────┐   ┌───────────────▼─────────────────┐
│   Capa de Datos        │   │   Groq API (externo)            │
│   FAISS · Embeddings   │   │   llama-3.1-8b-instant          │
│   CSV artículos MBE    │   │   streaming SSE                 │
└────────────────────────┘   └─────────────────────────────────┘
             │ metadata + respuesta completa
┌────────────▼────────────────────────────────────────────────┐
│        Logger SQLite (app/logger.py · mbe_logs.db)          │
│   usuario · chunks · scores · latencias por etapa           │
└─────────────────────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────────┐
│          Infraestructura Docker (docker-compose.yml)         │
│   Volúmenes: data (ro) · logs (rw) · users.yaml (ro)        │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Componentes en detalle

### 3.1 Interfaz web — `app/app.py`

La capa de presentación está construida con **Streamlit** y es el único punto de contacto del usuario con el sistema.

**Responsabilidades:**
- Renderizar el chat y el historial de mensajes de la sesión activa.
- Gestionar múltiples conversaciones simultáneas a través de `st.session_state`, identificadas por un UUID único.
- Cargar todos los recursos pesados (modelos, índice FAISS, cliente Groq) **una única vez** al arrancar, usando `@st.cache_resource`, para no repetir la carga en cada interacción.
- Invocar el pipeline RAG en modo streaming y mostrar los tokens conforme llegan, con cursor de escritura en tiempo real.
- Recibir el primer `yield` del pipeline (metadatos de latencias y chunks), y el resto de `yield`s como tokens de texto.
- Guardar el log de cada consulta en SQLite una vez recibida la respuesta completa.
- Ofrecer la descarga directa del archivo de logs (`.db`) desde el sidebar.

**Autenticación:**  
Antes de mostrar cualquier elemento de la aplicación, el módulo `streamlit-authenticator` valida las credenciales contra `users.yaml`. Las contraseñas están almacenadas como hashes Bcrypt. La sesión se mantiene mediante una cookie con tiempo de expiración configurable.

---

### 3.2 Pipeline RAG — `rag_langgraph/app_langgraph.py`

El corazón del sistema. Orquesta la recuperación y la generación mediante un **grafo de estados con LangGraph**.

#### Modelo de estado

```python
GraphState = {
    "query":    str,   # Pregunta original del usuario
    "context":  str,   # Artículos concatenados recuperados por FAISS
    "response": str,   # Respuesta final del LLM
}
```

El grafo define `InputState = { query }` y `OutputState = { response }`, lo que permite que LangGraph valide entradas y salidas automáticamente.

#### Nodo 1: `retrieve`

1. Codifica la pregunta en un vector de 384 dimensiones usando `SentenceTransformer`.
2. Ejecuta una búsqueda de similitud coseno en el índice FAISS (`IndexFlatIP`) recuperando los **3 artículos más relevantes** (`top_k=3`).
3. Construye un bloque de contexto con los títulos y textos de los artículos recuperados.
4. Retorna `{ "context": <texto concatenado> }` al estado del grafo.

#### Nodo 2: `generate`

1. Recibe el estado con `query` y `context`.
2. Construye el prompt final: `PREGUNTA + CONTEXTO`.
3. Aplica un **system prompt estricto** que instruye al modelo a:
   - Responder únicamente con la información del contexto.
   - No inventar datos ni usar conocimiento externo.
   - Responder "No hay suficiente información..." si el contexto no es suficiente.
4. Llama a la **Groq API** con `stream=True` y hace `yield` de cada token.

#### Función `responder_stream_logged`

Variante especializada del pipeline que:
- **Aísla** el tiempo de embedding, retrieval y LLM en variables separadas.
- **Yield 1:** diccionario de metadata `{ chunks, scores, lat_embedding, lat_retrieval, llm_start }`.
- **Yields siguientes:** tokens del LLM en tiempo real.

Esta separación permite que `app.py` capture los metadatos antes de iniciar el streaming visual.

---

### 3.3 Core y utilidades — `app/core.py`

Módulo de funciones compartidas que abstraen el acceso a los recursos:

| Función | Descripción |
|---|---|
| `load_resources()` | Carga el CSV, embeddings, índice FAISS, modelo SentenceTransformer y cliente Groq. Llamada una sola vez al iniciar. |
| `buscar_articulos(query, top_k)` | Codifica la query y ejecuta la búsqueda FAISS. Retorna un DataFrame con los artículos y sus scores. |
| `call_ollama(prompt)` | Llamada síncrona a Groq (para uso sin streaming). |
| `call_ollama_stream(prompt)` | Generador que hace `yield` de tokens en tiempo real desde la API de Groq. |

**Constantes clave:**
```
EMBED_MODEL  = sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
GROQ_MODEL   = llama-3.1-8b-instant
TEMPERATURE  = 0.2
MAX_TOKENS   = 1300
```

---

### 3.4 Capa de datos — `data/processed/`

Archivos generados durante el preprocesamiento offline (ver sección 5):

| Archivo | Descripción |
|---|---|
| `articulos_total.csv` | Corpus de artículos MBE dividido en chunks. Columnas: `id_articulo`, `titulo`, `texto`, `tipo`, `fuente_pdf`. |
| `models/embeddings_total.npy` | Matriz NumPy con los vectores de cada chunk (shape: `[n_chunks, 384]`). Normalizada (L2). |
| `models/faiss_index_total.bin` | Índice FAISS (`IndexFlatIP`) serializado. Permite búsqueda por producto interno (equivale a similitud coseno sobre vectores normalizados). |

Estos archivos se montan en el contenedor Docker como **volumen de solo lectura**, por lo que no es necesario reconstruir la imagen si se actualiza el corpus.

---

### 3.5 Autenticación — `users.yaml`

Archivo de configuración de usuarios. Estructura:

```yaml
credentials:
  usernames:
    nombre_usuario:
      name: Nombre Completo
      password: <hash bcrypt>
cookie:
  name: mbe_auth
  key: <clave secreta>
  expiry_days: 30
```

Se monta como volumen de solo lectura en Docker, permitiendo agregar o modificar usuarios sin reconstruir la imagen.

---

### 3.6 Observabilidad — `app/logger.py`

Cada consulta al asistente genera un registro en **SQLite** con la siguiente información:

| Campo | Tipo | Descripción |
|---|---|---|
| `timestamp` | DATETIME | Momento de la consulta |
| `usuario` | TEXT | Username autenticado |
| `session_id` | TEXT | UUID de la conversación |
| `pregunta` | TEXT | Consulta original del usuario |
| `chunks_extraidos` | TEXT (JSON) | Lista de artículos recuperados (`id_articulo`, `titulo`) |
| `scores_similitud` | TEXT (JSON) | Scores de similitud coseno para cada chunk (4 decimales) |
| `respuesta` | TEXT | Respuesta completa generada |
| `latencia_embedding` | REAL | Tiempo de codificación de la query (segundos) |
| `latencia_retrieval` | REAL | Tiempo de búsqueda en FAISS (segundos) |
| `latencia_llm` | REAL | Tiempo total de generación del LLM (segundos) |
| `latencia_total` | REAL | Tiempo end-to-end de la consulta (segundos) |

El archivo `mbe_logs.db` vive en `data/logs/`, montado con escritura habilitada. El usuario puede descargarlo directamente desde el sidebar de la aplicación para análisis posterior.

El logger falla silenciosamente: un error al guardar el log **nunca interrumpe** la experiencia del usuario.

---

### 3.7 Infraestructura Docker — `docker-compose.yml` + `Dockerfile.app`

La aplicación se despliega como un único contenedor Docker:

```
Servicio: app
  Imagen:   mbe-app:latest
  Puerto:   8501 (Streamlit)
  
Volúmenes:
  ./data            → /app/data       (read-only)   corpus + índices
  ./data/logs       → /app/data/logs  (read-write)  base de datos de logs
  ./Javeriana.png   → /app/Javeriana.png (read-only) logo institucional
  ./users.yaml      → /app/users.yaml  (read-only)  credenciales

Secrets:
  .env  →  GROQ_API_KEY, LOGS_DB_PATH
```

Esta arquitectura permite:
- **Actualizar el corpus** sin reconstruir la imagen (reemplazar archivos en `data/processed/` y reiniciar el contenedor).
- **Agregar usuarios** sin reconstruir (editar `users.yaml` y reiniciar).
- **Consultar logs** sin entrar al contenedor (el archivo `.db` está en el host).

---

## 4. Flujo completo de una consulta

```
1. El usuario escribe una pregunta clínica en el chat.

2. Streamlit (app.py) invoca responder_stream_logged(query, ...).

3. Pipeline RAG — Nodo retrieve:
   a. SentenceTransformer codifica la query en un vector de 384 dim.
   b. FAISS busca los 3 artículos con mayor similitud coseno.
   c. Se construye el bloque de contexto con los textos recuperados.
   → yield 1: { chunks, scores, lat_embedding, lat_retrieval }

4. Pipeline RAG — Nodo generate:
   a. Se ensambla: system_prompt + PREGUNTA + CONTEXTO.
   b. Groq API recibe el prompt con stream=True.
   c. Los tokens llegan y se reenvían al frontend.
   → yield N (tokens): "Se", " define", " como", " la", ...

5. Streamlit muestra los tokens con cursor de escritura en tiempo real.

6. Al completar el stream, Streamlit llama a log_consulta() con:
   - La respuesta completa.
   - Los metadatos del yield 1 (chunks, scores, latencias).
   - La latencia LLM y total calculadas en app.py.

7. El log se inserta en SQLite (mbe_logs.db).

8. La respuesta queda guardada en el historial de la sesión activa.
```

---

## 5. Preprocesamiento del corpus (offline)

Este paso se ejecuta **una sola vez** antes de desplegar la aplicación. Convierte los PDFs del corpus MBE en el índice FAISS que usa el sistema en producción.

### Paso 1 — Extracción y chunking: `src/preprocess_corpus.py`

Lee todos los PDFs en `data/raw/` y genera `data/processed/articulos_total.csv`.

**Proceso:**
1. Extrae texto de cada página del PDF con `pdfplumber`.
2. Normaliza espacios, saltos de línea y caracteres especiales.
3. Divide el texto en **chunks por ventana deslizante**:
   - Tamaño del chunk: ~400 palabras.
   - Solapamiento: 20% (para no perder contexto en los bordes).
   - Mínimo de caracteres por chunk: 200 (descartar fragmentos muy cortos).
4. Exporta todos los chunks de todos los PDFs a un único CSV.

```bash
cd RAG_langraph
python src/preprocess_corpus.py
```

### Paso 2 — Embeddings e índice FAISS: `src/indexing.py`

Lee el CSV generado en el paso anterior y produce los archivos de vectores e índice.

**Proceso:**
1. Carga el CSV y descarta filas con texto vacío.
2. Codifica todos los chunks con `paraphrase-multilingual-MiniLM-L12-v2` (384 dimensiones, normalizado L2).
3. Construye un índice FAISS `IndexFlatIP` (producto interno = similitud coseno sobre vectores normalizados).
4. Guarda `embeddings_total.npy` y `faiss_index_total.bin` en `data/processed/models/`.

```bash
python src/indexing.py
```

**Resultado esperado:**
```
data/processed/
├── articulos_total.csv          ← corpus en chunks
└── models/
    ├── embeddings_total.npy     ← matriz de vectores
    └── faiss_index_total.bin    ← índice de búsqueda
```

> Estos archivos **no se incluyen en el repositorio** por su tamaño. Deben generarse localmente antes del primer despliegue.

---

## 6. Estructura del repositorio

```
RAG_langraph/
│
├── app/                          # Aplicación principal (runtime)
│   ├── app.py                    # Interfaz Streamlit + lógica de sesión
│   ├── core.py                   # Carga de recursos, búsqueda FAISS, cliente Groq
│   └── logger.py                 # Registro de consultas en SQLite
│
├── rag_langgraph/                # Pipeline RAG con LangGraph
│   └── app_langgraph.py          # Grafo de estados, nodos retrieve y generate
│
├── src/                          # Scripts de preprocesamiento (offline, ejecutar 1 vez)
│   ├── preprocess_corpus.py      # PDF → chunks → CSV
│   └── indexing.py               # CSV → embeddings → índice FAISS
│
├── data/
│   ├── raw/                      # PDFs originales del corpus MBE
│   ├── processed/
│   │   ├── articulos_total.csv   # Corpus en chunks (generado por preprocess)
│   │   └── models/
│   │       ├── embeddings_total.npy
│   │       └── faiss_index_total.bin
│   └── logs/
│       └── mbe_logs.db           # Base de datos de observabilidad (generada en runtime)
│
├── Dockerfile.app                # Imagen Docker de la aplicación
├── docker-compose.yml            # Orquestación del servicio
├── requirements.txt              # Dependencias Python
├── users.yaml                    # Credenciales de usuarios (no commitear en producción)
├── .env                          # Variables de entorno (no commitear)
├── Javeriana.png                 # Logo institucional
└── arquitectura_mbe.svg          # Diagrama de arquitectura del sistema
```

---

## 7. Instalación y puesta en marcha

### Requisitos previos

- Python 3.10+
- Docker y Docker Compose
- Cuenta en [Groq](https://console.groq.com/) con una API key activa

### Opción A — Docker (recomendado para producción)

**1. Clonar el repositorio**
```bash
git clone <url-del-repo>
cd RAG_langraph
```

**2. Generar el corpus y el índice** (solo la primera vez)
```bash
# Instalar dependencias necesarias para el preprocesamiento
pip install pdfplumber pandas sentence-transformers faiss-cpu numpy

# Colocar los PDFs del corpus en data/raw/
# Luego ejecutar:
python src/preprocess_corpus.py
python src/indexing.py
```

**3. Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env y agregar GROQ_API_KEY=<tu-clave>
```

**4. Configurar usuarios**

Editar `users.yaml` con las credenciales. Las contraseñas deben estar hasheadas con Bcrypt:
```python
import bcrypt
print(bcrypt.hashpw("mi_contraseña".encode(), bcrypt.gensalt()).decode())
```

**5. Levantar el servicio**
```bash
docker compose up --build
```

La aplicación estará disponible en `http://localhost:8501`.

---

### Opción B — Ejecución local (desarrollo)

```bash
# Crear entorno virtual
python -m venv env
source env/bin/activate        # Linux/Mac
# env\Scripts\activate         # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
export GROQ_API_KEY=<tu-clave>

# Ejecutar la aplicación
cd app
streamlit run app.py
```

---

## 8. Variables de entorno

| Variable | Descripción | Requerida |
|---|---|---|
| `GROQ_API_KEY` | Clave de autenticación de la API de Groq | Sí |
| `LOGS_DB_PATH` | Ruta al archivo SQLite de logs. Default: `data/logs/mbe_logs.db` | No |

---

## 9. Observabilidad y logs

El sistema registra automáticamente cada consulta en una base de datos SQLite. Esto permite analizar:

- **Calidad de la recuperación:** ¿Qué artículos se recuperan con más frecuencia? ¿Los scores son consistentemente altos?
- **Latencias por etapa:** ¿Cuánto toma el embedding vs. el retrieval vs. la generación?
- **Patrones de uso:** ¿Qué preguntas hacen los usuarios? ¿En qué sesiones?

**Cómo acceder a los logs:**

1. **Desde la UI:** sidebar → botón "Descargar logs (.db)".
2. **Directamente:** el archivo `data/logs/mbe_logs.db` está en el host (no dentro del contenedor).
3. **Con cualquier cliente SQLite:** `sqlite3`, DBeaver, DB Browser for SQLite, etc.

```sql
-- Ejemplo: consultas por usuario con latencia promedio
SELECT usuario,
       COUNT(*)                        AS total_consultas,
       ROUND(AVG(latencia_total), 2)   AS latencia_promedio_s,
       ROUND(AVG(latencia_llm), 2)     AS latencia_llm_s
FROM consultas
GROUP BY usuario
ORDER BY total_consultas DESC;
```

---

## 10. Stack tecnológico

| Componente | Tecnología | Versión |
|---|---|---|
| Interfaz web | Streamlit | latest |
| Autenticación | streamlit-authenticator | 0.2.3 |
| Orquestación RAG | LangGraph | ≥ 0.1.0 |
| Embeddings | sentence-transformers / paraphrase-multilingual-MiniLM-L12-v2 | 2.7.0 |
| Índice vectorial | FAISS (CPU) | ≥ 1.9.0 |
| Modelo de lenguaje | LLaMA 3.1-8b-instant vía Groq API | — |
| Cliente LLM | groq (Python SDK) | latest |
| Base de datos de logs | SQLite | (stdlib) |
| Procesamiento de PDFs | pdfplumber | latest |
| Datos tabulares | pandas | ≥ 2.0.0 |
| Contenedores | Docker + Docker Compose | — |
| Lenguaje | Python | 3.10+ |
