# Inventario funcional — Reporte docente (Asistente MBE)

> Documento de referencia para diseño. Describe qué existe HOY en el Reporte
> de Uso que ve un Docente, sin detalles de implementación técnica.

## Acceso y alcance general

- El reporte es exclusivo para usuarios con rol **Docente**. Un Estudiante que
  intente entrar ve un mensaje de "sin permisos" y no accede a ninguna pantalla.
- Todo el reporte se basa en una única fuente de datos: el registro histórico
  de preguntas hechas al Asistente MBE (quién preguntó, cuándo, qué preguntó,
  en qué sesión, y qué tan bien respondió el sistema).
- El reporte tiene 4 niveles de profundidad, pensados como "zoom in":
  1. **General** (Pulso) — resumen ejecutivo del curso.
  2. **Temas** — qué está preguntando el curso.
  3. **Estudiantes** — listado y comparación entre estudiantes.
  4. **Estudiante individual** — detalle de una sola persona (solo se llega
     haciendo clic desde la vista de Estudiantes o desde una alerta).
- Las vistas 1–3 son pestañas de navegación superior. La vista 4 nunca aparece
  como pestaña: es una pantalla de detalle a la que se entra y de la que se
  sale explícitamente.

### Controles disponibles en todas las pantallas (barra lateral)

- **Selector de período**: fecha "Desde" y fecha "Hasta", acotado al rango de
  fechas que existen en los datos. Todo lo que se muestra en las pestañas 1–3
  se recalcula según este período.
- **Filtro de quién pregunta**: Todos / Solo Docentes / Solo Estudiantes.
  Filtra qué preguntas se incluyen en las tres vistas agregadas según el rol
  de quien las hizo.
- Identificación del docente que tiene la sesión iniciada y opción de cerrar
  sesión.

---

## Nivel 1 — General (Pulso del curso)

**Propósito:** responder en segundos "¿cómo va la semana?". Es la pantalla de
entrada.

### Qué información muestra
- Seis indicadores numéricos del período seleccionado, cada uno comparado
  contra el período inmediatamente anterior de igual duración (variación en %):
  - Total de estudiantes (roster completo, no depende del período)
  - Estudiantes activos
  - Total de chats (sesiones de conversación)
  - Total de preguntas
  - Preguntas por estudiante (promedio)
  - Tiempo promedio por sesión
- Gráfico de actividad de las últimas 4 semanas (volumen de preguntas por
  semana), siempre mostrando las 4 semanas más recientes independientemente
  del período elegido arriba.
- Distribución de preguntas por día de la semana.
- Mapa de calor de actividad cruzando día de la semana y hora del día.
- Detalle opcional expandible con: duración promedio de sesión y porcentaje
  de uso concentrado en los 2 días más activos (con aviso si ese uso está
  muy concentrado, ≥40%).
- Hasta 3 tarjetas de alerta automática, priorizadas, señalando lo que más
  necesita atención del docente esa semana. Los tipos de alerta posibles son:
  - Un tema de preguntas que subió significativamente esta semana.
  - Un tema con preguntas frecuentes pero baja calidad de respuesta (el
    sistema no está encontrando buen contenido para responderlas).
  - Estudiantes que nunca han usado la herramienta o que llevan 2+ semanas
    sin actividad.
  - Uso del curso muy concentrado en pocos días de la semana.
  - Si no hay nada que amerite alerta, se indica explícitamente que todo
    está en orden.
- Si el análisis de temas (ver Nivel 2) aún no se ha generado para el período
  actual, se avisa que las alertas relacionadas con contenido no están
  disponibles todavía.

### Qué puede hacer el usuario aquí
- Cambiar el período y el filtro de rol desde la barra lateral y ver todo
  recalculado.
- Hacer clic en "Ver más" de una tarjeta de alerta para saltar directamente a
  la pestaña Temas (con foco en el tema correspondiente) o a la pestaña
  Estudiantes, según el tipo de alerta.
- Expandir/contraer el detalle de patrones de horario.
- Navegar a las otras pestañas.

### Qué datos vienen del backend
- Conteos de preguntas, estudiantes activos, sesiones y duración de sesión
  del período actual y del período anterior (para calcular las variaciones).
- Serie semanal de volumen de preguntas de las últimas 4 semanas.
- Distribución de preguntas por hora y por día de la semana.
- Duración promedio de sesión y porcentaje de concentración en los 2 días
  más activos.
- Tamaño total del roster de estudiantes.
- Resultado del análisis de temas más reciente generado en la pestaña Temas
  (si existe), usado para detectar tema en alza y temas con baja calidad de
  respuesta.
- Lista de estudiantes que nunca han usado la herramienta y de estudiantes
  inactivos hace 2+ semanas (calculada sobre todo el histórico, no solo el
  período seleccionado).

---

## Nivel 2 — Temas (qué se está preguntando)

**Propósito:** entender de qué está hablando el curso, agrupando preguntas
por significado.

### Qué información muestra
- Si se llegó desde una alerta con un tema específico, un aviso indicando en
  qué tema está puesto el foco.
- Antes de generar el análisis: una explicación de qué hace el análisis y
  cuánto puede tardar (1 a 3 minutos), y un botón para generarlo. Si no hay
  al menos 5 preguntas en el período, se avisa que no hay suficientes datos.
  Si no hay conexión disponible al servicio de análisis, se avisa que la
  función no está disponible.
