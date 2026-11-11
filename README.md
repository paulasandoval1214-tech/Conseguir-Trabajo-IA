# Conseguir-Trabajo-IA

Herramienta para encontrar vacantes que piden **enviar la hoja de vida por correo** y dejar en
Gmail **borradores listos** (asunto, cuerpo, CV adjunto) para que la persona solo revise y
dé *Enviar*. También lleva un **histórico** de postulaciones y detecta respuestas (rechazos,
entrevistas) para aprender qué funciona.

Nació para ayudar a una persona en transición de carrera (psicología → análisis de datos) y está
pensada para que **cualquiera** pueda usarla con su propio perfil.

> Nunca envía correos por su cuenta. Solo crea borradores.

## Dos formas de usarla

| Modo | Quién la corre | Para qué sirve |
|---|---|---|
| **Asistente en el chat** | Claude, dentro de una conversación | Claude extrae posts de LinkedIn con un script y Python hace el trabajo pesado (limpiar, filtrar, no repetir, redactar). Gasta muchos menos tokens que leer las páginas. Ver [docs/GUIA_CLAUDE.md](docs/GUIA_CLAUDE.md). |
| **Local / nocturno** | Tu computador (Windows), con una tarea programada | Busca en Google posts públicos con correo, filtra (reglas + Claude Haiku opcional), crea borradores con el CV adjunto y revisa respuestas. Ver [docs/INSTALACION_WINDOWS.md](docs/INSTALACION_WINDOWS.md). |

## Cómo funciona (resumen)

```
fuentes (LinkedIn vía navegador / Google)      -> posts con correo
extraccion.py   texto libre -> cargo, empresa, ciudad, inglés, años, asunto exigido
filtros.py      país, ciudad, inglés, experiencia, profesión, ya postulada, vacante cerrada
clasificador.py (opcional) segunda opinión con Claude Haiku
redaccion.py    plantilla por línea -> asunto + cuerpo + qué CV va
gmail_api.py    borradores con CV adjunto, adjuntar CVs, revisar respuestas
historial.py    histórico en Markdown (legible por personas y por la IA)
```

Más detalle en [docs/COMO_FUNCIONA.md](docs/COMO_FUNCIONA.md) y el porqué de cada decisión en
[docs/CONTEXTO.md](docs/CONTEXTO.md).

## Inicio rápido

```bash
pip install -e .                    # o: pip install -r requirements.txt
cp config/perfil.example.yaml config/perfil.yaml   # y edítalo
python -m buscador_empleo consultas                # URLs de búsqueda por línea
python -m buscador_empleo importar datos/crudo/*.json   # filtra y redacta
python -m buscador_empleo resumen                  # estado del histórico
```

Windows, todo automático cada noche:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\instalar.ps1
powershell -ExecutionPolicy Bypass -File scripts\programar_tarea.ps1 -Hora "21:30"
```

## Privacidad (regla del repo)

Este repositorio **no guarda datos personales**: ni teléfonos, ni correos, ni hojas de vida, ni
el histórico. Todo eso vive en carpetas ignoradas por git (`config/perfil.yaml`, `cvs/`,
`datos/`, `secretos/`, `.env`). Detalles y buenas prácticas en
[docs/PRIVACIDAD_Y_BUENAS_PRACTICAS.md](docs/PRIVACIDAD_Y_BUENAS_PRACTICAS.md).

## Estructura

```
config/perfil.example.yaml   perfil de ejemplo (copiar a perfil.yaml)
plantillas/                  cuerpos de correo por línea ($cargo, $experiencia, ...)
extractor/linkedin_posts.js  script de navegador que devuelve solo posts con correo
src/buscador_empleo/         paquete Python (CLI: python -m buscador_empleo)
scripts/                     instalación y tarea programada de Windows
tests/                       pruebas con datos ficticios
docs/                        contexto, guía para Claude, instalación, privacidad
```

## Licencia

MIT.
