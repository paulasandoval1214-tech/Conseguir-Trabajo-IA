# Conseguir-Trabajo-IA

Herramienta para **conseguir empleo postulando por correo**. Muchas vacantes en Colombia no
están en un portal: son publicaciones de LinkedIn que dicen *"envía tu hoja de vida a
seleccion@empresa.com con el asunto X"*, a veces solo dentro de un afiche. Esta herramienta:

1. **Encuentra** esas publicaciones en búsquedas, hashtags, el feed de inicio y los afiches.
2. **Filtra** las que encajan con el perfil: línea, ciudad, país, inglés, años de
   experiencia, profesión, vacante cerrada, ya postulada.
3. **Redacta** un correo corto por vacante, con el asunto exigido y el CV que corresponde.
4. Deja **borradores en Gmail**, listos para revisar y enviar. **Nunca envía nada sola.**
5. Lleva un **histórico** de postulaciones y respuestas (rechazos, entrevistas, rebotes)
   para aprender qué funciona.
6. Sugiere **a quién seguir o conectar** en LinkedIn y **qué hashtags usar**, con evidencia
   de lo que ya funcionó.

Nació para ayudar a una psicóloga que se reorienta hacia análisis de datos (dos líneas:
*Analista de datos / Power BI* y *Gestión humana*). Está pensada para que **cualquier
persona** la descargue, ponga su perfil y siga el mismo camino, con todo lo aprendido ya
incorporado. El porqué de cada decisión está en [docs/CONTEXTO.md](docs/CONTEXTO.md). La
historia de cambios y aprendizajes, búsqueda por búsqueda, está en
[docs/HISTORIAL_CAMBIOS.md](docs/HISTORIAL_CAMBIOS.md).

---

## Dos formas de usarla

| Modo | Quién la corre | Qué hace | Guía |
|---|---|---|---|
| **Asistente en el chat** | Claude, en una conversación con acceso a un navegador y a Gmail | Claude abre LinkedIn y corre el extractor (devuelve un JSON pequeño, no la página). Python filtra, deduplica y redacta gratis. Claude crea los borradores con el conector de Gmail. | [docs/GUIA_CLAUDE.md](docs/GUIA_CLAUDE.md) |
| **Local / nocturno (Windows)** | Tu computador, con una tarea programada | Revisa respuestas en Gmail, busca en LinkedIn (con tu sesión, pocas consultas y en rotación) y en Google, **lee los afiches con OCR**, filtra (reglas + Claude Haiku), crea borradores con CV y firma, y actualiza los rankings de hashtags y personas. | [docs/INSTALACION_WINDOWS.md](docs/INSTALACION_WINDOWS.md) |

Los dos modos comparten el mismo perfil, las mismas reglas y el mismo histórico. Lo que se
puede hacer con Python se hace con Python, para **gastar pocos tokens**. La IA solo toma las
decisiones dudosas.

---

## Cómo funciona (de punta a punta)

```
                    ┌──────────── FUENTES (LinkedIn) ────────────┐
                    │ feed de inicio · hashtags · palabras clave │  ← consultas --hoy N (rotación)
                    └──────────────────────┬─────────────────────┘
          extractor/linkedin_posts.js      ▼  (corre DENTRO de la página)
          JSON pequeño: {correos, autor, autorUrl, texto, hashtags, imagenes, sinCorreo}
                                           │
          imagenes.py  (solo en el PC)     ▼  afiches sin correo en el texto:
                                              alt → OCR Tesseract → Claude Haiku si falla
          extraccion.py                    ▼  cargo, empresa, ciudad, modalidad, salario,
                                              años, inglés, país, asunto exigido, autor
          filtros.py                       ▼  línea del perfil + motivos de descarte
          clasificador.py (opcional)       ▼  segunda opinión de Claude Haiku
          redaccion.py                     ▼  asunto + cuerpo (plantillas/) + qué CV va
                                           │
     ┌──────────── chat ──────────────┐    │    ┌──────────── PC ─────────────┐
     │ conector de Gmail: create_draft│◄───┴───►│ gmail_api.py: borrador con  │
     │ con CV adjunto                 │         │ CV, firma; revisa respuestas│
     └────────────────┬───────────────┘         └──────────────┬──────────────┘
                      ▼                                        ▼
          historial.py → datos/historial.md (y copia en el proyecto de Claude)
                      │
          hashtags.py → qué hashtags traen vacantes útiles → docs/HASHTAGS.md
          personas.py → a quién seguir/conectar → datos/personas_para_conectar.csv
```

