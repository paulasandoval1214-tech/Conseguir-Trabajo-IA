# Estrategia de búsqueda: más vacantes sin que LinkedIn limite la cuenta

El cuello de botella no es filtrar ni redactar (eso lo hace Python gratis). El cuello de
botella es **cuántas publicaciones nuevas se ven**. LinkedIn limita las búsquedas: después de
unas 15 en un día empieza a responder "No se han encontrado resultados". Esta página explica
las cinco fuentes y cómo combinarlas.

## 1. Las fuentes, de la más barata a la más cara

| Fuente | Gasta búsquedas | Qué trae | Cómo se activa |
|---|---|---|---|
| **Feed de inicio** | No | Lo que publican las personas y páginas que sigue la candidata. | `busqueda.linkedin_feed: true`. En el chat: abrir `https://www.linkedin.com/feed/` y correr el extractor con `--scrolls 25`. |
| **Afiches (imágenes)** | No (usa lo ya visto) | Vacantes cuyo correo o cargo solo está en la imagen. | En el PC: `imagenes.usar: true` + Tesseract. El extractor con `incluirImagenes` trae esos posts. |
| **Hashtags** | Sí (1 por hashtag) | Volumen alto: empresas que etiquetan sus vacantes. | `busqueda.hashtags_generales` y `lineas.*.hashtags`. Ver [HASHTAGS.md](HASHTAGS.md). |
| **Palabras clave** | Sí (1 por consulta) | Lo más preciso por línea. | `lineas.*.consultas` (3–5 palabras). |
| **Google (Serper)** | No (de LinkedIn) | Posts públicos indexados. Suelen ser viejos. | `busqueda.usar_google: true` + `SERPER_API_KEY`. |

## 2. El feed: que las vacantes lleguen solas

El feed solo sirve si la candidata **sigue a quien publica vacantes**. Para eso existe:

```bash
python -m buscador_empleo -p config/perfil.yaml personas
```

Arma `datos/personas_para_conectar.md` y `.csv` con un ranking de autores (reclutadoras,
líderes de gestión humana, páginas de empleo, empresas) que ya publicaron vacantes que **sí
encajaron**. El puntaje es 3 × posts útiles + posts con correo.

Cómo usar la lista:
1. Abre el CSV (o `scripts\personas_para_conectar.bat`).
2. De arriba hacia abajo, de a **10–15 por día**:
   - **Páginas y agregadores** ("Ofertas de trabajo…", empresas): *Seguir*.
   - **Personas** (reclutadoras, analistas de selección): *Conectar* con una nota corta.
     Si no aceptan, *Seguir* también sirve para el feed.
3. Marca la columna `estado`: `Seguido`, `Conectado` o `Descartar`. La próxima ejecución
   respeta lo marcado.
4. Si el enlace es una búsqueda (`/search/results/people/...`), el post no traía el enlace
   al perfil: busca el nombre y elige el que trabaje en selección.

Nota sugerida para conectar (corta, sin pedir trabajo de una):

> Hola, soy psicóloga con experiencia en selección y People Analytics (Power BI). Vi que
> compartes vacantes de gestión humana y datos en Bogotá; me gustaría estar al tanto.
> ¡Gracias!

Efecto extra: cuando la candidata conecta con reclutadoras, su perfil les aparece.

## 3. Afiches: el correo que no está en el texto

Muchos posts dicen "¡Únete a nuestro equipo! #Vacante" y el cargo, la ciudad y el correo
están solo en la imagen. El extractor los marca con `sinCorreo: true` y guarda la URL de la
imagen. Luego `imagenes.py` los lee:

1. **Texto alternativo** que LinkedIn a veces trae (gratis).
2. **OCR con Tesseract** en el PC (gratis). Agranda y pasa a gris la imagen antes de leerla.
3. **Claude Haiku con visión**, solo si el OCR no encontró ningún correo. Tiene un tope
   (`max_ia_por_ejecucion`, 15 por defecto). Cuesta centavos.

Lo leído queda guardado dentro del mismo archivo crudo (`texto_imagen`), así que no se vuelve
a pagar. Después `importar` lo trata como cualquier otro post: un afiche con varios cargos
puede dar varias vacantes.

¿Por qué en el PC y no en el chat? Desde el chat no se pueden descargar las imágenes de
LinkedIn al entorno de Python, y mirarlas una por una gasta tokens. En el chat se puede
correr el extractor con `js --imagenes`, guardar el crudo y luego, en el PC, hacer doble clic
en `scripts\leer_afiches.bat`.

## 4. Rotación: no gastar siempre las mismas búsquedas

```bash
python -m buscador_empleo -p config/perfil.yaml consultas --hoy 6
```

Devuelve el feed (si está activo) más las siguientes 5 búsquedas de la lista (hashtags
generales, hashtags de cada línea, consultas por palabras). Guarda dónde quedó en
`datos/rotacion_linkedin.json`. Mañana sigue con las siguientes. La noche en el PC usa la
misma rotación con `max_consultas_linkedin` (máximo 8).

## 5. Señales de que LinkedIn está limitando

- Varias búsquedas seguidas con "No se han encontrado resultados", incluso con consultas
  que ayer funcionaban.
- El feed carga solo 2 o 3 publicaciones.

Qué hacer: parar por hoy (Playwright lo hace solo tras dos páginas vacías seguidas), dejar 1
o 2 días de pausa, y mientras tanto usar el feed y las respuestas de Gmail.

## 6. Ritmo recomendado

| Cuándo | Qué |
|---|---|
| Todos los días (noche en el PC) | Feed + 5 búsquedas en rotación + afiches + respuestas + borradores + rankings. |
| Cada 2 días (chat, si se quiere) | 4–6 consultas de `consultas --hoy 6`; todo por `importar`. |
| Cada semana | `hashtags --actualizar-doc` y mover hashtags entre "usar" y "evitar" en [HASHTAGS.md](HASHTAGS.md). Revisar `personas` y conectar con 10–15. |
| Cuando llegue un rechazo | Anotar el motivo en "Aprendizajes" del histórico. Si se repite, ajustar `palabras_excluir` o la línea. |
