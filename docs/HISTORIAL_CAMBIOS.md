# Historial de cambios y aprendizajes

Bitácora del proyecto en orden: qué buscamos cada día, qué salió, qué aprendimos y qué se
cambió en el código por eso. Sirve para entender por qué el código es como es, y para que
otra persona que descargue el repo arranque con todo este camino ya recorrido.

> Solo conteos y aprendizajes. Los nombres de empresas, personas y correos de cada
> postulación viven en el histórico privado (`datos/historial.md` y el proyecto de Claude).

## Resumen en números

| Fecha | Cómo se buscó | Posts revisados | Vacantes aceptadas | Borradores | Notas |
|---|---|---|---|---|---|
| 10-nov | — | — | — | — | Se rehízo la hoja de vida (datos) y el correo base. |
| 11-nov | A mano con Claude (navegador), ~15 búsquedas por palabras | ~150 | 27 | 27 | 13 de datos, 14 de gestión humana. Todas enviadas. |
| 12-nov | Extractor + `importar` | pocos (LinkedIn devolvió 0–7 por búsqueda) | 2 | 2 | Cargos afines de gestión humana. Enviados. |
| 13-nov | Respuestas | — | — | — | 1 rechazo (cargo afín de relaciones laborales), 1 rebote (correo mal escrito en el post), 1 acuse de recibo. |
| 15/16-nov | Extractor + `importar`, ~16 búsquedas (relevancia, última semana) | 56 con correo nuevo | 9 (8 tras revisión) | 8 | LinkedIn empezó a limitar ("No se han encontrado resultados"). |

| 22-nov | Extractor guardado en el navegador (modo acumulado), feed + 15 búsquedas | 152 con correo nuevo | 23 (15 tras revisión) | 15 | Una semana sin buscar. Nueva línea de riesgo operacional. Sin límite de LinkedIn. |

Estado al 22-nov: 33 enviadas, 15 borradores listos, **2 en proceso (entrevistas)**, 1
rechazada, 2 rebotadas.

---

## 2026-11-10 — Hoja de vida y correo

- Se escribió la hoja de vida de la línea de datos. Es apta para ATS, conserva la foto y
  reorienta la experiencia a datos sin inventar nada: People Analytics, freelance en
  dashboards y cursos de ciencia de datos.
- Correo base: muy corto y cordial, con la firma (nombre y teléfono) en el cuerpo:
  "Buen día, espero te encuentres bien. Estoy interesada en la vacante de X. Adjunto mi
  hoja de vida, en la que podrán ver mi experiencia en Y. Quedo atenta…".

## 2026-11-11 — Primera búsqueda (manual) y proyecto inicial

**Cómo se hizo:** Claude buscó en LinkedIn **publicaciones** (no la sección de Empleos) de
la última semana o mes, leyó las que traían correo, descartó las que no encajaban, revisó
en Gmail que no se hubiera escrito antes y dejó borradores con el CV adjunto.

**Aprendizajes:**
- La búsqueda de publicaciones rinde mucho más que la sección de empleos para encontrar
  correos de postulación.
- Leer páginas completas gasta muchísimos tokens → se creó el **extractor JS**, que corre
  dentro de la página y devuelve solo los posts con correo, recortados.
- Consultas cortas (3–5 palabras) funcionan mejor que las largas.
- Muchos resultados son de Ecuador, Perú y México → filtro por país.
- Algunas vacantes exigen un asunto exacto → se respeta.

**Código:** proyecto inicial (`3ce4ac9`): extractor, CLI `importar/registrar/resumen`,
filtros, plantillas por línea, histórico en Markdown, modo local con Gmail API y Serper.

**Mejoras esa misma noche** (`128e56b`), tras revisar los descartes reales:
- El **titular del autor** ("Psicóloga | Analista de reclutamiento") contaminaba el cargo →
  se separa la cabecera del cuerpo.
- Cargos entre comillas, entre paréntesis o seguidos de la ciudad → limpieza del cargo.
- Páginas que **republican ofertas** (tipo "Ofertas de trabajo") se tomaban como la empresa →
  se detectan como agregadores.
- Fechas límite ya vencidas → descarte.
- País por el dominio del correo (`.ec`, `.pe`, `.mx`, `.gt`, `.cr`…) y más ciudades de
  Colombia.

## 2026-11-12 — Segunda búsqueda y correos con tilde

