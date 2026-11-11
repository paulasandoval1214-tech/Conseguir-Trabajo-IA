# Guía para Claude (modo asistente en el chat)

Esta guía es para el asistente. El objetivo: encontrar vacantes nuevas, dejar borradores y
actualizar el histórico **gastando pocos tokens**. Regla de oro: el navegador y Python hacen el
trabajo pesado; el asistente solo mueve JSON pequeños y toma las decisiones dudosas.

## 0. Preparar (una vez por sesión)

```bash
git clone <repo> && cd conseguir-trabajo-ia
pip install -r requirements.txt --break-system-packages   # PyYAML, requests, pytest
```

- **Perfil**: el perfil real NO está en el repo. Búscalo en el proyecto de Claude
  (`claude/perfil.yaml`) y guárdalo como `config/perfil.yaml`. Si no existe, créalo a partir de
  `config/perfil.example.yaml` preguntando a la persona lo mínimo.
- **Histórico**: léelo del proyecto (`claude/historico_postulaciones.md`) y guárdalo como
  `datos/historial.md`. Sirve para no repetir correos.
- Revisa también en Gmail (conector) los enviados recientes si hay dudas de duplicados.

## 1. Buscar (navegador integrado)

```bash
python -m buscador_empleo -p config/perfil.yaml consultas      # URLs por línea
python -m buscador_empleo -p config/perfil.yaml js -o /tmp/extractor.js
```

Lee `/tmp/extractor.js` **una vez**. Para cada URL:

1. `navigate` a la URL (la persona debe tener sesión de LinkedIn en el navegador integrado; si
   la página pide login, pídele que inicie sesión, no escribas contraseñas).
2. Ejecuta el contenido del extractor con la herramienta de JavaScript. Devuelve un JSON con
   solo los posts que traen correo nuevo, ya recortados.
3. Guarda el resultado tal cual en `datos/crudo/NN.json`.

Consejos para ahorrar tokens:
- 4–6 consultas por sesión suelen bastar (cada una trae 10–25 posts con correo).
- Si el resultado es muy grande, baja `busqueda.max_texto` (p. ej. 600) o `scrolls`.
- No leas la página con `get_page_text`/capturas: el extractor ya trae lo necesario.

## 2. Filtrar y redactar (Python, gratis)

```bash
python -m buscador_empleo -p config/perfil.yaml importar datos/crudo/*.json
```

Imprime una tabla corta de ACEPTADAS y un conteo de DESCARTADAS por motivo, y escribe
`datos/borradores_FECHA.json` con `para`, `asunto`, `cuerpo`, `cv` y `linea`.

Tú eres la "IA" de este modo (no hace falta `--ia`): revisa la tabla y quita las que no tengan
sentido para el perfil (por ejemplo, analista financiero). Si dudas de una, abre su texto en
`datos/vacantes_FECHA.json`.

## 3. Borradores en Gmail (conector)

- Crea **un borrador por vacante con `create_draft`**, de uno en uno (en paralelo pueden fallar).
- Usa exactamente `para`, `asunto` y `cuerpo` del JSON. Respeta el asunto exigido.
- El conector no adjunta el PDF de forma práctica y no pega la firma. Al terminar, dile a la
  persona que haga doble clic en `scripts\adjuntar_cvs.bat` en su computador: pone el CV correcto
  y la firma en todos los borradores sin adjunto.
- **Nunca envíes** correos. Solo borradores.

## 4. Histórico

```bash
python -m buscador_empleo -p config/perfil.yaml registrar datos/vacantes_FECHA.json \
    --solo correo1@empresa.com correo2@empresa.com   # solo las que quedaron en borrador
```

Luego sube `datos/historial.md` al proyecto de Claude como `claude/historico_postulaciones.md`
(reemplazando el anterior).

## 5. Respuestas (cuando la persona lo pida)

Con el conector de Gmail, busca mensajes recibidos de los dominios del histórico
(`from:@dominio newer_than:30d`). Clasifica: rechazo / entrevista / sin respuesta, actualiza la
columna Estado y anota en "Aprendizajes" lo que se repita (p. ej., "piden SQL").

## Reglas que no se negocian

- Nada personal al repositorio (teléfonos, correos, CV, histórico, perfil). Solo a `datos/`,
  `config/perfil.yaml`, `cvs/`, `secretos/` o al proyecto de Claude.
- Commits a nombre de la persona dueña del repo (ver `CLAUDE.md`), nunca del asistente.
- No automatizar envíos ni mensajes en LinkedIn.
- Si una vacante pide algo que la persona no tiene (inglés avanzado, años de más), no se envía.
