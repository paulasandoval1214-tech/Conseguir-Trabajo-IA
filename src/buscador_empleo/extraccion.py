"""Convierte texto libre de un post de empleo en una `Vacante` estructurada.

Todo es con expresiones regulares: rápido, gratis y suficiente para la
mayoría de posts en español. La IA (opcional) solo se usa después, para los
casos dudosos.
"""

from __future__ import annotations

import re
import unicodedata

from .modelos import PostCrudo, Vacante

RE_CORREO = re.compile(r"(?<![\wÀ-ÿ.%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
RE_EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0000FE0F\U0000200D⭐✅❌✔]"
)

PAISES = {
    "colombia": ["colombia", "bogota", "medellin", "cali", "barranquilla", "cartagena",
                 "bucaramanga", "chia", "cundinamarca", "antioquia", "pereira", "yumbo"],
    "ecuador": ["ecuador", "quito", "guayaquil", "samborondon", "cuenca"],
    "peru": ["peru", "lima"],
    "mexico": ["mexico", "cdmx", "monterrey", "guadalajara", "aguascalientes"],
    "venezuela": ["venezuela", "caracas"],
    "chile": ["chile", "santiago de chile"],
    "argentina": ["argentina", "buenos aires"],
    "republica dominicana": ["republica dominicana", "santo domingo", "distrito nacional"],
    "panama": ["panama"],
    "costa rica": ["costa rica"],
    "guatemala": ["guatemala"],
    "espana": ["espana", "madrid", "barcelona"],
}

CIUDADES = ["Bogotá", "Medellín", "Cali", "Barranquilla", "Cartagena", "Bucaramanga",
            "Chía", "Pereira", "Yumbo", "Cajicá", "Zipaquirá", "Funza", "Mosquera", "Soacha",
            "Itagüí", "Envigado", "Rionegro", "Girardot", "Manizales", "Ibagué", "Villavicencio",
            "Valledupar", "Tunja", "Neiva", "Santa Marta", "Cúcuta", "Armenia", "Popayán", "Pasto",
            "Montería", "Sincelejo", "Facatativá", "Tocancipá"]

PALABRAS_CARGO = (
    "analista|profesional|psic[oó]log[oa]|generalista|auxiliar|asistente|coordinador[a]?|"
    "especialista|practicante|reclutador[a]?|ingenier[oa]|cient[ií]fic[oa]|consultor[a]?|"
    "l[ií]der|hrbp|senior|junior|data|business|desarrollador[a]?|t[eé]cnico|tecn[oó]logo|director[a]?|"
    "jefe|gerente|supervisor[a]?|ejecutiv[oa]|controller|administrador[a]?"
)


