# Contexto: qué estamos haciendo y por qué

## El problema

Muchas vacantes en Colombia (y Latinoamérica) no se publican en un portal con botón de
"postularse": aparecen como **posts de LinkedIn** de reclutadores o empresas con un texto tipo
*"envía tu hoja de vida a seleccion@empresa.com con el asunto X"*. Esas vacantes tienen menos
competencia, pero encontrarlas una a una, leer requisitos, escribir el correo, adjuntar el CV
correcto y acordarse de a quién ya se le escribió toma horas.

## El caso que dio origen al proyecto

Una profesional en psicología que se reorienta hacia **análisis de datos / Power BI**, con:

- experiencia en People Analytics (dashboards en Power BI y Excel, automatizaciones con macros),
- experiencia en selección y onboarding en empresas de retail y fintech,
- trabajo freelance en dashboards, limpieza de datos y automatización con Python,
- cursos de Machine Learning para BI, Python, SQL y estadística aplicada,
- inglés básico.

De ahí salen las **dos líneas de búsqueda** del perfil de ejemplo:

1. **Datos**: analista de datos, analista de información, analista BI / Power BI junior.
2. **Gestión humana**: analista de selección, reclutamiento, talento humano, generalista.

Cada línea tiene su propio CV y su propia plantilla de correo.

## Cómo lo hicimos la primera vez (manual, con Claude)

1. Se reescribió la hoja de vida para la línea de datos (formato apto para ATS, con foto,
   experiencia reorientada a datos sin inventar nada).
2. Claude buscó en LinkedIn **publicaciones** (no la sección de empleos) del último mes con
   palabras como "analista de datos", "power bi", "hoja de vida", "Bogotá", y leyó solo los
   posts que traían un correo.
3. Se descartaron vacantes fuera del país, que pedían inglés B2/C1, que pedían muchos más años
   de experiencia, o que eran de otra profesión (contabilidad, desarrollo, finanzas).
4. Se revisó en Gmail que no se hubiera escrito antes a esos correos.
5. Se crearon borradores en Gmail con un cuerpo corto y cordial, y el asunto que pedía cada
   vacante.
6. Se dejó un histórico con fecha, empresa, cargo, correo, CV usado y estado.

Ese primer intento encontró 10 vacantes buenas en ~15 búsquedas, pero gastó muchos tokens
leyendo páginas completas. Este repositorio convierte ese proceso en código para que:

- la IA solo reciba un JSON pequeño (el extractor ya filtra en el navegador),
- Python haga las reglas, la deduplicación y la redacción gratis,
- se pueda correr todas las noches y para otras personas.

## Aprendizajes que ya están en las reglas

- La búsqueda de **publicaciones** de LinkedIn rinde mucho más que la sección de empleos para
  encontrar correos. Ordenada por **relevancia** (y de la última semana) trae más que por fecha.
- Consultas cortas (3–5 palabras) funcionan mejor; con muchas palabras LinkedIn no devuelve nada.
- Hay muchas vacantes de Ecuador, Perú y México en los resultados: se filtran por país.
- El titular del autor ("Psicóloga | Analista de reclutamiento") confunde la detección del
  cargo; por eso se separa la cabecera del cuerpo del post.
- Algunas vacantes exigen un asunto exacto: se respeta.
- Posts de personas buscando empleo también traen correo: se descartan.
- La API de Gmail no agrega la firma sola: el código la lee de la configuración de Gmail y la
  pega al final.
- Adjuntar el PDF desde el chat obliga a pasar el archivo completo por la conversación, lo que
  sale caro; por eso existe `adjuntar` (lo hace el computador local, gratis).

- LinkedIn **limita las búsquedas** (unas 15 en un día y empieza a responder "No se han
  encontrado resultados"). Por eso hay rotación de consultas, el feed de inicio como fuente
  y la lista de personas para seguir (ver [MEJORAS_BUSQUEDA.md](MEJORAS_BUSQUEDA.md)).
- Muchas vacantes traen el correo **solo en el afiche**: se leen con OCR en el PC.
- Los hashtags se eligen con datos (`hashtags`), no a ojo (ver [HASHTAGS.md](HASHTAGS.md)).
- Los cargos "afines" muy lejanos al perfil se rechazan rápido. Las páginas que republican
  ofertas a veces traen el correo mal escrito.

La bitácora completa, día por día, está en [HISTORIAL_CAMBIOS.md](HISTORIAL_CAMBIOS.md).

## Límites y riesgos conocidos

- **LinkedIn con sesión automatizada va contra sus términos** y puede bloquear la cuenta. Por eso
  el modo LinkedIn con Playwright está apagado en el perfil de ejemplo. Si se activa, va con
  pocas consultas (máximo 8), pausas largas y rotación, y se detiene solo al primer síntoma
  de límite. Nunca sigue, conecta ni escribe a nadie.
- Las reglas son heurísticas: pueden descartar alguna vacante buena o dejar pasar alguna dudosa.
  La revisión humana antes de enviar es parte del diseño.
- "Masivo" no es "spam": un correo por vacante real, a la dirección publicada para postular,
  con el CV que corresponde.