- Una vez generado, para el período seleccionado:
  - Número de grupos temáticos identificados.
  - Gráfico de barras con cada tema y cuántas preguntas contiene.
  - Por cada tema: nombre, número y porcentaje de preguntas, y una lista de
    preguntas de ejemplo reales de ese tema.
  - Gráfico de evolución semana a semana de cada tema (si hay al menos 2
    semanas de datos en el período), para ver si un tema crece o desaparece
    con el tiempo.

### Qué puede hacer el usuario aquí
- Generar el análisis de temas bajo demanda (no se ejecuta automáticamente
  por lo que puede tardar).
- Quitar el foco en un tema específico si llegó desde una alerta.
- Expandir cada tema para ver sus preguntas de ejemplo.
- El análisis generado queda disponible mientras no cambie el período
  seleccionado (si el docente cambia de fecha, debe volver a generarlo).

### Qué datos vienen del backend
- Todas las preguntas del período seleccionado (texto de la pregunta).
- Agrupación automática de esas preguntas por similitud de significado.
- Nombre descriptivo de cada grupo temático, generado automáticamente a
  partir del contenido de las preguntas de ese grupo.
- Selección automática de preguntas de ejemplo representativas por grupo.
- Conteo semanal de preguntas por tema para la evolución temporal.

---

## Nivel 3 — Estudiantes (vista de grupo)

**Propósito:** comparar el nivel de uso entre estudiantes y detectar quién
necesita seguimiento.

### Qué información muestra
- Histograma de "esfuerzo": cuántos estudiantes caen en cada rango de
  cantidad de preguntas hechas en el período (0, 1–5, 6–20, más de 20).
- Lista de estudiantes silenciosos: quienes ya usaron la herramienta antes
  pero no tienen actividad hace 2 o más semanas, con hace cuántos días fue
  su última actividad.
- Lista de estudiantes que nunca han usado la herramienta (nombres).
- Si todos los estudiantes del curso han tenido actividad reciente, se indica
  explícitamente.
- Listado completo de estudiantes del curso (roster), cada uno con: nombre,
  número de preguntas en el período, número de sesiones, y los últimos temas
  que ha tocado (si ya existe un análisis de temas generado). El orden por
  defecto es de menor a mayor uso (para resaltar primero a quien menos ha
  usado la herramienta), no alfabético.

### Qué puede hacer el usuario aquí
- Hacer clic en "Ver" en la fila de cualquier estudiante para entrar a su
  detalle individual (Nivel 4). Esta es la única puerta de entrada a esa
  pantalla junto con las alertas de Nivel 1.

### Qué datos vienen del backend
- Roster completo de estudiantes matriculados (fuente de cuentas con acceso
  a la herramienta).
- Actividad de cada estudiante en el período seleccionado: número de
  preguntas, número de sesiones, últimos temas tocados (si hay análisis de
  temas disponible). Un estudiante sin actividad en el período aparece igual
  en la lista, con ceros.
- Fecha de última actividad de cada estudiante (calculada sobre todo el
  histórico, no solo el período seleccionado), usada para identificar a los
  "silenciosos".

---

## Nivel 4 — Estudiante individual

**Propósito:** dar al docente el mínimo de información necesaria para una
tutoría puntual con un estudiante, sin exponer todo su historial.

**Acceso:** solo llegando desde una fila de la pestaña Estudiantes (o desde
una alerta que apunte a un estudiante). No es una pestaña visible de forma
permanente y se marca explícitamente como una vista restringida para uso de
tutoría docente.

### Qué información muestra
- Nombre del estudiante, total de preguntas, total de sesiones y fecha de su
  última actividad (todo esto sobre el histórico completo del estudiante, no
  limitado al período seleccionado en la barra lateral).
- Sus últimas 3 a 5 preguntas hechas, con fecha (no se muestra todo su
  historial de preguntas).
- Un gráfico de línea de tiempo con su actividad diaria a lo largo de todo
  su historial.
- Perfil temático: qué temas ha tocado y cuáles no, comparado contra el
  universo completo de temas identificados (solo disponible si ya se generó
  el análisis de temas en la pestaña Temas).

### Qué puede hacer el usuario aquí
- Volver a la pestaña Estudiantes con un botón explícito ("Volver a
  Estudiantes").

### Qué datos vienen del backend
- Conteo total de preguntas y sesiones del estudiante, y fechas de primera y
  última actividad (histórico completo).
- Sus últimas 3 a 5 preguntas registradas.
- Su actividad diaria (número de preguntas por día) a lo largo del tiempo.
- Todas sus preguntas históricas, cruzadas contra el mapeo de temas generado
  en la pestaña Temas, para calcular qué temas ha tocado y cuáles no.

---

## Notas transversales para diseño

- El reporte distingue explícitamente "datos agregados" (vistas 1–3, seguros
  de mostrar a cualquier docente) de la "vista individual" (Nivel 4, marcada
  como de uso exclusivo para tutoría), y lo comunica al docente en pantalla.
- El análisis de temas es el único proceso "pesado" (puede tardar minutos) y
  por eso es bajo demanda; todo lo demás responde de inmediato al cambiar
  filtros. El diseño debe seguir contemplando estados de "aún no generado",
  "generando" y "generado" para ese análisis, y que varias pantallas dependen
  de que ya exista para mostrar ciertos contenidos (alertas de contenido en
  Nivel 1, últimos temas en Nivel 3, perfil temático en Nivel 4).
- Varias señales (nunca usado, silenciosos, última actividad) se calculan
  siempre sobre el histórico completo del curso, independientemente del
  período de fechas elegido en la barra lateral — es una distinción funcional
  importante a comunicar en la interfaz para no confundir al docente.
