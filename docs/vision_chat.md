# Visión de diseño — Asistente MBE (chat)

> Brief de dirección visual y de experiencia. Se lee junto con
> `inventario_chat.md`, que describe qué información y qué acciones tiene
> cada pantalla. Este documento define **cómo debe verse y sentirse**.
> Complementa `vision_reporte.md`: ambos deben compartir paleta,
> tipografía y tokens de diseño.

---

## Contexto

**Producto:** interfaz conversacional de un asistente RAG (Retrieval-
Augmented Generation) sobre Medicina Basada en Evidencia, para uso
educativo. Parte de una tesis de Maestría en Inteligencia Artificial en
la Pontificia Universidad Javeriana.

**Público principal:** estudiantes universitarios de medicina cursando
la materia de MBE. Digitalmente competentes, acostumbrados a chats tipo
ChatGPT, WhatsApp, etc. Esperan que la interacción se sienta natural y
familiar.

**Público secundario:** docentes, que también acceden al mismo chat
(entre otras cosas) para probar la herramienta en primera persona. El
diseño del chat es el mismo para ambos roles — la diferenciación docente
vs estudiante ocurre en el acceso al reporte, no en el chat.

**Objetivo del diseño:** que el estudiante entre, pregunte con
confianza, reciba una respuesta que se sienta apoyada en material
académico, y quiera volver.

---

## Dirección estética

**Coherencia con el reporte docente:** este chat comparte identidad
visual con `vision_reporte.md`. Misma paleta institucional (azul
Javeriana profundo + acento verde teal + grises neutros), misma
tipografía sans-serif refinada, misma iconografía line icons. El
estudiante o docente debe reconocer instantáneamente que chat y reporte
son la misma herramienta.

**Tono específico del chat:** más cálido y conversacional que el
reporte, sin perder la sobriedad académica. El reporte es un
instrumento; el chat es un compañero de estudio. Puede permitirse un
poco más de aire y calidez, pero nunca cae en tono "asistente de
startup" (nada de "¡Hola! 👋 ¿En qué puedo ayudarte hoy?").

**Referencia negativa (lo que NO queremos):**
- Estética "de chatbot corporativo" con burbujas rígidas y avatares
  cartoon.
- Emojis grandes protagónicos, especialmente en la bienvenida.
- Un look Streamlit crudo (que es lo que hay hoy).
- Sensación de encuesta o formulario.

**Referencia positiva:**
- **ChatGPT / Claude.ai** para el patrón de conversación central: burbujas
  suaves, streaming de respuesta natural, historial en sidebar izquierdo.
- **Perplexity** para cómo la respuesta se siente apoyada en fuentes,
  incluso cuando no muestra la fuente explícitamente (aire, tipografía
  seria, sensación de "esto no lo estoy inventando").
- **Notion AI** para la calidad tipográfica de las respuestas del
  asistente (buen manejo de bloques, listas, énfasis).

---

## Principios rectores

1. **Foco en la conversación.** La conversación activa es el
   protagonista visual. Todo lo demás (historial, header, controles)
   debe estar presente pero en jerarquía secundaria. El estudiante
   entra a preguntar, no a navegar.

2. **Bienvenida acogedora, no intimidante.** El estado de bienvenida es
   la primera impresión de la herramienta. Debe transmitir "esto es un
   compañero de estudio serio, hazle una pregunta" — no un formulario
   ni un test.

3. **Respuesta que se sienta confiable.** Aunque hoy el estudiante no
   ve los chunks recuperados, la tipografía, el ritmo del streaming y
   la estructura de la respuesta deben transmitir seriedad y anclaje
   en evidencia. Es una decisión de diseño consciente que la respuesta
   se lea académica, no casual.

4. **Historial presente pero no invasivo.** El sidebar de conversaciones
   está siempre disponible, pero visualmente más liviano que la
   conversación central. Colapsable en pantallas pequeñas.

5. **Cero fricción para preguntar.** El campo de entrada debe estar
   siempre visible, siempre accesible, y responder al primer clic. Un
   solo enter para enviar.

---

## Consideración de diseño abierta (decisión pendiente)

El inventario actual establece que el estudiante **no ve** los
fragmentos de texto recuperados ni las fuentes. En MBE, la
trazabilidad de la evidencia es un valor pedagógico central — un
estudiante que aprende MBE debería, idealmente, poder ver de dónde
salió la respuesta.

**Recomendación:** dejar espacio en el diseño para una futura
funcionalidad de "ver fuente" o "expandir citas" en cada respuesta del
asistente, aunque no se implemente en esta iteración. Puede ser un
icono discreto al pie de cada respuesta que hoy no hace nada visible, o
simplemente reservar la zona visual. Esto evita rediseñar la burbuja
del asistente después.

Esta decisión conviene discutirla explícitamente con los docentes en
la sesión de evaluación.

---

## Layout general

- **Sidebar izquierdo persistente:** identidad institucional (escudo
  Javeriana pequeño), nombre del asistente ("Asistente MBE"), botón
  prominente de "Nueva conversación", listado de conversaciones
  anteriores (título auto-generado, la activa destacada), identificación
  del usuario logueado abajo con opción de cerrar sesión.
- **Área central:** la conversación activa (o el estado de bienvenida
  si no hay preguntas aún), con el campo de entrada fijo al pie.
- **Sin sidebar derecho.** No hay panel de configuración ni ajustes —
  el usuario está aquí para conversar.
- **Responsivo:** en pantallas pequeñas, el sidebar de historial se
  colapsa a un botón que lo despliega como overlay. La conversación
  siempre ocupa el espacio principal.

---

## Dirección visual por pantalla

Referirse al inventario para el detalle funcional.

### Pantalla 1 — Inicio de sesión

