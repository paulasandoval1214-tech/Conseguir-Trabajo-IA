# Instalación en Windows (modo local / nocturno)

## 1. Requisitos

- Python 3.10 o superior (en la instalación marca "Add Python to PATH").
- Git (opcional, para actualizar el repo).

## 2. Instalar

```powershell
git clone <url-del-repo>
cd Conseguir-Trabajo-IA
powershell -ExecutionPolicy Bypass -File scripts\instalar.ps1
```

Esto:

- crea `.venv` e instala las dependencias (Gmail, Claude, OCR y Playwright),
- instala Chromium para Playwright,
- instala **Tesseract OCR** con `winget` (si no estaba) y descarga los idiomas español e
  inglés en `herramientas\tessdata` (no necesita permisos de administrador),
- copia `config\perfil.yaml` y `.env` de ejemplo.

Opciones: `-SinLinkedIn` (sin Playwright) y `-SinOCR` (sin lectura de afiches).

## 3. Tu perfil y tus CV

1. Edita `config\perfil.yaml`: nombre, correo de envío, ciudad, años de experiencia, nivel de
   inglés y, sobre todo, las **líneas** (palabras clave, consultas y frase de experiencia).
2. Pon tus hojas de vida en PDF en `cvs\` con los mismos nombres del perfil
   (por defecto `CV_Datos.pdf` y `CV_Gestion_Humana.pdf`).
3. Ajusta las plantillas de `plantillas\` si quieres otro tono.

## 4. Gmail API (para crear borradores con adjunto)

1. Entra a https://console.cloud.google.com/ con la cuenta de Gmail que enviará los correos.
2. Crea un proyecto (p. ej. "conseguir-trabajo").
3. *APIs y servicios → Biblioteca* → habilita **Gmail API**.
4. *Pantalla de consentimiento OAuth* → tipo **Externo** → agrega tu correo como **usuario de
   prueba**.
5. *Credenciales → Crear credenciales → ID de cliente OAuth → App de escritorio*.
6. Descarga el JSON y guárdalo como `secretos\credentials.json`.
7. Primera prueba (abre el navegador para autorizar; después queda `secretos\token.json`):

```powershell
.\.venv\Scripts\python.exe -m buscador_empleo adjuntar --simular
```

Permisos que pide: crear/editar borradores y leer correo (para firma y respuestas). **No** pide
permiso de envío.

## 5. Búsqueda en Google (Serper)

1. Crea cuenta en https://serper.dev (trae créditos gratis).
2. Copia la API key en `.env`: `SERPER_API_KEY=...`

## 6. Filtro con IA (opcional)

1. Crea una API key en https://console.anthropic.com
2. En `.env`: `ANTHROPIC_API_KEY=...`
3. En el perfil: `ia.usar: true`. Usa Claude Haiku: centavos por noche.

## 7. Lectura de afiches (OCR)

Muchas vacantes traen el correo solo dentro de la imagen. Con `imagenes.usar: true` en el
perfil, la noche lee esos afiches.

- `instalar.ps1` ya deja Tesseract. Si `winget` falló, instálalo a mano desde
  https://github.com/UB-Mannheim/tesseract/wiki. El código lo busca solo en
  `C:\Program Files\Tesseract-OCR\`. Si lo instalaste en otro lado, pon la ruta en
  `imagenes.tesseract_cmd`.
- Si el OCR no encuentra un correo, se usa Claude Haiku (necesita `ANTHROPIC_API_KEY`), con
  un tope de `max_ia_por_ejecucion` imágenes por noche.
- Prueba manual con lo último que se extrajo: doble clic en `scripts\leer_afiches.bat`.

## 8. LinkedIn desde el PC

1. En el perfil: `busqueda.linkedin_con_sesion: true`.
2. Doble clic **una vez** en `scripts\iniciar_sesion_linkedin.bat`. Se abre un navegador:
   inicia sesión con la cuenta de la candidata y presiona Enter en la ventana negra. La
   sesión queda en `secretos\perfil_navegador\`; la contraseña no se guarda.
3. Cada noche se visitan el feed y hasta `max_consultas_linkedin` búsquedas (máximo 8),
   **en rotación**, con pausas de 25–60 s. Si LinkedIn responde "No se han encontrado
   resultados" dos veces seguidas, se detiene solo.
4. Si LinkedIn cierra la sesión, la noche lo avisa en el log y sigue con Gmail y Google.
   Repite el paso 2.

Riesgo: automatizar LinkedIn va contra sus términos y puede llevar a un bloqueo. Por eso van
pocas consultas, con pausas y rotación, y se detiene ante el primer síntoma de límite.

## 9. Personas para conectar y hashtags

Cada noche se actualizan:

- `datos\personas_para_conectar.csv` (y `.md`): quién publica vacantes que encajan. Doble
  clic en `scripts\personas_para_conectar.bat` para abrirlo. Marca la columna `estado`
  (Seguido / Conectado / Descartar) y la siguiente noche se respeta. Seguir o conectar se
  hace a mano en LinkedIn, de a 10–15 por día.
- `datos\hashtags_ranking.md`: qué hashtags traen vacantes útiles. Ver `docs\HASHTAGS.md`.

## 10. Programar cada noche

```powershell
powershell -ExecutionPolicy Bypass -File scripts\programar_tarea.ps1 -Hora "21:30"
```

Cada mañana revisa la carpeta **Borradores** de Gmail, `datos\reporte_FECHA.md` y el log
`datos\logs\noche_FECHA.log`. El computador debe estar encendido y con la sesión de
Windows iniciada a esa hora, porque Playwright abre un navegador visible.

## Uso combinado con Claude

Si Claude dejó borradores desde el chat (sin adjunto), haz doble clic en
`scripts\adjuntar_cvs.bat`: agrega el CV correcto y tu firma a cada borrador sin adjunto.

## Actualizar el repo

```powershell
git pull
powershell -ExecutionPolicy Bypass -File scripts\instalar.ps1   # instala lo nuevo, no toca tu perfil
```

Después de actualizar, compara `config\perfil.example.yaml` con tu `config\perfil.yaml`.
Las secciones nuevas (p. ej. `imagenes:`, `hashtags:`) hay que copiarlas a mano.
