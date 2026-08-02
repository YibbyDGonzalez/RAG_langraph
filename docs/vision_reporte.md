# Visión de diseño — Reporte docente (Asistente MBE)

> Brief de dirección visual y de experiencia. Se lee junto con
> `inventario_reporte.md`, que describe qué información y qué acciones
> tiene cada pantalla. Este documento define **cómo debe verse y sentirse**.

---

## Contexto

**Producto:** reporte analítico para docentes de una herramienta educativa
de Medicina Basada en Evidencia (MBE) desarrollada como parte de una tesis
de Maestría en Inteligencia Artificial en la Pontificia Universidad
Javeriana, Bogotá.

**Público:** docentes universitarios de medicina. No son técnicos. Están
acostumbrados a interfaces académicas y clínicas, no a dashboards estilo
startup. Valoran seriedad, claridad, densidad de información controlada.

**Objetivo del diseño:** que el docente entre al reporte, en 10 segundos
entienda cómo va su curso, y en 3 clics llegue a la acción pedagógica
concreta que necesita.

---

## Dirección estética

**Tono:** institucional, académico, sobrio, cálido. Confiable. Que un
docente universitario lo abra y sienta que es una herramienta seria, no un
demo de estudiante.

**Referencia negativa (lo que NO queremos):**
- Estética "de científico" (Streamlit crudo, Jupyter, tablas sin jerarquía).
- Estética "startup SaaS" (gradientes vibrantes, ilustraciones cartoon,
  emojis grandes, tono jovial excesivo).
- Densidad tipo Bloomberg (cientos de cifras por pantalla).

**Referencia positiva:**
- iOS Screen Time / Apple Health para los gráficos de actividad (barras
  limpias, promedio con línea punteada, delta contra periodo anterior en
  color).
- Dashboards analíticos serios tipo Linear, Vercel Analytics, Notion — en
  el nivel de refinamiento tipográfico y espaciado, no en el tono.
- Publicaciones académicas de calidad — en la sobriedad y en el manejo del
  contraste.

