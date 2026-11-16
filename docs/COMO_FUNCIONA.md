# Cómo funciona

## Flujo

```
              ┌──────────────────── modo chat ────────────────────┐   ┌──────── modo PC ────────┐
 qué visitar  │ consultas --hoy N  (feed, hashtags, palabras;      │   │ navegador.elegir_       │
              │                     rotación en datos/rotacion_…)  │   │ consultas (misma lista) │
 extraer      │ navegador integrado + extractor/linkedin_posts.js │   │ fuentes/linkedin.py     │
              │ (Claude lo corre en cada página)                   │   │ (Playwright + sesión)   │
              └──────────────────────────┬─────────────────────────┘   │ fuentes/google.py       │
                                         │                             └────────────┬────────────┘
                                         ▼                                          ▼
         JSON crudo: [{correos, autor, autorUrl, hace, url, texto, hashtags, imagenes, sinCorreo}]
                                         │
                    imagenes.py          ▼  (PC) afiches: alt → Tesseract → Haiku → texto_imagen
                    extraccion.py        ▼  cargo, empresa, ciudad, modalidad, salario, años,
                                            inglés, país, asunto exigido, autor limpio
                    filtros.py           ▼  línea (datos / gestión humana / ...) + descartes
                    clasificador.py      ▼  (opcional) Claude Haiku confirma las aceptadas
                    redaccion.py         ▼  asunto + cuerpo desde plantillas/ + qué CV
                                         │
              ┌──────────────────────────┴──────────────────────────┐
     chat:    │ Claude crea borradores con el conector de Gmail      │  PC: gmail_api.crear_borrador
              │ (CV adjunto por referencia de archivo)               │      (CV + firma)
              └──────────────────────────┬──────────────────────────┘
                                         ▼
                    historial.py   datos/historial.md  ◄── gmail_api.revisar_respuestas
                                         │
                    hashtags.py    datos/hashtags_ranking.md  → docs/HASHTAGS.md
                    personas.py    datos/personas_para_conectar.csv / .md
```

## Comandos

Todos se corren como `python -m buscador_empleo -p config/perfil.yaml <comando>`. Donde se
esperan archivos, se aceptan comodines entre comillas (`"datos/crudo/*.json"`), también en
PowerShell.

| Comando | Red / credenciales | Qué hace |
|---|---|---|
| `consultas [--tipo feed hashtag palabras] [--hoy N]` | no | Lista lo que se visita en LinkedIn. Con `--hoy N` elige N en rotación (el feed siempre) y guarda dónde quedó. |
| `js [-o archivo] [--imagenes] [--scrolls N]` | no | Imprime el extractor con la configuración incluida: correos ya postulados, países excluidos, palabras clave. `--imagenes` trae también posts sin correo con afiche. |
| `importar crudo.json ... [--ia] [--imagenes]` | no (`--ia` usa Anthropic; `--imagenes` necesita Tesseract) | Extrae, filtra, deduplica y redacta. Escribe `datos/vacantes_FECHA.json` y `datos/borradores_FECHA.json` e imprime una tabla corta. |
| `imagenes crudo.json ... [--sin-ia]` | Tesseract (+ Anthropic) | Lee los afiches de los posts sin correo y guarda lo leído en el mismo crudo. |
| `registrar vacantes.json [--solo correo ...] [--estado X]` | no | Agrega las aceptadas al histórico (por defecto "Borrador listo"). |
| `resumen` | no | Cuenta postulaciones por estado. |
| `hashtags [--minimo 2] [--actualizar-doc]` | no | Ranking de hashtags por vacantes útiles y por línea. |
| `personas [--top 15]` | no | Ranking de autores para seguir o conectar. Conserva el estado marcado a mano. |
| `sesion-linkedin` | navegador | Abre Chromium para iniciar sesión en LinkedIn una vez. |
| `buscar` | LinkedIn (si se activa) + Serper | Busca, lee afiches, guarda el crudo y hace `importar`. |
| `borradores [vacantes.json] [--simular]` | Gmail | Crea borradores con CV adjunto y firma, y los registra en el histórico. |
| `adjuntar [--simular]` | Gmail | Agrega el CV correcto a borradores sin adjunto. |
| `respuestas` | Gmail | Marca "Enviado" lo que ya salió y detecta rechazos y entrevistas. |
| `noche` | todo lo anterior | `respuestas` + `buscar` + `borradores` + `hashtags` + `personas` + reporte. |