- LinkedIn devolvió muy pocos posts nuevos (0–7 por búsqueda): primera señal de que limita
  cuando se hacen muchas búsquedas en pocos días.
- Un post escribía el correo con tilde ("Andrés.x@empresa-ejemplo.com"). El extractor lo
  recortaba a "s.x@empresa-ejemplo.com" → regex con *lookbehind* que no corta en letras con tilde
  (`60086a6`), en Python y en JS, con prueba.
- Se probaron **cargos afines** (entrenamiento, relaciones laborales) en gestión humana.

## 2026-11-13 — Primeras respuestas

- **Rechazo** del cargo afín de relaciones laborales ("tu perfil no se ajusta") →
  aprendizaje: los afines muy distintos al perfil se rechazan rápido; priorizar selección y
  datos.
- **Rebote** de un correo tomado de una página que republica ofertas: el post traía la
  dirección mal escrita → aprendizaje: con agregadores, verificar el correo o usar el canal
  alterno del post (WhatsApp, formulario).
- **Acuse de recibo** automático de una empresa (no cuenta como respuesta).

## 2026-11-15/16 — Búsqueda después de dos días de pausa

**Cómo se hizo:** extractor con la configuración guardada en el navegador
(`localStorage`), consultas cortas con orden por **relevancia** y última semana, y todo
pasado por `importar`, sin descartar a ojo.

**Resultado:** 56 posts con correo nuevo → `importar` aceptó 9 → se revisaron a mano →
8 borradores (1 de datos y 7 de gestión humana). Después de unas 16 búsquedas, LinkedIn
empezó a responder "No se han encontrado resultados" incluso con consultas que antes
funcionaban.

**Aprendizajes:**
- Ordenar por **relevancia** trae más resultados que por fecha.
- Casi todo lo publicado en la semana ya se había visto: hay que **ampliar las fuentes**,
  no repetir búsquedas.
- Muchas publicaciones ponen el cargo y el correo **solo en el afiche** (imagen).
- Un banco de otro país (Nicaragua) pasó el filtro porque el texto no nombraba el país →
  descartes manuales en el perfil (`correos_descartados`).
- "Gerente de Data & AI" pasó como línea de datos → se excluyen cargos gerenciales.
- Una vacante de Soledad (Atlántico) pasó como "sin ciudad" → más ciudades.
- Un post traía el cargo solo en un hashtag (`#AuxiliarDeTalentoHumano`) → el cargo se
  saca también de hashtags.

**Código** (`8ec6224`): Nicaragua y Honduras como países, Soledad como ciudad, cargo desde
hashtags, "gerente/director" excluidos en la línea de datos.

## 2026-11-16 — Afiches, hashtags, feed y personas para conectar (v0.2.0)

