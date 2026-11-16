# Hashtags para encontrar vacantes

Buscar por hashtag trae publicaciones que no salen con palabras clave. Muchas empresas
y reclutadoras ponen el cargo y el correo **en un afiche** y en el texto solo dejan
`#VacantesBogotá #OfertaLaboral`. Esta página es la lista curada de qué hashtags usar
por línea de búsqueda. Se afina con evidencia, no a ojo.

## Cómo se usan

En `config/perfil.yaml`:

```yaml
busqueda:
  hashtags_generales: ["#vacantesbogota", "#ofertalaboral", "#empleobogota", "#trabajosihay"]
lineas:
  datos:
    hashtags: ["#analistadedatos", "#powerbi", "#dataanalytics", "#peopleanalytics"]
  gestion_humana:
    hashtags: ["#talentohumano", "#gestionhumana", "#recursoshumanos", "#seleccion"]
```

- `python -m buscador_empleo consultas --tipo hashtag` muestra las URLs.
  Un hashtag se busca como una palabra: `keywords=%23vacantesbogota`, última semana, orden
  por relevancia.
- `python -m buscador_empleo consultas --hoy 6` elige las 6 de hoy **en rotación**: la
  siguiente sesión sigue donde quedó esta. Así no se gastan siempre las mismas búsquedas.
- Los hashtags generales traen de todo (meseros, conductores, otras ciudades). Eso está
  bien: `importar` filtra por línea, ciudad, país, inglés y experiencia.

## Cómo se afina (con datos)

```bash
python -m buscador_empleo -p config/perfil.yaml hashtags                    # ranking en datos/hashtags_ranking.md
python -m buscador_empleo -p config/perfil.yaml hashtags --actualizar-doc   # además reescribe la tabla de abajo
```

El comando lee todo lo ya extraído (`datos/crudo/*.json` y `datos/vacantes_*.json`) y pasa
cada post por las mismas reglas de `importar`. Por hashtag cuenta:

- **Posts vistos**: cuántos posts lo traían.
- **Con correo**: cuántos traían un correo de postulación.
- **Útiles**: cuántos dejaron al menos una vacante que pasa los filtros. Se cuentan
  también las ya postuladas, porque prueban que el hashtag sirve.
- Una columna por línea, y la **tasa útil** (útiles / posts).

Reglas para mover un hashtag de lista:

| Situación (después de 2 semanas usándolo) | Acción |
|---|---|
| ≥ 2 útiles y tasa ≥ 30 % | **Usar**: dejarlo en el perfil. |
| Útiles en una sola línea | Moverlo a `hashtags:` de esa línea, no a los generales. |
| ≥ 10 posts y 0 útiles | **Evitar**: quitarlo del perfil y anotarlo abajo. |
| Lo usan sobre todo otros países | **Evitar** (ya lo filtra el país, pero gasta búsquedas). |

## Lista curada

Estado: ✅ probado con datos propios · 🧪 por probar · ⛔ evitar.

### Generales (cualquier línea, Bogotá / Colombia)

| Hashtag | Estado | Nota |
|---|---|---|
| #vacantesbogota | ✅ | Útil en gestión humana (2/2 al 16-nov). |
| #ofertalaboral | ✅ | 3/3 útiles al 16-nov. Muy usado por empresas medianas. |
| #empleo | ✅ | Amplio. 4 de 5 útiles, pero mezcla países. |
| #bogota | ✅ | Igual que #empleo: sirve para confirmar ciudad. |
| #empleobogota | 🧪 | |
| #trabajosihay | 🧪 | Lo propuso Miguel; medir en las próximas sesiones. |
| #vacante | 🧪 | 2 de 3 útiles al 16-nov. |
| #estamoscontratando / #hiring | 🧪 | Mucho en inglés y de otros países. |
| #trabajoenbogota | 🧪 | |

### Datos / Power BI

| Hashtag | Estado | Nota |
|---|---|---|
| #analistadedatos | ✅ | 2/2 útiles al 16-nov. |
| #powerbi | ✅ | 2/2. También trae cursos y tutoriales: el filtro los descarta (no traen correo). |
| #dataanalytics | ✅ | 2/2. |
| #peopleanalytics | 🧪 | Mezcla datos y gestión humana: justo el perfil híbrido. |
| #businessintelligence | 🧪 | |
| #analisisdedatos | 🧪 | |

### Gestión humana

| Hashtag | Estado | Nota |
|---|---|---|
| #talentohumano | ✅ | 3 de 5 útiles. |
| #recursoshumanos | ✅ | 2/2. |
| #seleccion | ✅ | 2/2. |
| #gestionhumana | ✅ | 2 de 4. |
| #auxiliardetalentohumano | ✅ | Cargos técnicos (por debajo del perfil, pero responden). |
| #reclutamiento | 🧪 | |
| #psicologia | 🧪 | Trae mucha clínica. Probar combinado con "selección". |

### Evitar

| Hashtag | Por qué |
|---|---|
| #empleoecuador, #trabajoenatlantico, #empleomedellin | Otros países o ciudades. |
| #globalrecruiting, #internationalrecruiting, #talentacquisition | Reclutamiento internacional en inglés: 0 útiles. |
| #opentowork, #buscoempleo | Son personas buscando empleo, no vacantes. |
| #somos<empresa> (p. ej. de un banco) | Hashtag de marca: sirve una vez, no como búsqueda. |

## Ranking actual (generado)

Esta tabla la escribe `hashtags --actualizar-doc`; no la edites a mano. Solo trae
conteos, no correos ni nombres.

<!-- ranking:inicio -->
_Actualizado 2026-11-16 con 140 posts extraídos._

| Hashtag | Posts vistos | Con correo | Útiles | datos | gestion_humana | Tasa útil |
|---|---|---|---|---|---|---|
| #bogotá | 5 | 5 | 4 | 1 | 3 | 80 % |
| #empleo | 5 | 5 | 4 | 1 | 3 | 80 % |
| #ofertalaboral | 3 | 3 | 3 | 0 | 3 | 100 % |
| #talentohumano | 5 | 5 | 3 | 0 | 3 | 60 % |
| #analistadedatos | 2 | 2 | 2 | 2 | 0 | 100 % |
| #auxiliardetalentohumano | 2 | 2 | 2 | 0 | 2 | 100 % |
| #dataanalytics | 2 | 2 | 2 | 2 | 0 | 100 % |
| #powerbi | 2 | 2 | 2 | 2 | 0 | 100 % |
| #recursoshumanos | 2 | 2 | 2 | 0 | 2 | 100 % |
| #selección | 2 | 2 | 2 | 0 | 2 | 100 % |
| #vacantesbogotá | 2 | 2 | 2 | 0 | 2 | 100 % |
| #vacante | 3 | 3 | 2 | 1 | 1 | 67 % |
| #gestiónhumana | 4 | 4 | 2 | 0 | 2 | 50 % |
| #ecuador | 2 | 2 | 0 | 0 | 0 | 0 % |
| #empleocolombia | 2 | 2 | 0 | 0 | 0 | 0 % |
| #globalrecruiting | 2 | 2 | 0 | 0 | 0 | 0 % |
| #internationalrecruiting | 2 | 2 | 0 | 0 | 0 | 0 % |
| #somosavanz | 2 | 2 | 0 | 0 | 0 | 0 % |
| #somosgrupopellas | 2 | 2 | 0 | 0 | 0 | 0 % |
| #talentacquisition | 2 | 2 | 0 | 0 | 0 | 0 % |
| #trabajoenatlántico | 2 | 2 | 0 | 0 | 0 | 0 % |
<!-- ranking:fin -->
