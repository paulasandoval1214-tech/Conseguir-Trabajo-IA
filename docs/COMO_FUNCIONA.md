# Cómo funciona

## Flujo

```
              ┌──────────────── modo chat ────────────────┐   ┌──── modo local ────┐
 fuentes      │ navegador + extractor/linkedin_posts.js   │   │ fuentes/google.py  │
              │ (Claude lo ejecuta en cada búsqueda)       │   │ fuentes/linkedin.py│ (apagado)
              └────────────────────┬──────────────────────┘   └─────────┬──────────┘
                                   ▼                                    ▼
                         JSON crudo: [{correos, autor, hace, url, texto}]
                                   │
                    extraccion.py  ▼  cargo, empresa, ciudad, modalidad, salario,
                                      años, inglés, país, asunto exigido
                    filtros.py     ▼  línea (datos / gestión humana / ...) + descartes
                    clasificador.py▼  (opcional) Claude Haiku confirma las aceptadas
                    redaccion.py   ▼  asunto + cuerpo desde plantillas/
                                   │
              ┌────────────────────┴──────────────────────┐
     chat:    │ Claude crea borradores con el conector     │  local: gmail_api.crear_borrador
              │ de Gmail (sin adjunto) ──► adjuntar_cvs.bat│        (con CV y firma)
              └────────────────────┬──────────────────────┘
                                   ▼
                    historial.py  datos/historial.md  ◄── gmail_api.revisar_respuestas
```

## Comandos

Todos se corren como `python -m buscador_empleo -p config/perfil.yaml <comando>`.

| Comando | Red / credenciales | Qué hace |
|---|---|---|
| `consultas` | no | Lista las URLs de búsqueda de publicaciones de LinkedIn de cada línea. |
| `js [-o archivo]` | no | Imprime el extractor con la configuración incluida (correos ya postulados, países excluidos, palabras clave). |
| `importar crudo.json ... [--ia]` | no (`--ia` usa Anthropic) | Extrae, filtra, deduplica y redacta. Escribe `datos/vacantes_FECHA.json` y `datos/borradores_FECHA.json` e imprime una tabla corta. |
| `registrar vacantes.json [--solo correo ...]` | no | Agrega las aceptadas al histórico con estado "Borrador listo". |
| `resumen` | no | Cuenta postulaciones por estado. |
| `buscar` | Serper (+ LinkedIn si se activa) | Busca y hace `importar`. |
| `borradores [vacantes.json] [--simular]` | Gmail | Crea borradores con CV adjunto y firma; registra en el histórico. |
| `adjuntar [--simular]` | Gmail | Agrega el CV correcto (según palabras clave de la línea) a borradores sin adjunto. |
| `respuestas` | Gmail | Marca "Enviado" lo que ya salió y detecta rechazos / entrevistas. |
| `noche` | Gmail + Serper | `respuestas` + `buscar` + `borradores` + reporte. |

## El perfil (`config/perfil.yaml`)

- `candidato`: nombre, correo de envío, profesión, años de experiencia, nivel de inglés.
- `ubicacion`: país y ciudades aceptadas (incluye "Remoto").
- `lineas`: una entrada por tipo de búsqueda, con CV, plantilla, frase de experiencia para el
  correo, palabras clave, palabras a excluir y consultas.
- `busqueda`: periodos, límites, tolerancia de años, modo LinkedIn (apagado).
- `ia`: activar Claude Haiku y modelo.
- `gmail`: rutas de `credentials.json` y `token.json`.

## Reglas de filtrado (en orden)

1. Correo ya está en el histórico → descartada.
2. Post de alguien buscando empleo → descartada.
3. Vacante cerrada / cubierta → descartada.
4. País distinto al del perfil → descartada.
5. Ciudad fuera de la lista (salvo remoto) → descartada.
6. Pide inglés por encima del nivel del perfil → descartada.
7. Pide más años de experiencia que los del perfil + tolerancia → descartada.
8. No coincide con ninguna línea (el cargo no tiene palabras clave y el texto casi no las
   menciona, o tiene palabras excluidas) → descartada.

## Histórico

`datos/historial.md` tiene una tabla por línea con las columnas
`Fecha | Empresa | Cargo | Ciudad / modalidad | Correo | Línea | Fuente | Estado | Notas`.
Se puede editar a mano (por ejemplo, marcar "Oferta"); el lector acepta cualquier tabla
Markdown que tenga una columna "Correo".

Estados: `Borrador listo → Enviado → En proceso / Rechazado / Sin respuesta / Oferta`.
