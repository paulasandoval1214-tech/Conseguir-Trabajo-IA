"""Buscador de vacantes con correo de postulación y generador de borradores.

Pensado para dos modos de uso:
- Herramienta para un asistente de IA (Claude) dentro de un chat: el asistente
  extrae posts con un script de navegador y este paquete hace el trabajo
  pesado (limpiar, filtrar, deduplicar, redactar) sin gastar tokens.
- Ejecución local y desatendida (por ejemplo, todas las noches en Windows).
"""

__version__ = "0.1.0"
