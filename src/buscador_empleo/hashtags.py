"""¿Qué hashtags traen vacantes útiles? Ranking a partir de lo que ya se extrajo.

Por qué existe
--------------
Buscar por hashtag (#trabajosihay, #vacantesbogota…) trae mucho volumen, pero no todos
sirven igual. En vez de adivinar, este módulo mira los posts ya guardados en
`datos/crudo/*.json`, pasa cada uno por las mismas reglas de `importar` y cuenta, por
hashtag, cuántos posts trajo y cuántos terminaron en una vacante aceptada para cada línea.

El resultado se usa para afinar `docs/HASHTAGS.md` (la lista curada, pública) y la lista
`hashtags:` de cada línea en el perfil.

Uso:
    python -m buscador_empleo -p config/perfil.yaml hashtags              # imprime y guarda datos/hashtags_ranking.md
    python -m buscador_empleo -p config/perfil.yaml hashtags --actualizar-doc   # además reescribe la tabla de docs/HASHTAGS.md
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

from . import filtros
from .config import RAIZ, Perfil
from .extraccion import normalizar, post_a_vacantes
from .modelos import PostCrudo

RE_HASHTAG = re.compile(r"#[\wÀ-ÿ]{3,}")
MARCA_INICIO = "<!-- ranking:inicio -->"
MARCA_FIN = "<!-- ranking:fin -->"
DOC = RAIZ / "docs" / "HASHTAGS.md"


def hashtags_de(post: PostCrudo) -> list[str]:
    """Hashtags del post (los que trae el extractor nuevo o, si no, los del texto)."""
    crudos = post.hashtags or RE_HASHTAG.findall(post.texto)
    return list(dict.fromkeys(h.lower() for h in crudos))


def _clave(h: str) -> str:
    return normalizar(h).lstrip("#")


def analizar(posts: list[PostCrudo], perfil: Perfil, minimo_posts: int = 1) -> list[dict]:
    """Devuelve filas ordenadas por utilidad.

    Cada fila: {"hashtag", "posts", "con_correo", "utiles", "por_linea": {linea: n}, "tasa"}.
    "utiles" = posts con al menos una vacante que pasa los filtros (sin mirar el historial:
    una vacante ya postulada también prueba que el hashtag sirve).
    """
    forma: dict[str, Counter] = defaultdict(Counter)
    filas: dict[str, dict] = {}
    for p in posts:
        tags = hashtags_de(p)
        if not tags:
            continue
        vs = post_a_vacantes(p, perfil.correos_ignorar)
        lineas_ok = set()
        for v in vs:
            v.linea, v.puntaje = filtros.clasificar_linea(v, perfil)
            if not filtros.motivo_descarte(v, perfil, set()):
                lineas_ok.add(v.linea)
        for h in tags:
            k = _clave(h)
            forma[k][h] += 1
            f = filas.setdefault(k, {"posts": 0, "con_correo": 0, "utiles": 0, "por_linea": Counter()})
            f["posts"] += 1
            f["con_correo"] += 1 if vs else 0
            if lineas_ok:
                f["utiles"] += 1
                f["por_linea"].update(lineas_ok)
    salida = []
    for k, f in filas.items():
        if f["posts"] < minimo_posts:
            continue
        salida.append({
            "hashtag": forma[k].most_common(1)[0][0],
            "posts": f["posts"], "con_correo": f["con_correo"], "utiles": f["utiles"],
            "por_linea": dict(f["por_linea"]), "tasa": round(f["utiles"] / f["posts"], 2),
        })
    return sorted(salida, key=lambda r: (-r["utiles"], -r["tasa"], -r["posts"], r["hashtag"]))


def tabla_markdown(filas: list[dict], perfil: Perfil, maximo: int = 40) -> str:
    lineas = list(perfil.lineas)
    cab = "| Hashtag | Posts vistos | Con correo | Útiles | " + " | ".join(lineas) + " | Tasa útil |"
    sep = "|---|---|---|---|" + "---|" * len(lineas) + "---|"
    cuerpo = [
        f"| {r['hashtag']} | {r['posts']} | {r['con_correo']} | {r['utiles']} | "
        + " | ".join(str(r["por_linea"].get(l, 0)) for l in lineas)
        + f" | {int(r['tasa'] * 100)} % |"
        for r in filas[:maximo]
    ]
    return "\n".join([cab, sep, *cuerpo])


def actualizar_doc(tabla: str, fecha: str, n_posts: int, doc: Path = DOC) -> bool:
    """Reemplaza la tabla entre las marcas de docs/HASHTAGS.md. Devuelve True si cambió."""
    if not doc.exists():
        return False
    texto = doc.read_text(encoding="utf-8")
    if MARCA_INICIO not in texto or MARCA_FIN not in texto:
        return False
    nuevo_bloque = (f"{MARCA_INICIO}\n_Actualizado {fecha} con {n_posts} posts extraídos._\n\n"
                    f"{tabla}\n{MARCA_FIN}")
    antes, resto = texto.split(MARCA_INICIO, 1)
    _, despues = resto.split(MARCA_FIN, 1)
    nuevo = antes + nuevo_bloque + despues
    if nuevo != texto:
        doc.write_text(nuevo, encoding="utf-8")
        return True
    return False
