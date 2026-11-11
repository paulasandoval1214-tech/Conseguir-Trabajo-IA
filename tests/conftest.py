import json
from pathlib import Path

import pytest

from buscador_empleo.config import cargar_perfil
from buscador_empleo.modelos import PostCrudo

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture
def perfil():
    return cargar_perfil(RAIZ / "config" / "perfil.example.yaml")


@pytest.fixture
def posts():
    datos = json.loads((RAIZ / "tests" / "fixtures" / "posts_ejemplo.json").read_text(encoding="utf-8"))
    return [PostCrudo.desde_dict(d) for d in datos]