def normalizar(texto: str) -> str:
    """Minúsculas y sin tildes, para comparar."""
    t = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def limpiar(texto: str) -> str:
    texto = RE_EMOJI.sub(" ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _limpiar_cargo(c: str) -> str:
    c = limpiar(c).replace("#", "")
    c = re.split(r"\s*[(…*\"“”]|\.\.\.", c)[0]
    palabras_may = [w for w in c.split() if w.isalpha()]
    if palabras_may and sum(w.isupper() for w in palabras_may) >= max(2, len(palabras_may) // 2):
        c = " ".join(w.lower() if w.isupper() else w for w in c.split())
    c = re.split(r"\s(?:en|para|con|que|en la ciudad de)\s(?=[A-ZÁÉÍÓÚa-z])|[!?¿¡:|]| - | – ", c)[0]
    c = re.split(r"\s(?:Ubicaci[oó]n|Formaci[oó]n|Requisitos|Salario|Experiencia|Modalidad|Horario|"
                 r"Contrato|Perfil|Funciones|Lugar|Ciudad)\b", c, flags=re.IGNORECASE)[0]
    c = c.strip(" .,-–*\"'“”")
    if c.isupper():
        c = c.lower()
    for ciudad in CIUDADES:  # "Analista X Bogotá" -> "Analista X"
        c = re.sub(rf"\s+{ciudad}$", "", c)
    c = re.sub(r"\b(analista|auxiliar|profesional|asesor|asistente)e?s\b", r"\1", c, flags=re.IGNORECASE)
    palabras = c.split()
    return " ".join(palabras[:9])


RE_FIN_CABECERA = re.compile(
    r"\b\d{1,2}\s*(?:h|d|sem|mes|meses|d[ií]as?|min|a[ñn]os?)\b(?:\s*•\s*Editado)?(?:\s*•)?\s*"
    r"(?:Conectar|Seguir|Unirse|Ver mis servicios)?",
)


def separar_cabecera(texto: str) -> tuple[str, str]:
    """Separa la cabecera del post (nombre + titular del autor) del cuerpo.

    El titular del autor ("Psicóloga | Analista de Reclutamiento") confunde la
    detección del cargo, por eso se quita antes de extraer.
    """
    t = limpiar(texto)
    m = RE_FIN_CABECERA.search(t[:400])
    if m and m.start() > 3:
        return t[: m.end()].strip(), t[m.end():].strip()
    return "", t


def extraer_cargo(texto: str) -> str:
    t = limpiar(texto).replace("#", "")
    patrones = [
        rf"(?:vacante|cargo|posici[oó]n|rol)\s*[:\-–]?\s*((?:{PALABRAS_CARGO})[^.!\n]{{2,80}})",
        rf"(?:buscando|buscamos|b[uú]squeda de|contratando|necesitamos|requiere)\s+"
        rf"(?:a\s+)?(?:un\(a\)|una?\(a\)|un/a|una?|nuestr[oa](?:/a)?|nuestro/a|el/la|la|el)?\s*(?:pr[oó]xim[oa](?:/a)?\s+)?"
        rf"(?:\d+\s+)?((?:{PALABRAS_CARGO})[^.!\n]{{2,80}})",
        rf"\b((?:{PALABRAS_CARGO})\s+(?:de|en|del|jr\.?|junior|senior|sr\.?)\s+[^.!\n]{{3,60}})",
    ]
    for i, p in enumerate(patrones):
        m = re.search(p, t, flags=re.IGNORECASE)
        # El patrón genérico solo vale si el cargo viene en mayúscula inicial
        # ("Analista de ...") y no en medio de una frase ("conocimiento técnico ...").
        if m and i == len(patrones) - 1 and not m.group(1)[0].isupper():
            m = None
        if m:
            cargo = _limpiar_cargo(m.group(1))
            if len(cargo) >= 4:
                return cargo[0].upper() + cargo[1:]
    return ""


def extraer_asunto(texto: str) -> str:
    m = re.search(
        r"asunto(?:\s+obligatorio)?\s*[:：]\s*[\"“']?"
        r"([^\"”'\n#!?¡\U0001F000-\U0001FAFF\u2600-\u27BF]{3,90}?)(?=\.\s|\.$|[\"”'\n#!?¡\U0001F000-\U0001FAFF\u2600-\u27BF]|$)",
        texto, re.IGNORECASE)
    if not m:
        return ""
    asunto = limpiar(m.group(1))
    asunto = re.split(r"\s(?:e indica|indicando|y\s+(?:tu|su)|¡|!)", asunto)[0]
    return asunto.strip(" .,")


def extraer_empresa(texto: str) -> str:
    t = limpiar(texto)
    m = re.search(
        r"\b[Ee]n\s+((?:[A-Z][\w&.\-]*\s?){1,5}?)\s*(?:S\.?A\.?S\.?|S\.?A\.?)?\s*,?\s*"
        r"(?:buscamos|estamos|seguimos|queremos|nos encontramos|tenemos|abrimos)",
        t,
    )
    if m:
        return m.group(1).strip(" ,")
    m = re.search(r"(?:haz parte de|[uú]nete a)\s+((?:[A-Z][\w&.\-]*\s?){1,5})", t, re.IGNORECASE)
    if m and m.group(1)[0].isupper():
        return m.group(1).strip(" ,!")
    # "... Analista de Datos en Medismart!" (descarta ciudades)
    for m in re.finditer(r"\ben\s+([A-Z][\w&.\-]+(?:\s[A-Z][\w&.\-]+){0,3})\s*[!.,]", t):
        nombre = m.group(1).strip()
        no_empresa = {normalizar(c) for c in CIUDADES} | {
            "colombia", "linkedin", "ingenieria", "administracion", "economia", "contaduria",
            "psicologia", "sistemas", "excel", "power", "python", "sql", "ingles"}
        if normalizar(nombre.split()[0]) not in no_empresa and normalizar(nombre) not in no_empresa:
            return nombre
    return ""


def extraer_ciudad(texto: str) -> str:
    n = normalizar(texto)
    for c in CIUDADES:
        if normalizar(c) in n:
            return c
    if re.search(r"\b(remot[oa]|teletrabajo|home ?office|100% virtual)\b", n):
        return "Remoto"
    return ""


def extraer_modalidad(texto: str) -> str:
    n = normalizar(texto)
    if re.search(r"\bhibrid[oa]\b", n):
        return "Híbrido"
    if re.search(r"\b(remot[oa]|teletrabajo|home ?office)\b", n):
        return "Remoto"
    if "presencial" in n:
        return "Presencial"
    return ""


def extraer_salario(texto: str) -> str:
    m = re.search(r"\$\s?\d{1,3}(?:[.,]\d{3})+(?:\s*(?:[-–a]|hasta)\s*\$?\s?\d{1,3}(?:[.,]\d{3})+)?", texto)
    return m.group(0).replace(" ", "") if m else ""


def extraer_anios(texto: str) -> int | None:
    n = normalizar(texto)
    m = re.search(r"(?:minimo|al menos|entre|mas de|desde)?\s*(\d{1,2})\s*(?:a|-|y)?\s*\d{0,2}\s*anos?\s+de\s+experiencia", n)
    if m:
        return int(m.group(1))
    m = re.search(r"experiencia[^.]{0,40}?(?:minima|de)\s*(?:de\s*)?(\d{1,2})\s*anos?", n)
    if m:
        return int(m.group(1))
    return None


def extraer_ingles(texto: str) -> str:
    """Nivel de inglés exigido: "", "intermedio" o "avanzado"."""
    n = normalizar(texto)
    if "bilingue" in n or "bilingual" in n:
        if not re.search(r"bilingue[^.]{0,25}(deseable|plus|no indispensable)", n):
            return "avanzado"
    m = re.search(r"ingles[^.\n]{0,45}", n)
    if not m:
        return ""
    frag = m.group(0)
    if re.search(r"deseable|no indispensable|plus|valorable|opcional", frag):
        return ""
    if re.search(r"\b(c1|c2|b2|avanzado|fluido|nativo)\b", frag):
        return "avanzado"
    if re.search(r"\b(b1|intermedio|conversacional)\b", frag):
        return "intermedio"
    return ""


def detectar_pais(texto: str) -> str:
    n = normalizar(texto)
    encontrados = []
    for pais, claves in PAISES.items():
        for c in claves:
            if re.search(rf"\b{re.escape(c)}\b", n):
                encontrados.append(pais)
                break
    if not encontrados:
        return ""
    # Si menciona Colombia y otro país, se marca el otro (suele ser "#EmpleoQuito").
    otros = [p for p in encontrados if p != "colombia"]
    return otros[0] if otros else "colombia"


DOMINIOS_PUBLICOS = {"gmail", "hotmail", "outlook", "yahoo", "live", "icloud", "protonmail"}
TLD_PAIS = {"ec": "ecuador", "pe": "peru", "mx": "mexico", "ve": "venezuela", "cl": "chile",
            "ar": "argentina", "do": "republica dominicana", "pa": "panama", "cr": "costa rica",
            "gt": "guatemala", "es": "espana", "hn": "honduras", "sv": "el salvador", "us": "", "co": "colombia"}


def empresa_desde_correo(correo: str) -> str:
    """seleccion@empresa-ejemplo.co -> "Empresa Ejemplo" (si el dominio no es un correo público)."""
    dominio = correo.split("@")[-1].lower()
    nombre = dominio.split(".")[0]
    if nombre in DOMINIOS_PUBLICOS:
        return ""
    return nombre.replace("-", " ").title()


def pais_desde_correo(correo: str) -> str:
    return TLD_PAIS.get(correo.rsplit(".", 1)[-1].lower(), "")


def correos_del_post(post: PostCrudo, ignorar: list[str] | None = None) -> list[str]:
    ignorar = [i.lower() for i in (ignorar or [])]
    correos = set(c.strip(".").lower() for c in post.correos)
    correos.update(c.strip(".").lower() for c in RE_CORREO.findall(post.texto))
    salida = []
    for c in sorted(correos):
        if any(c.startswith(i) or c.endswith(i) for i in ignorar):
            continue
        salida.append(c)
    return salida


def post_a_vacantes(post: PostCrudo, ignorar_correos: list[str] | None = None) -> list[Vacante]:
    """Un post puede traer varios correos; se crea una vacante por correo."""
    cabecera, cuerpo = separar_cabecera(post.texto)
    texto = cuerpo or post.texto
    agregador = re.search(r"ofertas ?de ?trabajo|ofertas ?laborales|red de referidos|empleos? colombia",
                          normalizar(post.autor + " " + cabecera[:80]))
    es_pagina_empresa = bool(cabecera) and "•" not in cabecera[:150] and not agregador
    empresa = extraer_empresa(texto) or (limpiar(post.autor)[:60] if es_pagina_empresa else "")
    base = dict(
        cargo=extraer_cargo(texto),
        empresa=empresa,
        ciudad=extraer_ciudad(texto),
        modalidad=extraer_modalidad(texto),
        salario=extraer_salario(texto),
        asunto_exigido=extraer_asunto(post.texto),
        anios_experiencia=extraer_anios(texto),
        ingles_exigido=extraer_ingles(texto),
        pais_detectado=detectar_pais(texto),
        autor=limpiar(post.autor)[:120],
        hace=post.hace,
        url=post.url,
        fuente=post.fuente,
        texto=texto[:3000],
    )
    # Si el cargo quedó pobre pero hay asunto exigido, el asunto suele ser el cargo.
    if base["asunto_exigido"] and len(base["cargo"].split()) <= 1:
        candidato = re.sub(r"^(postulaci[oó]n|hoja de vida|hv)\s*[-–:]\s*", "", base["asunto_exigido"],
                           flags=re.IGNORECASE)
        base["cargo"] = re.split(r"\s[-–]\s", candidato)[0]
    vacantes = []
    for c in correos_del_post(post, ignorar_correos):
        v = Vacante(correo=c, **base)
        v.empresa = v.empresa or empresa_desde_correo(c)
        if not v.pais_detectado or v.pais_detectado == "colombia":
            v.pais_detectado = pais_desde_correo(c) or v.pais_detectado
        vacantes.append(v)
    return vacantes