- **Layout centrado**, tarjeta única con logo Javeriana arriba, título
  "Asistente MBE", descripción corta ("Facultad de Medicina — Pontificia
  Universidad Javeriana") en tipografía discreta.
- **Formulario mínimo:** dos campos (usuario, contraseña), un botón
  primario grande "Iniciar sesión".
- **Fondo sobrio:** blanco o gris muy tenue, sin ilustración de fondo,
  sin gradientes. Sensación académica.
- **Mensaje de error** en rojo sobrio, alineado al formulario, no como
  banner intrusivo.
- **Sin enlaces "olvidé mi contraseña" ni "crear cuenta"** — esas
  acciones no existen en el producto.

### Pantalla 2 — Chat (estado de bienvenida)

Es lo que ve el estudiante justo después de login o al iniciar una
conversación nueva.

- **Área central vacía, generosa.** Título grande centrado tipo "Hola,
  [nombre]. ¿Sobre qué quieres estudiar hoy?" o similar — sin emoji.
- **Tres tarjetas de preguntas sugeridas** debajo, clickeables. Cada
  una con un ícono line icon a la izquierda que hint al tipo de
  pregunta (ej: ícono de libro para conceptual, ícono de estetoscopio
  para caso clínico, etc.), y el texto de la pregunta como el
  contenido principal. Al hacer clic, la pregunta se envía
  directamente.
- **Campo de entrada fijo al pie** con placeholder tipo "Escribe tu
  pregunta sobre Medicina Basada en Evidencia..." y botón de enviar a
  la derecha.
- **Nada más.** Nada de tips, tutoriales, banners.

### Pantalla 2 — Chat (conversación activa)

- **Burbujas de conversación** limpias, sin bordes duros. Distinción
  visual clara pero sobria entre usuario y asistente:
  - Usuario: alineado a la derecha, fondo azul institucional suave,
    texto blanco o gris muy oscuro (según contraste).
  - Asistente: alineado a la izquierda, fondo blanco o gris muy
    tenue, borde sutil o sombra mínima, texto principal en negro/
    gris oscuro.
- **Tipografía de la respuesta del asistente** con más peso que un
  chat casual: renglones cómodos (line-height generoso), soporte
  visual para listas, negrita, bloques de código si aparecen. Debe
  leerse como material de estudio, no como un mensaje de WhatsApp.
- **Streaming de respuesta** visible: el texto aparece progresivamente
  con un cursor o indicador sutil al final mientras genera. Sin
  spinner grande.
- **Espacio reservado al pie de cada respuesta del asistente** para la
  futura funcionalidad de "ver fuente" (ver consideración abierta
  arriba). Puede ser una fila delgada con ícono de link o libro
  discreto, incluso si aún no hace nada.
- **Campo de entrada siempre fijo al pie**, no scrollea con la
  conversación. La conversación scrollea detrás de él.
- **Auto-scroll al final** cuando llega una respuesta nueva, pero el
  usuario puede subir manualmente sin ser forzado hacia abajo.

### Panel de historial (sidebar izquierdo)

- **Botón "Nueva conversación"** arriba de todo, prominente pero no
  agresivo — es la acción principal del sidebar.
- **Listado de conversaciones** debajo, cada una una fila con:
  - Título auto-generado (truncado a una línea con ellipsis).
  - Sin fecha visible (el orden ya lo comunica; agregar fecha satura).
  - La conversación activa destacada con fondo azul suave y borde
    lateral en verde teal.
- **Sin acciones adicionales** por conversación (no hay renombrar,
  archivar, eliminar). El listado es solo de lectura + selección.
- **Estado vacío** ("Aún no tienes conversaciones anteriores") con
  tipografía discreta, cuando aplica.

---

## Interacciones críticas

- **Enviar pregunta:** Enter envía. Shift+Enter salto de línea. Botón
  de enviar visible a la derecha del input; deshabilitado si el input
  está vacío o si el asistente está generando.
- **Mientras genera:** el input queda deshabilitado o con un indicador
  claro de que no se puede enviar otra pregunta hasta que termine. Un
  botón sutil de "detener generación" opcional (patrón ChatGPT).
- **Click en pregunta sugerida:** envía inmediatamente, sin paso
  intermedio de "confirmar".
- **Click en conversación del historial:** carga la conversación en el
  área central sin recarga de página, con transición discreta.
- **Nueva conversación:** limpia el área central y vuelve al estado de
  bienvenida. La conversación anterior queda guardada en el historial.
- **Cerrar sesión:** confirmación explícita mínima ("¿Cerrar sesión?"),
  luego redirige al login.

---

## Entregable esperado

- Un archivo HTML + Tailwind por cada estado: login, chat en
  bienvenida, chat con conversación activa (con streaming simulado si
  es viable), y una vista con el historial cargado y una conversación
  antigua seleccionada.
- Coherencia estricta con `vision_reporte.md`: mismo header
  institucional, mismos tokens de color, misma tipografía.
- Datos ficticios pero realistas: preguntas de ejemplo genuinas de MBE
  (formulación PICO, GRADE, riesgo relativo, etc.), respuestas del
  asistente que se lean como respuestas académicas serias, no genéricas.
- Comentarios en el código señalando componentes reutilizables entre
  chat y reporte (sidebar, header, botones primarios).

---

## Iteración esperada

1. Primer entregable: login + chat en estado de bienvenida. Bloquear
   dirección estética y tokens.
2. Segundo entregable: chat con conversación activa y streaming.
3. Tercer entregable: sidebar de historial con estados (vacío, con
   conversaciones, con activa seleccionada).
4. Congelar. Los mockups se usan para:
   - La presentación con docentes (screenshots de "hacia dónde va el
     chat").
   - Referencia visual para la migración a Next.js + FastAPI tras la
     defensa.