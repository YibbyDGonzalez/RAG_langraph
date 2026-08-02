# Plan de migración — Streamlit → Next.js + FastAPI

> Ejecutado por fases con checkpoints funcionales. Cada fase termina con
> algo verificable. Se puede volver a `groq-deploy` en cualquier momento.

---

## Preparación (antes de tocar código)

### 0.1 — Rama de trabajo

```bash
git checkout groq-deploy
git pull
git checkout -b migration-nextjs-fastapi
git push -u origin migration-nextjs-fastapi
```

Todo el trabajo va en esta rama. `groq-deploy` no se toca.

### 0.2 — Estructura del monorepo objetivo

```
RAG_langraph/
├── streamlit_app/         ← el actual, INTACTO
├── backend/               ← nuevo, FastAPI
├── frontend/              ← nuevo, Next.js
├── mockups/               ← los HTMLs de Claude Design
├── docs/                  ← los inventarios y visiones
├── docker-compose.yml     ← se irá ampliando por fase
└── ...
```

### 0.3 — Copiar los mockups al repo

Los HTMLs exportados de Claude Design van a `'# Reporte docente medicina basada en evidencia'`. Son la referencia
visual que Claude Code va a traducir a React.

---

## Fase 1 — Backend FastAPI (extraer la lógica RAG)

**Objetivo:** que la lógica actual del RAG viva en una API HTTP, sin tocar
Streamlit todavía. Streamlit sigue funcionando aparte.

**Prompt para Claude Code:**

> Estoy en la rama `migration-nextjs-fastapi`. Voy a migrar el proyecto de
> Streamlit a Next.js + FastAPI en fases. El Streamlit actual en la carpeta
> `streamlit_app/` NO se toca; sigue funcional en paralelo.
>
> **Fase 1: extraer la lógica RAG a un backend FastAPI en `backend/`.**
>
> Requisitos:
> - Reutilizar la lógica existente de LangGraph + FAISS + Groq. No
>   reimplementar; importar o refactorizar desde `streamlit_app/`.
> - Endpoints REST que reproduzcan lo que hoy hace Streamlit:
>   - `POST /api/chat` — envía una pregunta y recibe una respuesta (con
>     streaming vía Server-Sent Events).
>   - `GET /api/conversations` — lista de conversaciones del usuario.
>   - `GET /api/conversations/{id}` — detalle de una conversación.
>   - `POST /api/conversations` — crear una conversación nueva.
> - Sin autenticación todavía (Fase 2). Por ahora usa un header
>   `X-User-Id` con el user_id para simular sesión.
> - La misma BD SQLite existente. No migrar esquema.
> - Estructura FastAPI limpia: `main.py`, `routers/`, `services/`,
>   `models/`.
> - `requirements.txt` propio del backend.
> - Que corra con `uvicorn backend.main:app --reload` y responda en
>   `localhost:8000`.
>
> Antes de escribir código:
> 1. Muéstrame la estructura de carpetas propuesta.
> 2. Muéstrame el mapa de qué función de Streamlit se convierte en qué
>    endpoint.
> 3. Muéstrame el diseño de los endpoints (paths, payloads, respuestas).
>
> No implementes hasta que apruebe el plan.

**Checkpoint funcional:**
- El backend arranca sin errores.
- Puedes hacer `curl` a `/api/chat` con una pregunta y recibir respuesta
  streaming.
- El Streamlit original sigue funcionando en paralelo.
- Commit + push. Si algo sale mal, vuelves al commit anterior.

---

## Fase 2 — Autenticación real (JWT)

**Objetivo:** que el backend valide usuarios contra la BD y emita JWTs.

**Prompt para Claude Code:**

> Fase 2: agregar autenticación JWT al backend FastAPI de la Fase 1.
>
> Requisitos:
> - `POST /api/auth/login` — recibe usuario y contraseña, valida contra
>   la BD SQLite existente (la misma tabla de usuarios que usa
>   Streamlit), devuelve un JWT.
> - Middleware que valide el JWT en todos los endpoints excepto login.
> - El JWT debe incluir `user_id` y `role` (estudiante o docente).
> - Endpoints protegidos por rol donde aplique (el reporte docente solo
>   accesible con `role=docente`).
> - Duración del token: 24h (coherente con la sesión actual de Streamlit).
> - Reemplazar el header `X-User-Id` de la Fase 1 por el JWT.
>
> Antes de escribir código, muéstrame:
> 1. Cómo vas a validar contraseñas (¿hasheadas ya en la BD?
>    ¿bcrypt?).
> 2. El diseño del middleware.
> 3. Qué endpoints quedan protegidos por qué rol.

**Checkpoint funcional:**
- `curl POST /api/auth/login` devuelve un JWT.
- `curl` a endpoints protegidos falla sin token, funciona con token.
- Un estudiante no puede acceder a endpoints del reporte docente.
- Commit + push.

---

## Fase 3 — Frontend Next.js (setup + chat)

**Objetivo:** Next.js corriendo, con login y chat funcionales, conectados
al backend.

**Prompt para Claude Code:**

