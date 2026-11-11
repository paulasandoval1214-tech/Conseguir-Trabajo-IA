# Instrucciones para Claude en este repo

- Propósito y flujo: `docs/CONTEXTO.md`. Paso a paso en el chat: `docs/GUIA_CLAUDE.md`.
- Usa la CLI (`python -m buscador_empleo ...`) para filtrar, deduplicar y redactar; no leas
  páginas completas de LinkedIn: usa `extractor/linkedin_posts.js`.
- **Privacidad**: nunca agregues al repo teléfonos, correos personales, CV, el perfil real
  (`config/perfil.yaml`) ni el histórico (`datos/`). Las pruebas usan dominios `*-ejemplo.com`.
- **Commits**: autor y committer "Miguel Muñoz" con su correo noreply de GitHub (pregúntalo si no
  está configurado). Sin trailers ni líneas de coautoría del asistente.
- **Correos**: solo borradores. Nunca enviar.
- Antes de hacer commit: `python -m pytest -q`.
