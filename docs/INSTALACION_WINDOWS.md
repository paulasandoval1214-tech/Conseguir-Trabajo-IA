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

Esto crea `.venv`, instala dependencias y copia `config\perfil.yaml` y `.env` de ejemplo.

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

## 7. Programar cada noche

```powershell
powershell -ExecutionPolicy Bypass -File scripts\programar_tarea.ps1 -Hora "21:30"
```

Cada mañana revisa la carpeta **Borradores** de Gmail y `datos\reporte_FECHA.md`.

## Uso combinado con Claude

Si Claude dejó borradores desde el chat (sin adjunto), haz doble clic en
`scripts\adjuntar_cvs.bat`: agrega el CV correcto y tu firma a cada borrador sin adjunto.

## Modo LinkedIn con sesión (no recomendado)

Va contra los términos de LinkedIn y puede bloquear la cuenta. Si aun así lo quieres:

```powershell
.\.venv\Scripts\python.exe -m pip install playwright
.\.venv\Scripts\python.exe -m playwright install chromium
```

y en el perfil `busqueda.linkedin_con_sesion: true` (máx. 8 consultas, pausas de 25–60 s).
