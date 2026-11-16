# Instrucciones para Claude en este repo

- Propósito y flujo: `docs/CONTEXTO.md`. Paso a paso en el chat: `docs/GUIA_CLAUDE.md`.
- Usa la CLI (`python -m buscador_empleo ...`) para filtrar, deduplicar y redactar; no leas
  páginas completas de LinkedIn: usa `extractor/linkedin_posts.js` (guardado en el navegador con
  `js --cargador`, luego `await eval(localStorage.cti_run)`). Todo lo extraído va a `datos/crudo/`
  y pasa por `importar`; nada se descarta a ojo antes.
- Al terminar una sesión: `hashtags --actualizar-doc` y `personas`; anota en
  `docs/HISTORIAL_CAMBIOS.md` lo aprendido y los cambios de código.
- No sigas, conectes ni escribas a nadie en LinkedIn: la lista de `personas` es para que lo
  hagan ellos.
- **Privacidad**: nunca agregues al repo teléfonos, correos personales, CV, el perfil real
  (`config/perfil.yaml`) ni el histórico (`datos/`). Las pruebas usan dominios `*-ejemplo.com`.
- **Commits**: autor y committer "Miguel Muñoz" con su correo noreply de GitHub (pregúntalo si no
  está configurado). Sin trailers ni líneas de coautoría del asistente.
- **Correos**: solo borradores. Nunca enviar.
- Antes de hacer commit: `python -m pytest -q`.