**Paleta:**
- **Azul institucional profundo** como color principal (identidad
  Javeriana; algo como #1e3a5f o similar).
- **Verde teal** como acento secundario para positivo/alza (algo como
  #2b8a7a).
- **Rojo/ámbar sobrio** para alertas y bajas, sin saturar.
- **Grises neutros amplios** para texto, bordes, fondos alternos. Mucho
  aire.
- **Blanco** como base dominante.

**Tipografía:**
- Sans-serif de calidad para todo (Inter, Söhne, o similar). Sin serifas.
- Jerarquía clara: números grandes para los KPIs (48–56px), títulos de
  sección medianos (24–28px), cuerpo generoso (16px), micro-texto para
  captions (13–14px).

**Iconografía:**
- Line icons (tipo Lucide o Heroicons outline). Nunca ilustraciones
  cartoon, nunca emoji grandes como protagonistas visuales.
- Un ícono por sección o alerta, no decoración excesiva.

---

## Principios rectores

1. **Overview-first, details-on-demand** (Shneiderman). El docente entra a
   la vista general, algo le llama la atención, hace click, baja al
   detalle. Nunca al revés. La navegación debe respetar esto.

2. **Mínimo suficiente.** Últimas 3–5 preguntas, no todo el historial.
   Si el docente entiende con menos, mostrar menos. Aplica a todos los
   listados y timelines.

3. **Contexto sobre números aislados.** Ningún KPI se muestra solo —
   siempre con delta contra el periodo anterior o con línea de referencia
   (promedio, meta). Un "47 preguntas" no dice nada; un "47 preguntas
   (+40% vs periodo anterior)" ancla una decisión.

4. **Cada elemento debe cerrar en acción pedagógica.** Si una tarjeta o
   gráfico no lleva a una decisión que el docente pueda tomar sobre su
   clase, sobra. Esto vale para descartar propuestas de diseño.

5. **Privacidad visible.** El reporte distingue explícitamente entre
   "vista agregada" (Niveles 1–3) y "vista individual" (Nivel 4, sólo para
   tutoría). Esta distinción debe ser **visible en la interfaz**, no
   escondida en documentación. Un banner discreto o un cambio de color de
   contexto al entrar al Nivel 4 lo comunica.

---

## Layout general

- **Barra lateral izquierda persistente:** identidad institucional
  (escudo Javeriana pequeño), identificación del docente logueado,
  selector de período (Desde / Hasta), filtro de rol (Todos / Docentes /
  Estudiantes), botón de cerrar sesión.
- **Área principal:** contenido de la pestaña activa. Encabezado con
  título de la vista + breadcrumb si aplica (importante en Nivel 4).
- **Navegación entre Niveles 1–3:** tabs superiores claros, con el activo
  destacado. El Nivel 4 no aparece como tab: se entra desde una fila del
  Nivel 3 o desde una alerta.
- **Responsividad:** el docente puede abrir esto desde su portátil en
  clase. Prioridad desktop, pero que no se rompa en tablet.

---

## Dirección visual por pantalla

Referirse al inventario para el detalle funcional. Aquí solo la
dirección visual clave por pantalla.

### Nivel 1 — Pulso del curso

- **Los 6 KPIs se muestran como una fila (o dos) de tarjetas grandes**,
  cada una con el número protagonista muy grande y el delta debajo en
  color (verde teal si sube, rojo sobrio si baja, gris si estable). Es
  la primera cosa que ve el docente y debe leerse en 3 segundos.
- **Debajo, el gráfico de las 4 semanas** en formato barras verticales
  **estilo iOS Screen Time**: una barra por semana, línea horizontal
  punteada con el promedio, etiqueta "prom." al lado derecho, delta
  vs semana anterior arriba a la izquierda. Nada de heatmaps aquí.
- **Distribución por día de la semana:** barras verticales simples, sin
  segmentación, misma estética.
- **Mapa de calor día × hora:** este sí puede ser un heatmap, pero con
  paleta sobria (una sola escala de azul), pequeño, colapsable — no
  protagonista.
- **Tarjetas de alerta:** hasta 3, apiladas verticalmente, cada una con
  ícono a la izquierda, título corto, una línea de descripción, y un
  botón "Ver más" a la derecha que salta al Nivel correspondiente.
  Estilo neutro con acento de color según severidad (información / atención
  / positivo). Si no hay alertas, un estado vacío tranquilizador ("Todo
  en orden esta semana"), no un espacio en blanco incómodo.

### Nivel 2 — Temas

- **Estados del análisis** son parte central del diseño de esta pantalla:
  - *No generado*: card informativa central con explicación breve y
    botón CTA prominente para generar.
  - *Generando*: estado de carga honesto que dice cuánto puede tardar y
    qué está pasando (no un spinner mudo). Idealmente con un pequeño
    progreso o mensajes de fase.
  - *Generado*: los resultados.
- **Gráfico de barras horizontales de temas** con el nombre del tema y
  el conteo. Ordenado de mayor a menor.
- **Cada tema es una card expandible** con las preguntas de ejemplo
  adentro. Colapsadas por defecto para no saturar.
- **Gráfico de evolución temporal** debajo, con una línea por tema (top
  N temas, no todos, para no saturar).

### Nivel 3 — Estudiantes

- **Histograma de esfuerzo** arriba, como bloque destacado — es el
  insight de equidad más importante de la pantalla.
- **Dos bloques laterales** debajo: "Silenciosos" y "Nunca han usado".
  Listas cortas con nombre y días de inactividad. Si están vacíos, mensaje
  positivo explícito.
- **Tabla del roster** ordenada por menor uso primero. Columnas: nombre,
  #preguntas, #sesiones, últimos temas (chips pequeños), botón "Ver".
  Filas alternadas suaves, hover state claro. La fila debe sentirse
  clickeable de forma evidente.

### Nivel 4 — Estudiante individual

- **Cambio visual sutil de contexto al entrar**: un banner superior
  discreto que diga algo como *"Vista individual — uso exclusivo para
  tutoría"*. No un modal alarmante, pero sí visible.
- **Header con nombre y KPIs históricos** del estudiante (total
  preguntas, total sesiones, última actividad).
- **Últimas 3–5 preguntas** como cards simples con fecha y texto de la
  pregunta. Nada más.
- **Timeline de actividad diaria** como sparkline horizontal amplio.
- **Perfil temático** como chips: temas tocados en color, temas no
  tocados en gris tenue. Comunicación visual instantánea.
- **Botón claro y persistente "← Volver a Estudiantes"** arriba.

---

## Interacciones críticas

- **Cambio de período/filtro** desde la barra lateral recalcula las
  vistas 1–3 sin recargar página. Feedback de carga discreto.
- **Click en alerta del Nivel 1** navega al Nivel 2 o 3 con el foco ya
  puesto en el tema o estudiante correspondiente.
- **Click en fila de estudiante en Nivel 3** entra al Nivel 4 con
  transición clara (no abrir en pestaña nueva, no modal — es una vista
  aparte).
- **Estados vacíos** cuidados en toda pantalla: mensaje explícito,
  neutro, con próximo paso sugerido cuando aplique.
- **Distinción visual de datos "histórico completo" vs "período
  seleccionado"** cuando conviven en la misma pantalla (por ejemplo,
  el KPI de "total estudiantes" no depende del período, pero
  "estudiantes activos" sí). Etiquetar sutilmente para no confundir.

---

## Entregable esperado

- Un archivo HTML + Tailwind por cada uno de los 4 niveles, más un
  archivo base que incluya la barra lateral y navegación entre niveles.
- Datos ficticios pero realistas (nombres de estudiantes colombianos,
  fechas coherentes, cifras plausibles para un curso de ~30 estudiantes).
- Diseño desktop-first, responsive hasta tablet.
- Comentarios en el HTML/CSS explicando qué componentes son reutilizables
  para facilitar la migración posterior a React.

---

## Iteración esperada

Después del primer entregable, el flujo será:
1. Revisar visualmente cada nivel.
2. Ajustar dirección estética si algo se siente muy startup o muy
   corporativo.
3. Iterar componentes específicos que no cierren bien (tarjetas de
   alerta, gráficos, estados vacíos).
4. Congelar el diseño y usarlo como referencia para:
   - Los mockups de la presentación con docentes (screenshots).
   - La migración posterior a Next.js + FastAPI + Tailwind (después de
     defensa de tesis).