Ideas de Miguel después de la búsqueda del 15/16:
1. Leer las **imágenes** de las publicaciones, que muchas veces traen el correo o varios
   cargos, y buscar por **hashtags** (#trabajosihay…) en lugar de solo por palabras.
2. **Seguir o conectar** con personas que comparten vacantes seguido (reclutadoras,
   líderes de gestión humana), para que el feed traiga vacantes sin gastar búsquedas.

Decisiones: la lectura de imágenes corre **en el PC con Windows** (OCR gratis; el chat no
puede descargar imágenes de LinkedIn). La lista de personas la arma **Python** y la acción
de conectar la hacen ellos, a mano.

**Qué se encontró al revisar LinkedIn por dentro:**
- El LinkedIn nuevo ya **no marca los posts con `data-urn`**. La página se desplaza dentro
  de `<main id="workspace">` y no en la ventana, así que el extractor viejo solo veía los
  primeros 3 posts del feed. Ahora se ubica cada post por su encabezado oculto
  ("Publicación en el feed") y se desplaza el contenedor correcto. Con eso pasó de 3 a 23
  posts en el feed en la prueba.
- Los afiches de los posts son imágenes `feedshare-shrink_*`. Fotos de perfil, logos y
  portadas de video se ignoran.
- El feed antepone contexto social ("Seguido por X", "X recomienda esto"). El autor real
  es el último nombre enlazado antes de la marca "• 2º" o de la hora.
- Palabras como "empleo" o "trabajo" aparecen en consejos de hoja de vida. Para posts
  **sin** correo se exigen señales fuertes de vacante ("estamos buscando", "envía tu hoja de
  vida", "#vacante"…).

**Código** (`6a8997c` y siguientes):
- Extractor v2: búsquedas, hashtags y feed. Trae `autorUrl`, `hashtags` e `imagenes`. Con
  `incluirImagenes` también trae posts sin correo pero con afiche (`sinCorreo`). Omite
  anuncios.
- `imagenes.py` y el comando `imagenes` (`importar --imagenes`): lee el texto alternativo,
  luego Tesseract y luego Claude Haiku, solo si el OCR no halló correo. Usa caché por URL y
  topes por noche. Detecta Tesseract solo en Windows; los idiomas van en
  `herramientas/tessdata`, sin permisos de administrador.
- `hashtags.py` y el comando `hashtags`: ranking por vacantes útiles y por línea, más la
  tabla generada en [HASHTAGS.md](HASHTAGS.md).
- `personas.py` y el comando `personas`: ranking de autores en
  `datos/personas_para_conectar.csv/.md`. Conserva el estado que marquen a mano
  (Pendiente / Seguido / Conectado / Descartar).
- Consultas: feed, hashtags generales y por línea, orden por relevancia y **rotación**
  entre sesiones (`consultas --hoy N`), para no gastar siempre las mismas búsquedas.
- Playwright: descarga los afiches con la sesión y se detiene tras dos páginas "sin
  resultados" seguidas. Sin sesión o sin Playwright, avisa y sigue con Gmail y Google, sin
  tumbar la noche. Nuevo comando `sesion-linkedin` (`scripts\iniciar_sesion_linkedin.bat`).
- `noche` ahora también lee afiches y regenera los rankings.
- `correos_descartados` en el perfil, estado "Rebotado", `.gitattributes` para CRLF en
  scripts de Windows e `instalar.ps1` que instala OCR y navegador.

## 2026-11-22 — Primeras entrevistas, tercera línea y extracción más barata

**Respuestas de la semana:**
- **Entrevista**: la empresa de un cargo de coordinación de talento al que se escribió el
  12-nov invitó por Teams. Fue el primer "sí" por correo directo, 10 días después.
- **En proceso**: una postulación hecha por un portal de empleo (no por este método) llamó
  a entrevista. Hay que registrar también lo que se envía por otros canales.
- **Rebote técnico**: el servidor de correo de una cadena hotelera no aceptó conexiones
  durante 3 días. No era la dirección: eso también cuenta como "Rebotado".

**Nueva línea:** riesgo operacional / procesos (fintech), con su propia hoja de vida y
plantilla `plantillas/correo_riesgo_operacional.txt`. Búsquedas que sirvieron: "riesgos hoja
de vida" y "analista de procesos hoja de vida". Las que tenían "riesgo operacional"
trajeron casi solo vacantes de otros países.

**Extracción más barata:** antes cada post viajaba dos veces por la conversación: al
extraerlo y al copiarlo a `datos/crudo/`. Ahora:
- `cti_run_acum` guarda todo en `localStorage.cti_acc` y solo devuelve un resumen.
- Al final, `localStorage.cti_acc` es tan grande que el chat lo guarda solo en un archivo.
- `importar` lee ese archivo tal cual (`_desenvolver` en `cli.py`).

Se probó descargarlo como archivo desde el navegador integrado y no funciona: las descargas
no llegan a la carpeta de Descargas.

**Filtros** (según los descartes reales del día):
- Países: Ecuador (SENESCYT), México (INFONAVIT, IMSS), Paraguay (.py), Brasil (.br,
  "vaga", "oportunidade"), Uruguay (.uy) y Bolivia (.bo).
- Ciudades: Galapa y El Rosal.
- Se descartan como "persona buscando empleo" los posts que recomiendan a un candidato
  ("quiero recomendar a…").
- Palabras de exclusión por línea: practicante/aprendiz; engineer/LLM en datos.
- Palabras de la línea de riesgo: "analista de riesgo", "control de operaciones",
  "procesos de mejora".
- Datos: "workforce" y "WFM".

---

## Cómo seguir esta bitácora

Después de cada sesión de búsqueda (en el chat o la noche en el PC):
1. Agrega una fila a "Resumen en números".
2. Si algo nuevo hizo que una vacante buena se descartara, o que una mala pasara, anótalo
   como aprendizaje y, si se corrigió, el commit que lo corrige.
3. Los aprendizajes de **la persona** (qué responden, qué rechazan) van en la sección
   "Aprendizajes" del histórico privado. Aquí solo van los que cambian el código o el
   método.
