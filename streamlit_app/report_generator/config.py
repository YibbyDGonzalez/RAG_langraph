import os

# Ruta por defecto a la base de datos SQLite
DB_PATH_DEFAULT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "logs", "mbe_logs.db"
)

# Modelo de embeddings multilingüe (corre localmente, sin costo)
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# UMAP: dimensiones para la etapa de clustering
UMAP_N_COMPONENTS = 10

# HDBSCAN: tamaño mínimo de cluster y muestras mínimas
HDBSCAN_MIN_CLUSTER_SIZE = 3
HDBSCAN_MIN_SAMPLES = 2

# Número máximo de preguntas de ejemplo mostradas por tema en la tabla
MAX_EJEMPLOS_POR_TEMA = 3

# Modelo de Groq usado para nombrar cada grupo temático
GROQ_MODEL = "llama-3.1-8b-instant"

# Offset de zona horaria aplicado al timestamp leído de la DB.
# SQLite CURRENT_TIMESTAMP guarda siempre en UTC.
# - Si el servidor/contenedor corría en UTC-5 (Colombia), los timestamps
#   ya están en hora local → pon 0.
# - Si quieres convertir de UTC a Colombia (UTC-5) → pon -5.
TIMEZONE_OFFSET_HOURS = 0

# Ruta al archivo de credenciales, usado como "roster" de estudiantes
# matriculados (no existe un roster académico separado hoy).
USERS_YAML_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "users.yaml"
)

# Número máximo de preguntas destacadas mostradas en el Nivel 2 (Temas)
MAX_PREGUNTAS_DESTACADAS = 3

# Días de inactividad para considerar a un estudiante "silencioso" (Nivel 1 y 3)
SILENCIO_DIAS = 14

# Umbrales para detectar "temas con retrieval débil" (Nivel 2):
# un tema entra en la alerta si tiene al menos RETRIEVAL_DEBIL_MIN_PREGUNTAS
# preguntas Y su score de similitud representativo promedio es
# <= RETRIEVAL_DEBIL_UMBRAL_SCORE (score de coseno entre pregunta y chunk,
# rango aproximado 0-1; ajustar tras calibrar con datos reales de un semestre).
RETRIEVAL_DEBIL_MIN_PREGUNTAS = 3
RETRIEVAL_DEBIL_UMBRAL_SCORE = 0.4