Más detalle (reglas de filtrado en orden, formato del histórico, todos los comandos) en
[docs/COMO_FUNCIONA.md](docs/COMO_FUNCIONA.md). La estrategia para encontrar más vacantes sin
que LinkedIn limite la cuenta está en
[docs/MEJORAS_BUSQUEDA.md](docs/MEJORAS_BUSQUEDA.md).

---

## Inicio rápido

```bash
pip install -e .                                   # o: pip install -r requirements.txt
cp config/perfil.example.yaml config/perfil.yaml   # edítalo: tus datos, líneas, CV
python -m buscador_empleo consultas --hoy 6        # qué visitar hoy en LinkedIn (en rotación)
python -m buscador_empleo js -o /tmp/extractor.js  # el script que se corre en cada página
python -m buscador_empleo importar "datos/crudo/*.json"   # filtra y redacta
python -m buscador_empleo registrar datos/vacantes_FECHA.json --solo correo1 correo2
python -m buscador_empleo resumen                  # estado del histórico
python -m buscador_empleo hashtags                 # qué hashtags sirven
python -m buscador_empleo personas                 # a quién seguir / conectar
```

Windows, todo automático cada noche:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\instalar.ps1          # Python, OCR, navegador
scripts\iniciar_sesion_linkedin.bat                                     # una sola vez
powershell -ExecutionPolicy Bypass -File scripts\programar_tarea.ps1 -Hora "21:30"
```

---

## Mapa del repositorio: qué hace cada archivo y para qué

### Código (`src/buscador_empleo/`)

| Archivo | Qué hace | Por qué existe |
|---|---|---|
| `cli.py` | Línea de comandos: `consultas`, `js`, `importar`, `registrar`, `resumen`, `hashtags`, `personas`, `imagenes`, `buscar`, `borradores`, `adjuntar`, `respuestas`, `sesion-linkedin`, `noche`. | Un solo punto de entrada para Claude y para el PC. Cada paso pesado es un comando. |
| `config.py` | Lee `config/perfil.yaml` (candidata, ubicación, líneas, búsqueda, imágenes, IA, Gmail) y `.env`. | El perfil es lo único que cambia de una persona a otra. |
| `modelos.py` | `PostCrudo` (lo que sale del extractor, incluido `texto_imagen`) y `Vacante` (normalizada). | Un formato común entre fuentes, filtros y redacción. |
| `extraccion.py` | Del texto libre saca correos, cargo, empresa, ciudad, modalidad, salario, años, inglés, país, asunto exigido y el autor limpio. | Los posts no tienen estructura. Aquí están casi todos los aprendizajes de formato: tildes en correos, hashtags tipo `#AuxiliarDeTalentoHumano`, ciudades, países por dominio. |
| `filtros.py` | Asigna la línea (por palabras clave) y el primer motivo de descarte. | Reglas gratis y explicables antes de gastar IA. |
| `clasificador.py` | Segunda opinión con Claude Haiku solo para las aceptadas (opcional). | Atrapa lo que las reglas no ven. Cuesta centavos. |
| `redaccion.py` | Llena la plantilla de la línea: asunto (respeta el exigido), cuerpo, qué CV adjuntar. | Correos cortos, iguales en tono, sin errores de copiar y pegar. |
| `historial.py` | Lee y escribe `datos/historial.md` (una tabla por línea, más "Descartadas" y "Aprendizajes"). | Legible por personas y por la IA. Evita repetir correos y guarda lo aprendido. |
| `imagenes.py` | Lee afiches: texto alternativo → OCR con Tesseract → Claude Haiku si el OCR no encontró correo. Caché por URL y topes por ejecución. | Muchas vacantes tienen el correo **solo en la imagen**. |
| `hashtags.py` | Ranking de hashtags según cuántas vacantes útiles trajeron, por línea. Reescribe la tabla de `docs/HASHTAGS.md`. | Afinar los hashtags con datos y no a ojo. |
| `personas.py` | Ranking de autores (reclutadoras, páginas, empresas) que publican vacantes que encajan. Conserva el estado marcado a mano. | Seguirlos convierte el feed en una fuente que no gasta búsquedas. |
| `gmail_api.py` | Gmail API en el PC: borradores con CV y firma, adjuntar CVs pendientes, revisar respuestas. | El conector del chat no pega la firma; el PC lo hace gratis. |
| `fuentes/navegador.py` | Arma las URLs (feed, hashtags, palabras; orden por relevancia), la **rotación** diaria y el extractor con su configuración. | Las mismas consultas para el chat y para Playwright. |
| `fuentes/linkedin.py` | Playwright con la sesión guardada: visita lo de hoy, corre el extractor, descarga afiches y se detiene si LinkedIn limita. | La búsqueda nocturna en el PC. Va apagada por defecto en el perfil de ejemplo. |
| `fuentes/google.py` | Busca posts públicos de LinkedIn en Google (Serper). | Fuente sin sesión. Rinde menos (posts viejos). |

