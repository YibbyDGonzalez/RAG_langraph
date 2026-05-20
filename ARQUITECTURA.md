# Arquitectura del Agente MBE
### Asistente conversacional RAG para Medicina Basada en la Evidencia
**Pontificia Universidad Javeriana · Facultad de Medicina**

> **Autores:** Yibby González · Juan Ruiz
> **Profesores:** Juan Pajaro · Fabian Armando

---

## Marco metodológico

La arquitectura de este sistema se documenta siguiendo el método **Views & Beyond (V&B)** propuesto por Clements et al., el mismo enfoque utilizado por Tummers et al. (2021) para diseñar arquitecturas de referencia en sistemas de información en salud.

Este método establece que un sistema complejo no puede describirse desde un único ángulo. Por eso se definen **cuatro vistas complementarias**, cada una respondiendo una pregunta distinta:

| Vista | Pregunta que responde |
|---|---|
| Diagrama de Contexto | ¿Con quién interactúa el sistema? |
| Descomposición | ¿De qué está hecho internamente? |
| Capas | ¿Cómo se organizan los módulos y quién puede usar a quién? |
| Despliegue | ¿Dónde corre físicamente cada parte? |

Antes de presentar las vistas, se identifican los **stakeholders** del sistema y sus preocupaciones, ya que son ellos quienes justifican cada decisión arquitectónica.

---

## Stakeholders y sus preocupaciones

| Stakeholder | Preocupación principal |
|---|---|
| **Estudiante / Profesional de salud** | Obtener respuestas clínicas fundamentadas, sin alucinaciones |
| **Profesor / Tutor** | Auditar la calidad de las respuestas y el corpus utilizado |
| **Administrador del sistema** | Actualizar el corpus y usuarios sin reconstruir la imagen Docker |
| **Desarrollador** | Extender el sistema con nuevos módulos o fuentes de datos |

Estas preocupaciones se ven reflejadas directamente en decisiones como: el system prompt estricto (no inventar información), el volumen Docker de solo lectura para el corpus, el logger con scores de similitud, y la separación entre preprocesamiento offline y ejecución en producción.

---

## Vista 1: Diagrama de Contexto

> *¿Con quién interactúa el sistema?*

Esta vista muestra el sistema como una caja negra y describe todas las entidades externas que se comunican con él. Permite entender el alcance del sistema sin entrar en su implementación interna.

```
                         ┌──────────────────────────────────┐
                         │                                  │
   [Usuario]    ────────▶│                                  │────────▶  [Groq API]
   consulta     ◀────────│          AGENTE MBE              │◀────────  tokens SSE
                         │                                  │
                         │      (Sistema RAG conversacional)│
                         │                                  │
                         │                                  │
  [Administrador]   ◀────│                                  │
   logs · métricas       │                                  │
   corpus · users        └──────────────────────────────────┘

   ──────▶  Comunicación obligatoria
   - - - ▶  Comunicación opcional
```

| Entidad | Tipo | Descripción |
|---|---|---|
| **Usuario** | Obligatoria | Hace consultas clínicas en lenguaje natural y recibe respuestas fundamentadas en el corpus |
| **Groq API** | Obligatoria | Servicio externo que ejecuta LLaMA 3.1-8b y retorna tokens en streaming (SSE) |
| **Administrador** | Opcional | Actualiza el corpus de artículos y gestiona credenciales de acceso |
| **Profesor / Auditor** | Opcional | Descarga y analiza los logs de consultas para evaluar calidad del sistema |

---

## Vista 2: Descomposición

> *¿De qué está hecho el sistema internamente?*

Esta vista descompone el sistema en módulos y submódulos, mostrando sus relaciones internas. Es la vista más importante para entender la estructura del sistema y guiar su desarrollo.

```
┌──────────────────────────────────────────────────────────────────┐
│                           AGENTE MBE                             │
│                                                                  │
│  ┌───────────────────┐      ┌───────────────────────────────┐    │
│  │   Interfaz UI     │      │       Pipeline RAG            │    │
│  │                   │      │                               │    │
│  │  · Chat           │      │  ┌───────────────────────── ┐ │    │
│  │  · Multi-sesión   │      │  │     Nodo Retrieve        │ │    │
│  │  · Autenticación  │      │  │  · Embedding de query    │ │    │
│  │  · Descarga logs  │      │  │  · Búsqueda FAISS top3   │ │    │
│  └───────────────────┘      │  │  · Construcción contexto │ │    │
│                             │  └──────────────────────────┘ │    │
│                             │  ┌────────────────────────┐   │    │
│                             │  │     Nodo Generate      │   │    │
│                             │  │  · Ensamblado prompt   │   │    │
│                             │  │  · Llamada Groq API    │   │    │
│                             │  │  · Streaming tokens    │   │    │
│                             │  └────────────────────────┘   │    │
│                             └───────────────────────────────┘    │
│                                                                  │
│  ┌───────────────────┐      ┌───────────────┐  ┌──────────────┐  │
│  │     Seguridad     │      │  Capa Datos   │  │Observabilidad│  │
│  │                   │      │               │  │              │  │
│  │  · Bcrypt/cookies │      │  · FAISS idx  │  │  · Logger    │  │
│  │  · Sesión usuario │      │  · Embeddings │  │  · SQLite    │  │
│  │  · API Key (env)  │      │  · CSV corpus │  │  · Latencias │  │
│  └───────────────────┘      └───────────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

| Módulo | Descripción |
|---|---|
| **Interfaz UI** | Único punto de contacto con el usuario; gestiona chat, sesiones y autenticación |
| **Nodo Retrieve** | Convierte la pregunta en vector (384 dim.) y recupera los 3 chunks más similares del corpus |
| **Nodo Generate** | Ensambla el prompt con el contexto recuperado y llama a Groq en modo streaming |
| **Seguridad** | Controla acceso por usuario (Bcrypt) y protege credenciales mediante variables de entorno |
| **Capa Datos** | Almacena el corpus preprocesado, los embeddings y el índice FAISS |
| **Observabilidad** | Registra cada consulta con los chunks recuperados, scores de similitud y latencias por etapa |

---

## Vista 3: Vista en Capas

> *¿Cómo se organizan los módulos y quién puede usar a quién?*

Esta vista organiza los módulos en capas con una relación unidireccional de uso (*allowed to use*): una capa solo puede usar los servicios de la capa inmediatamente inferior. Esto garantiza bajo acoplamiento y facilita el mantenimiento.

```
┌──────────────────────────────────────────────┐   ┌─────────────┐
│             CAPA DE PRESENTACIÓN             │   │             │
│                                              │◀─▶│  Seguridad  │
│      Streamlit UI  ·  Sesiones  ·  Auth      │   │             │
└────────────────────┬─────────────────────────┘   │ · Bcrypt    │
                     │  allowed to use             │ · Cookies   │
