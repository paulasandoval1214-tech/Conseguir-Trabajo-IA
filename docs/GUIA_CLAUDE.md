# Guía para Claude (modo asistente en el chat)

Esta guía es para el asistente. El objetivo: encontrar vacantes nuevas, dejar borradores con
el CV adjunto y actualizar el histórico **gastando pocos tokens**. Regla de oro: el navegador
y Python hacen el trabajo pesado; el asistente solo mueve JSON pequeños y toma las decisiones
dudosas. **Todo lo que sale del navegador se guarda en `datos/crudo/` y pasa por `importar`.**
No se descarta nada "a ojo" antes de Python.

## 0. Preparar (una vez por sesión)

```bash
git clone <repo> && cd conseguir-trabajo-ia
pip install -r requirements.txt --break-system-packages   # PyYAML, requests, pytest
export PYTHONPATH=src
```

- **Perfil**: el perfil real NO está en el repo. Léelo del proyecto de Claude
  (`claude/perfil.yaml`) y guárdalo como `config/perfil.yaml`. Si no existe, créalo desde
  `config/perfil.example.yaml` preguntando a la persona lo mínimo.
- **Histórico**: léelo del proyecto (`claude/historico_postulaciones.md`) y guárdalo como
  `datos/historial.md`. Sirve para no repetir correos.
- **Personas para conectar**: si existe `claude/personas_para_conectar.csv` en el proyecto,
  guárdalo como `datos/personas_para_conectar.csv`. Así se conservan los estados que la
  persona marcó (Seguido / Conectado / Descartar). Al final de la sesión súbelo de nuevo.
- **CV**: si una hoja de vida está solo en el computador de la persona (p. ej. una línea
  nueva), pide acceso a esa carpeta con el puente del dispositivo y cópiala a `cvs/`.
- **CV**: si hay que adjuntar desde el chat, los PDF deben estar en el entorno (descárgalos
  del correo de la persona con el conector de Gmail si ya los envió antes).
- Revisa en Gmail los enviados recientes si hay dudas de duplicados.

## 1. Qué visitar hoy

```bash
python -m buscador_empleo -p config/perfil.yaml consultas --hoy 6
```

Devuelve el feed de inicio (si está activo) y 5 búsquedas más **en rotación**: hashtags y
palabras clave. La próxima sesión sigue donde quedó esta (`datos/rotacion_linkedin.json`).
Si `datos/` es nuevo en esta sesión, el punto de partida depende de la fecha: cada día toca
un grupo distinto aunque no haya memoria entre sesiones.

## 2. Cargar el extractor en el navegador (una vez)

El extractor queda guardado en el `localStorage` de linkedin.com del navegador integrado y
persiste entre sesiones. Primero compara versiones:

```bash
python -m buscador_empleo -p config/perfil.yaml js --version
```

En el navegador (con la herramienta de JavaScript, en una página de linkedin.com):
`localStorage.cti_version`. Si no coincide o está vacío:

```bash
python -m buscador_empleo -p config/perfil.yaml js --cargador -o /tmp/cargador.js
```

Lee `/tmp/cargador.js` y ejecútalo **una vez** en el navegador. También carga los correos ya
postulados del histórico, así el extractor no los devuelve.

## 3. Extraer

Para cada URL de la lista:

1. `navigate` a la URL. La persona debe tener sesión de LinkedIn en el navegador integrado.
   Si la página pide login, pídele que inicie sesión; no escribas contraseñas.
2. Ejecuta, **solo esta línea** (LinkedIn bloquea `eval` si va con más instrucciones):
   `await eval(localStorage.cti_run_acum)`
   Devuelve un resumen corto (correo + 140 caracteres por post) y guarda el JSON completo en
   `localStorage.cti_acc`. Así cada post viaja una sola vez por la conversación.
3. Al terminar todas las consultas, ejecuta `localStorage.cti_acc`. Si es grande, el chat lo
   guarda solo en un archivo (`/tmp/claude-tool-results/...txt`, formato
   `[{"type":"text","text":...}]`). **Pásale ese archivo tal cual a `importar`**: lo
   reconoce. Cópialo antes a `datos/crudo/DD_NN.json` para no perderlo. Luego vacía el
   acumulado con `localStorage.cti_acc = '[]'`.
   - Si es pequeño y se ve en la conversación, guárdalo tal cual en `datos/crudo/`.
   - No intentes descargarlo como archivo: el navegador integrado no guarda descargas en
     la carpeta de Descargas (probado el 22-nov).

En el **feed**, antes del paso 2 ejecuta `localStorage.cti_extra = '{"scrolls":25}'`, y al
terminar vuelve a `'{}'`.

**Si LinkedIn limita** (dos o tres páginas con "No se han encontrado resultados" seguidas):
para por hoy. No insistas: arriesga la cuenta. Sigue con lo que ya hay. Ojo: una sola página
vacía con una consulta larga es normal; prueba una más corta antes de concluir que es el
límite.

Para ahorrar tokens:
- 8–16 consultas por sesión, si hace varios días que no se busca. Consultas cortas.
- Si la semana ya está agotada (las consultas devuelven 0–2 posts nuevos y la página sí
  muestra resultados), repite las que más rinden con `datePosted=%22past-month%22`.
