# Inventario funcional — Asistente MBE (vista Estudiante)

> Documento de referencia para diseño. Describe qué existe HOY en las
> pantallas del Asistente MBE que usa un Estudiante, sin detalles de
> implementación técnica.

## Acceso y alcance general

- No existe registro propio: las cuentas (una por estudiante, ej.
  "Estudiante 1", "Estudiante 2"...) son creadas de antemano por el equipo
  del curso. No hay pantalla de "crear cuenta" ni de "recuperar contraseña".
- Con una misma cuenta se puede iniciar sesión desde cualquier dispositivo o
  navegador: el historial de conversaciones no vive en el dispositivo, viaja
  con el usuario.
- El sistema reconoce automáticamente si la cuenta es de Estudiante o de
  Docente al iniciar sesión (no es algo que el usuario elija). Un Estudiante
  solo ve la pantalla del Asistente (chat). Un Docente ve, además, un Reporte
  de uso del curso (documentado aparte, en `inventario_reporte.md`); ese
  reporte no es visible ni accesible para un Estudiante.
- Una vez iniciada la sesión, esta se mantiene activa por un tiempo limitado
  (aprox. 1 día) sin necesidad de volver a autenticarse, incluso si se cierra
  y se vuelve a abrir el navegador.
- Dos pantallas funcionales conforman la experiencia del Estudiante:
  1. **Inicio de sesión**
  2. **Asistente (chat)** — incluye, dentro de sí misma, el historial de
     conversaciones anteriores del usuario (no es una pantalla aparte a la
     que se navegue, sino un panel siempre visible junto a la conversación
     activa).

---

## Pantalla 1 — Inicio de sesión

**Propósito:** validar la identidad del usuario antes de dar acceso al
Asistente.

### Qué información muestra
- Logo de la institución y nombre del asistente ("Asistente MBE") con su
  descripción corta ("Facultad de Medicina - Pontificia Universidad
  Javeriana").
- Campos para usuario y contraseña.
- Mensaje de error explícito si el usuario o la contraseña son incorrectos
  ("Usuario o contraseña incorrectos").
- Mientras no se ha iniciado sesión, no se muestra ningún otro contenido de
  la aplicación (ni siquiera el menú).

### Qué puede hacer el usuario aquí
- Ingresar usuario y contraseña e iniciar sesión.
- Reintentar si se equivoca (no hay bloqueo por intentos fallidos visible en
  esta pantalla).

### Qué datos vienen del backend
- Validación de las credenciales contra la lista de cuentas autorizadas del
  curso.
- El tipo de cuenta (Estudiante o Docente), que determina qué ve el usuario
  a partir de este punto.

---

## Pantalla 2 — Asistente MBE (chat)

**Propósito:** permitir que el estudiante haga preguntas sobre Medicina
Basada en la Evidencia y reciba respuestas apoyadas en material del curso.

### Qué información muestra
- Encabezado con el nombre del asistente y su descripción.
- Identificación del usuario que tiene la sesión iniciada.
- **Estado de bienvenida** (cuando la conversación activa todavía no tiene
  ninguna pregunta):
  - Mensaje de bienvenida invitando a preguntar.
  - 3 preguntas de ejemplo sugeridas, listas para usar con un clic, pensadas
    para mostrar el tipo de preguntas que el asistente puede responder.
- **Conversación activa**: el intercambio completo de preguntas del usuario
  y respuestas del asistente, en orden cronológico, cada una identificada
  visualmente según si la escribió el usuario o el asistente.
- Mientras el asistente está generando una respuesta, el texto va
  apareciendo de forma progresiva (no aparece de golpe), para que el usuario
  perciba que el sistema está trabajando en tiempo real.
- Campo para escribir una nueva pregunta, siempre visible al pie de la
  conversación.

### Qué puede hacer el usuario aquí
- Escribir cualquier pregunta en lenguaje libre y enviarla.
- Usar una de las preguntas sugeridas con un clic, sin tener que escribirla
  (solo disponible al iniciar una conversación nueva, antes de la primera
  pregunta).
- Leer la respuesta a medida que se va generando.
- Iniciar una conversación nueva en cualquier momento (ver Historial, más
  abajo), lo que limpia el área de conversación y vuelve a mostrar el estado
  de bienvenida.
- Cerrar sesión.

### Qué datos vienen del backend
- Para cada pregunta, una búsqueda automática en la base documental del
  curso que identifica los fragmentos de texto más relevantes para
  responderla (el usuario no ve estos fragmentos directamente, solo el
  resultado ya redactado).
- La respuesta generada a partir de esos fragmentos, con la instrucción de
  responder solo con base en ellos y no inventar información si el material
  disponible no alcanza para responder.
- El progreso de generación de la respuesta, entregado en tiempo real
  (palabra por palabra) en lugar de esperar a que esté completa.
- En segundo plano, cada intercambio (pregunta, respuesta, qué tan bien
  encontró contenido relevante y cuánto tardó cada paso) queda registrado;
  este registro es lo que después alimenta el Reporte que solo ve el
  Docente. El Estudiante no ve ni interactúa con este registro.

---

## Historial de conversaciones (panel dentro del Asistente)

**Propósito:** que el estudiante pueda retomar preguntas o respuestas de
sesiones anteriores sin perderlas, y organizar sus preguntas por tema o
sesión de estudio.

### Qué información muestra
- Un listado de todas las conversaciones anteriores del usuario, cada una
  identificada con un título corto tomado automáticamente de su primera
  pregunta.
- La conversación que se está viendo en este momento se distingue
  visualmente de las demás en la lista.
- El listado se muestra con la conversación más reciente primero.
- Este historial es acumulativo e independiente del dispositivo: si el
  estudiante inicia sesión en otro computador, ve las mismas conversaciones.

### Qué puede hacer el usuario aquí
- Iniciar una conversación nueva (queda vacía, con el estado de bienvenida,
  y aparece al tope del listado en cuanto se hace la primera pregunta).
- Hacer clic en cualquier conversación anterior de la lista para volver a
  verla completa (todas sus preguntas y respuestas) en el área principal.
- No hay opción visible para renombrar, archivar o eliminar una conversación
  del historial.

### Qué datos vienen del backend
- Todas las preguntas y respuestas previas del usuario, agrupadas por
  conversación, recuperadas desde el registro histórico de uso la primera
  vez que el usuario entra al Asistente en la sesión.
- El título mostrado de cada conversación se deriva automáticamente del
  texto de la primera pregunta de esa conversación (no es un nombre elegido
  por el usuario).

---

## Notas transversales para diseño

- El Estudiante nunca ve los fragmentos de texto recuperados, los puntajes
  de similitud ni las latencias que el sistema calcula por cada pregunta:
  toda esa información existe únicamente para el registro interno y para el
  Reporte del Docente. La experiencia del Estudiante es intencionalmente
  minimalista: pregunta → respuesta.
- El historial de conversaciones no es una pantalla separada a la que se
  "navegue": convive siempre junto a la conversación activa, como una forma
  de moverse entre sesiones de preguntas sin perder ninguna.
- La cuenta de un usuario determina su rol de forma automática y no
  editable desde la interfaz; no existe ninguna acción en pantalla para que
  un Estudiante solicite o vea permisos de Docente.
- No existe una pantalla de perfil o configuración de cuenta: las únicas
  acciones relacionadas con la cuenta disponibles para el Estudiante son
  iniciar sesión y cerrar sesión.