┌────────────────────▼─────────────────────────┐   │ · API Keys  │
│             CAPA DE LÓGICA (RAG)             │   │             │
│                                              │◀─▶│ (atraviesa  │
│   LangGraph  ·  Nodo Retrieve  ·  Generate   │   │  todas las  │
└────────────────────┬─────────────────────────┘   │   capas)    │
                     │  allowed to use             │             │
┌────────────────────▼─────────────────────────┐   │             │
│             CAPA DE DATOS                    │   │             │
│                                              │◀─▶│             │
│   FAISS  ·  Embeddings  ·  CSV  ·  SQLite    │   │             │
└──────────────────────────────────────────────┘   └─────────────┘
```

| Capa | Descripción |
|---|---|
| **Presentación** | Renderiza el chat y gestiona la experiencia del usuario; no accede directamente a datos |
| **Lógica RAG** | Orquesta la recuperación y generación; es el núcleo de negocio del sistema |
| **Datos** | Sirve vectores, chunks y registros de log; no conoce la lógica de negocio |
| **Seguridad** *(vertical)* | Aplica autenticación y autorización de forma transversal en todas las capas |

---

## Vista 4: Vista de Despliegue

> *¿Dónde corre físicamente cada parte del sistema?*

Esta vista muestra cómo los módulos de software se distribuyen sobre la infraestructura física y de red. Es especialmente útil para entender la disponibilidad, el rendimiento y los límites de seguridad del sistema.

```
┌──────────────┐          ┌────────────────────────────────────┐          ┌─────────────────┐
│    CLIENTE   │          │         SERVIDOR (Docker)          │          │   NUBE (Groq)   │
│              │          │                                    │          │                 │
│  Navegador   │◀────────▶│  Streamlit App  [:8501]            │─────────▶│  LLaMA 3.1-8b   │
│  Web         │   HTTP/  │  LangGraph Pipeline                │  HTTPS   │  REST + SSE     │
│              │          │  SentenceTransformer (en memoria)  │  stream  │                 │
│              │          │  Cliente Groq                      │          │                 │
│              │          │                                    │          │                 │
└──────────────┘          │  Volúmenes:                        │          └─────────────────┘
                          │  ├── /data/processed  (ro) ─────── │ corpus + índice FAISS
                          │  ├── /data/logs       (rw) ────────│ mbe_logs.db
                          │  ├── users.yaml       (ro) ────────│ credenciales
                          │  └── .env             (secret) ────│ GROQ_API_KEY
                          └────────────────────────────────────┘
```

| Nodo | Descripción |
|---|---|
| **Cliente (Navegador)** | Solo renderiza la interfaz; toda la lógica reside en el servidor |
| **Servidor Docker** | Contiene la aplicación completa: UI, pipeline RAG, modelos y acceso a datos |
| **Groq API (Nube)** | Ejecuta el LLM externamente; responde en streaming SSE sobre HTTPS |
| **Volúmenes** | Separan datos y configuración del contenedor, permitiendo actualizaciones sin reconstruir la imagen |

---

## Hilo conductor: de la pregunta a la respuesta

Las cuatro vistas describen el mismo sistema desde ángulos distintos. El siguiente flujo muestra cómo se articulan en una consulta real:

```
1. [Contexto]     El Usuario envía una pregunta clínica al Agente MBE.

2. [Capas]        La Capa de Presentación recibe la consulta
                  y la delega a la Capa de Lógica.

3. [Descomposición] El Nodo Retrieve codifica la pregunta,
                    busca en FAISS y construye el contexto.
                    El Nodo Generate ensambla el prompt
                    y llama a Groq en streaming.

4. [Despliegue]   La llamada viaja desde el contenedor Docker
                  hacia la Groq API en la nube.
                  Los tokens regresan en streaming SSE
                  y se muestran en tiempo real al usuario.

5. [Descomposición] El módulo de Observabilidad registra
                    la consulta completa en SQLite.

6. [Contexto]     El Profesor puede descargar los logs
                  para auditar la calidad del sistema.
```

---

## Referencias metodológicas

- Clements, P. et al. *Documenting Software Architectures: Views and Beyond*. 2nd Ed. Addison-Wesley, 2010.
- Tummers, J. et al. *Designing a reference architecture for health information systems*. BMC Medical Informatics and Decision Making, 21(210), 2021.