## El perfil (`config/perfil.yaml`)

| Sección | Para qué |
|---|---|
| `candidato` | Nombre, correo de envío, profesión, años de experiencia, nivel de inglés, resumen (para la IA). |
| `ubicacion` | País, ciudades aceptadas (incluye "Remoto"), si se aceptan posts sin ciudad. |
| `lineas` | Una entrada por tipo de búsqueda: CV, plantilla, frase de experiencia del correo, `palabras_clave`, `palabras_excluir`, `consultas` y `hashtags`. |
| `busqueda` | Periodo y orden de LinkedIn, `linkedin_feed`, `scrolls_feed`, `hashtags_generales`, `rotar_consultas`, `linkedin_con_sesion`, `max_consultas_linkedin` (≤ 8), pausas, tolerancia de años, `scrolls`, `max_texto`. Google: `usar_google`, periodo, máximo. |
| `correos_ignorar` | Correos que nunca son de postulación (`info@`, `noreply`...). |
| `correos_descartados` | Correos o dominios (`@dominio.com`) descartados a mano. No vuelven a salir en `importar`, `hashtags` ni `personas`. |
| `imagenes` | `usar`, `idioma_ocr`, `tesseract_cmd`, `tessdata_dir`, `usar_ia_si_ocr_falla`, topes por ejecución, `max_por_post`, `leer_con_correo`. |
| `ia` | Activar Claude Haiku, modelo, tope por ejecución. |
| `gmail` | Rutas de `credentials.json` y `token.json`. |

## Reglas de filtrado (en orden; gana la primera que falla)

1. Correo ya está en el histórico → "ya postulada".
2. Correo o dominio en `correos_descartados` → "descartada a mano".
3. Post de alguien buscando empleo → descartado.
4. Vacante cerrada o cubierta → descartada.
5. Fecha límite vencida → descartada.
6. País distinto al del perfil (por texto, ciudades o dominio del correo) → descartada.
7. Ciudad fuera de la lista (salvo remoto) → descartada.
8. Pide inglés por encima del nivel del perfil → descartada.
9. Pide más años de experiencia que los del perfil + tolerancia → descartada.
10. No coincide con ninguna línea → descartada. Pasa cuando el cargo no tiene palabras
    clave y el texto casi no las menciona, o cuando tiene palabras excluidas (p. ej.
    gerente, contador, senior).

Lo que pasa todas las reglas es una vacante **aceptada**. En el chat, Claude revisa la tabla
y quita a mano lo que no tenga sentido. Si una exclusión se repite, se agrega a
`correos_descartados` o a `palabras_excluir`.

## Archivos que se generan (todos en `datos/`, ignorada por git)

| Archivo | Qué es |
|---|---|
| `crudo/*.json` | Salida del extractor tal cual (más `texto_imagen` si se leyeron afiches). |
| `vacantes_FECHA.json` | Todas las vacantes del día con su línea, motivo de descarte y texto. |
| `borradores_FECHA.json` | Para cada aceptada: `para`, `asunto`, `cuerpo`, `cv`, `linea`. |
| `historial.md` | El histórico (ver abajo). |
| `imagenes/` | Afiches descargados y `lecturas.json` (caché de lo ya leído). |
| `hashtags_ranking.md` | Ranking de hashtags. |
| `personas_para_conectar.csv / .md` | Ranking de autores con estado. |
| `rotacion_linkedin.json` | Dónde quedó la rotación de consultas. |
| `reporte_FECHA.md`, `logs/` | Resumen y log de la noche en el PC. |

## Histórico

`datos/historial.md` tiene una tabla por línea con las columnas
`Fecha | Empresa | Cargo | Ciudad / modalidad | Correo | Línea | Fuente | Estado | Notas`, y
luego las secciones "Descartadas" y "Aprendizajes". Se puede editar a mano (p. ej., marcar
"Oferta"). El lector acepta cualquier tabla Markdown que tenga una columna "Correo" y
conserva el texto libre.

Estados: `Borrador listo → Programado → Enviado → En proceso / Rechazado / Sin respuesta /
Oferta`, además de `Rebotado` (el correo no existe) y `Descartada`.

La columna **Fuente** se escribe como `LinkedIn (Nombre de quien publicó)`. `personas` la
usa para el ranking, aun para días sin crudo guardado.