### Otros archivos

| Ruta | Qué es |
|---|---|
| `extractor/linkedin_posts.js` | Script que se corre dentro de la página de LinkedIn. Devuelve solo los posts útiles, recortados. Funciona en búsquedas, hashtags y feed. |
| `config/perfil.example.yaml` | Perfil de ejemplo, comentado línea por línea. Se copia a `config/perfil.yaml` (privado). |
| `plantillas/correo_*.txt` | Cuerpo del correo por línea (`$cargo`, `$experiencia`, `$nombre`, ...). |
| `scripts/instalar.ps1` | Instala todo en Windows: entorno, dependencias, Chromium, Tesseract e idiomas del OCR. |
| `scripts/programar_tarea.ps1` / `ejecutar_noche.ps1` | Tarea programada diaria y lo que corre (deja log en `datos\logs\`). |
| `scripts/iniciar_sesion_linkedin.bat` | Abre un navegador para iniciar sesión en LinkedIn una vez. |
| `scripts/adjuntar_cvs.bat` | Pone el CV correcto en borradores sin adjunto (p. ej. los que dejó el chat). |
| `scripts/leer_afiches.bat` | OCR de lo último extraído y nuevo filtrado. |
| `scripts/personas_para_conectar.bat` | Actualiza y abre la lista de personas para conectar. |
| `tests/` | 30 pruebas con datos ficticios (`*-ejemplo.com`), incluido OCR real si hay Tesseract. |
| `docs/` | Contexto, cómo funciona, guía para Claude, instalación, hashtags, estrategia de búsqueda, privacidad e historial de cambios. |
| `CLAUDE.md` | Reglas para Claude dentro del repo: privacidad, commits, nunca enviar. |

### Lo que NO está en el repo (y dónde vive)

| Qué | Dónde |
|---|---|
| Perfil real | `config/perfil.yaml` (ignorado por git) y copia en el proyecto de Claude. |
| Hojas de vida y cartas | `cvs/` (ignorado). |
| Histórico, vacantes, crudos, afiches, rankings, lista de personas | `datos/` (ignorado). El histórico también va al proyecto de Claude. |
| Claves y sesiones | `.env`, `secretos/` (ignorados). |

---

## Privacidad y uso responsable

- Este repositorio **no guarda datos personales**: ni teléfonos, ni correos personales, ni
  hojas de vida, ni el histórico, ni nombres de reclutadores.
- **Siempre borradores.** Una persona revisa y envía.
- Un correo por vacante real, a la dirección publicada para postular.
- La lista de personas para conectar es una **sugerencia**. Seguir o conectar lo hace la
  persona, a mano y de a pocos.
- Automatizar LinkedIn va contra sus términos. El modo con sesión usa pocas consultas,
  pausas largas y rotación, y se detiene si LinkedIn limita.

Detalles en [docs/PRIVACIDAD_Y_BUENAS_PRACTICAS.md](docs/PRIVACIDAD_Y_BUENAS_PRACTICAS.md).

## Licencia

MIT.
