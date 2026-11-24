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
_Actualizado 2026-11-23 con 575 posts extraídos._

| Hashtag | Posts vistos | Con correo | Útiles | datos | gestion_humana | riesgo_operacional | Tasa útil |
|---|---|---|---|---|---|---|---|
| #ofertalaboral | 45 | 45 | 18 | 7 | 11 | 0 | 40 % |
| #talentohumano | 63 | 63 | 18 | 4 | 14 | 0 | 28 % |
| #powerbi | 31 | 31 | 17 | 14 | 0 | 3 | 55 % |
| #bogotá | 50 | 50 | 16 | 5 | 10 | 1 | 32 % |
| #empleobogotá | 45 | 45 | 14 | 4 | 7 | 3 | 31 % |
| #empleo | 48 | 47 | 12 | 5 | 6 | 1 | 25 % |
| #oportunidadlaboral | 49 | 49 | 11 | 5 | 6 | 0 | 22 % |
| #businessintelligence | 14 | 14 | 10 | 10 | 0 | 0 | 71 % |
| #estamoscontratando | 35 | 35 | 9 | 3 | 6 | 0 | 26 % |
| #dataanalytics | 12 | 12 | 8 | 8 | 0 | 0 | 67 % |
| #sql | 12 | 12 | 8 | 8 | 0 | 0 | 67 % |
| #recursoshumanos | 19 | 19 | 7 | 0 | 7 | 0 | 37 % |
| #python | 7 | 7 | 6 | 6 | 0 | 0 | 86 % |
| #analíticadedatos | 5 | 5 | 5 | 5 | 0 | 0 | 100 % |
| #excelavanzado | 5 | 5 | 4 | 3 | 1 | 0 | 80 % |
| #selección | 8 | 7 | 4 | 0 | 4 | 0 | 50 % |
| #analistadedatos | 9 | 9 | 4 | 4 | 0 | 0 | 44 % |
| #medellín | 11 | 11 | 4 | 1 | 2 | 1 | 36 % |
| #vacantesbogota | 13 | 13 | 4 | 0 | 4 | 0 | 31 % |
| #gestiónhumana | 14 | 14 | 4 | 0 | 4 | 0 | 28 % |
| #empleocolombia | 19 | 19 | 4 | 1 | 2 | 1 | 21 % |
| #automatización | 3 | 3 | 3 | 1 | 2 | 0 | 100 % |
| #datascience | 3 | 3 | 3 | 3 | 0 | 0 | 100 % |
| #hiringnow | 4 | 4 | 3 | 1 | 1 | 1 | 75 % |
| #oportunidadeslaborales | 9 | 9 | 3 | 0 | 3 | 0 | 33 % |
| #vacante | 22 | 22 | 3 | 2 | 1 | 0 | 14 % |
| #trabajosihay | 24 | 24 | 3 | 0 | 2 | 1 | 12 % |
| #aiengineer | 2 | 2 | 2 | 2 | 0 | 0 | 100 % |
| #analistadebienestar | 2 | 2 | 2 | 0 | 2 | 0 | 100 % |
| #análisisfinanciero | 2 | 2 | 2 | 2 | 0 | 0 | 100 % |
| #atracción | 2 | 2 | 2 | 0 | 2 | 0 | 100 % |
| #auxiliardetalentohumano | 2 | 2 | 2 | 0 | 2 | 0 | 100 % |
| #dataanalyst | 2 | 2 | 2 | 2 | 0 | 0 | 100 % |
| #datalake | 2 | 2 | 2 | 2 | 0 | 0 | 100 % |
| #dentisalud | 2 | 2 | 2 | 2 | 0 | 0 | 100 % |
| #generativeai | 2 | 2 | 2 | 2 | 0 | 0 | 100 % |
| #gobiernodedatos | 2 | 2 | 2 | 1 | 0 | 1 | 100 % |
| #growthmarketing | 2 | 2 | 2 | 2 | 0 | 0 | 100 % |
| #hagamosequipo | 2 | 2 | 2 | 2 | 0 | 0 | 100 % |
| #iagenerativa | 2 | 2 | 2 | 2 | 0 | 0 | 100 % |
<!-- ranking:fin -->