- En el panel oculto, el feed con 25 scrolls puede pasar de 45 s y la herramienta corta la
  llamada; el script termina igual y guarda en `cti_acc`. Espera y revisa
  `JSON.parse(localStorage.cti_acc).length` antes de repetir. En búsquedas usa
  `localStorage.cti_extra = '{"scrolls":10}'`.
- No leas la página con `get_page_text` ni capturas: el extractor ya trae lo necesario.
- Si una respuesta es muy grande, baja `maxTexto` con `localStorage.cti_extra`.
- Afiches: el chat no puede leerlos con OCR. Si la persona quiere aprovecharlos, carga el
  extractor con `js --cargador --imagenes` y deja los crudos para que en el PC corran
  `scripts\leer_afiches.bat`.

## 4. Filtrar y redactar (Python, gratis)

```bash
python -m buscador_empleo -p config/perfil.yaml importar "datos/crudo/DD_*.json"
```

Imprime las ACEPTADAS y un conteo de DESCARTADAS por motivo. Escribe
`datos/vacantes_FECHA.json` y `datos/borradores_FECHA.json`, con `para`, `asunto`, `cuerpo`,
`cv` y `linea`.

Tú eres la "IA" de este modo (no hace falta `--ia`):
- Revisa las aceptadas y quita las que no tengan sentido (cargos gerenciales, otro país,
  otra profesión). Si dudas, abre su texto en `datos/vacantes_FECHA.json`.
- Revisa los descartes "no coincide con ninguna línea" que tengan Bogotá. A veces el cargo
  no se detectó, y eso es un bug que vale la pena corregir en `extraccion.py` con una
  prueba.
- Lo que descartes a mano y pueda volver a salir: agrégalo a `correos_descartados` del
  perfil (y súbelo al proyecto).

## 5. Borradores en Gmail (conector)

- Antes, comprueba duplicados: `search_threads` con `in:sent {to:a to:b ...}` y
  `list_drafts` con los dominios.
- Crea **un borrador por vacante con `create_draft`**, de uno en uno; en paralelo pueden
  fallar.
- Usa `para`, `asunto` y `cuerpo` del JSON. Respeta el asunto exigido. La firma (nombre y
  teléfono) va al final del cuerpo: `includeSignature` del conector no la agrega.
- Adjunta con referencia de archivo, no en base64:
  `{"content": "sha256:<hash>:/ruta/al/CV.pdf", "filename": "CV.pdf", "mimeType": "application/pdf"}`.
  La línea de datos lleva el CV de datos; la de gestión humana, el CV de gestión humana y
  la carta.
- Verifica con `list_drafts` y `has:attachment newer_than:1d`.
- Si no hay PDF en el entorno: crea el borrador sin adjunto y dile a la persona que haga
  doble clic en `scripts\adjuntar_cvs.bat` en su computador.
- **Nunca envíes** correos. Solo borradores.

## 6. Histórico

```bash
python -m buscador_empleo -p config/perfil.yaml registrar datos/vacantes_FECHA.json \
    --solo correo1@empresa.com correo2@empresa.com   # solo las que quedaron en borrador
```

- En la columna Fuente usa `LinkedIn (Nombre de quien publicó)`; `personas` lo aprovecha.
- Agrega en "Descartadas" y "Aprendizajes" lo nuevo del día.
- Sube `datos/historial.md` al proyecto de Claude como `claude/historico_postulaciones.md`.
  Primero haz `project_read`, luego `project_write` con `local_path`.

## 7. Rankings (gratis, al final de cada sesión)

```bash
python -m buscador_empleo -p config/perfil.yaml hashtags --actualizar-doc   # docs/HASHTAGS.md
python -m buscador_empleo -p config/perfil.yaml personas --top 15
```

Muéstrale a la persona los 10–15 primeros pendientes de `personas` para que los siga o
conecte a mano. **No sigas ni conectes tú.** Si `hashtags` muestra uno con muchos posts y
0 útiles, propón quitarlo del perfil.

## 8. Respuestas (cuando la persona lo pida)

Con el conector de Gmail, busca mensajes recibidos de los dominios del histórico
(`from:@dominio newer_than:30d`) y rebotes (`from:mailer-daemon newer_than:7d`). Clasifica
cada uno como rechazo, entrevista, acuse de recibo o rebote. Actualiza la columna Estado y
anota en "Aprendizajes" lo que se repita (p. ej. "piden SQL").

## 9. Si cambias código

- Agrega una prueba con datos ficticios (`*-ejemplo.com`) y corre `python -m pytest -q`.
- Anota el cambio y el porqué en `docs/HISTORIAL_CAMBIOS.md`. Si cambia el uso, también en
  `README.md`.
- Commit y push con la identidad de `CLAUDE.md`.

## Reglas que no se negocian

- Nada personal al repositorio: teléfonos, correos, CV, histórico, perfil, nombres de
  reclutadores. Eso va solo a `datos/`, `config/perfil.yaml`, `cvs/`, `secretos/` o al
  proyecto de Claude.
- Commits a nombre de la persona dueña del repo (ver `CLAUDE.md`), nunca del asistente.
- No automatizar envíos, mensajes, seguimientos ni conexiones en LinkedIn.
- Si una vacante pide algo que la persona no tiene (inglés avanzado, años de más), no se
  envía.