> Fase 3: crear el frontend Next.js en `frontend/`.
>
> Requisitos:
> - Next.js 14+ con App Router, TypeScript, Tailwind CSS.
> - Traducir los mockups de `mockups/login.html` y
>   `mockups/chat_bienvenida.html` a componentes React reales.
> - Manejo de auth con JWT: al hacer login exitoso, guardar el token
>   (httpOnly cookie preferible) y redirigir al chat.
> - Chat funcional consumiendo `/api/chat` con streaming (Server-Sent
>   Events).
> - Sidebar de historial consumiendo `/api/conversations`.
> - Estados de bienvenida y conversación activa según los mockups.
> - Variables de entorno: `NEXT_PUBLIC_API_URL=http://localhost:8000`.
> - Que corra con `npm run dev` en `localhost:3000`.
>
> Antes de escribir código, muéstrame:
> 1. La estructura de carpetas del frontend (páginas, componentes,
>    hooks, servicios de API).
> 2. Los componentes reutilizables que vas a extraer (Sidebar,
>    ChatMessage, Input, etc.).
> 3. Cómo vas a manejar el streaming de respuesta en React.

**Checkpoint funcional:**
- Puedes hacer login desde `localhost:3000` y llegar al chat.
- Preguntas y respuestas fluyen correctamente con streaming.
- El historial se ve y navega.
- Coherencia visual con los mockups de Design.
- Commit + push.

---

## Fase 4 — Reporte docente (los 4 niveles)

**Objetivo:** trasladar el reporte docente a Next.js.

Se hace en subfases para no meterse en una pantalla gigante:

**4a.** Endpoints del reporte en el backend (KPIs, temas, estudiantes,
individual). Cada uno con datos calculados de la BD.

**4b.** Nivel 1 (Pulso) en Next.js, con los 6 KPIs, gráficos y alertas.

**4c.** Nivel 2 (Temas) en Next.js, incluyendo el análisis bajo demanda.

**4d.** Nivel 3 (Estudiantes) en Next.js.

**4e.** Nivel 4 (Individual) en Next.js.

**Prompt para Claude Code (por cada subfase):**

> Fase 4X: implementar el Nivel N del reporte docente. Backend + Frontend.
>
> Referencia funcional: `docs/inventario_reporte.md` (sección "Nivel N").
> Referencia visual: `docs/vision_reporte.md` y `mockups/reporte_nivelN.html`.
>
> Backend: endpoints necesarios para servir los datos de este nivel.
> Frontend: componentes React que consumen esos endpoints, respetando
> los mockups.
>
> Muéstrame el plan antes de implementar.

**Checkpoint por subfase:** el nivel implementado se ve y navega
correctamente en Next.js. Commit + push tras cada subfase para poder
volver atrás si una rompe.

---

## Fase 5 — Docker Compose

**Objetivo:** orquestar backend + frontend + Caddy en contenedores para
poder desplegar.

**Prompt para Claude Code:**

> Fase 5: actualizar `docker-compose.yml` para orquestar la nueva
> arquitectura.
>
> Servicios:
> - `backend`: FastAPI (build desde `backend/`).
> - `frontend`: Next.js en modo producción (build + `npm start`).
> - `caddy`: reverse proxy sirviendo `frontend` en `/` y `backend`
>   en `/api`.
> - Volumen compartido para la BD SQLite.
>
> El `streamlit_app` NO va en este compose (se puede dejar como
> archivo comentado por si se quiere revivir).
>
> Que arranque con `docker compose up -d --build` y sirva todo en el
> puerto 80/443.
>
> Muéstrame el archivo antes de aplicarlo.

**Checkpoint funcional:** `docker compose up` levanta todo,
`localhost` sirve el frontend, `localhost/api/...` sirve el backend.

---

## Fase 6 — Despliegue en Hetzner

**Antes de desplegar, backup del VPS actual:**

```bash
ssh usuario@hetzner
cd ~/RAG_langraph
docker compose down
tar czf backup_streamlit_$(date +%Y%m%d).tar.gz .
# guardar ese tar.gz fuera del VPS si es posible
```

**Despliegue:**

```bash
git checkout migration-nextjs-fastapi
git pull
docker compose up -d --build
docker compose logs -f
```

**Checkpoint final:** la URL pública sirve el nuevo frontend, todo
funciona.

---

## Rollback (si algo sale mal en producción)

```bash
ssh usuario@hetzner
cd ~/RAG_langraph
git checkout groq-deploy
docker compose down
docker compose up -d --build
```

Vuelves al Streamlit funcionando en minutos.

---

## Reglas de oro durante la migración

1. **Nunca borres el Streamlit hasta que Next.js cubra todo.** Ambos
   coexisten mientras dura el proceso.
2. **Commit + push tras cada checkpoint funcional.** Sin excepción.
3. **Cada fase se prueba antes de arrancar la siguiente.** No acumular
   deuda de verificación.
4. **Si Claude Code propone algo que no entiendes, para y pregúntame.**
   Antes de aprobar.
5. **La rama `groq-deploy` es sagrada.** Es tu red de seguridad. No la
   toques hasta que la migración esté validada.

