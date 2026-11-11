"""Fuentes de vacantes.

- `navegador`: arma las URLs de búsqueda y el script JS para que un asistente
  (o una persona) los ejecute en su navegador.
- `google`: busca posts públicos con una API de búsqueda (Serper). No usa la
  sesión de LinkedIn. Es la fuente por defecto del modo nocturno.
- `linkedin`: Playwright con la sesión de LinkedIn. APAGADO por defecto: va
  contra los términos de uso de LinkedIn y puede bloquear la cuenta.
"""
