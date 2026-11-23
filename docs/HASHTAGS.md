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
_Actualizado 2026-11-22 con 440 posts extraídos._

| Hashtag | Posts vistos | Con correo | Útiles | datos | gestion_humana | riesgo_operacional | Tasa útil |
|---|---|---|---|---|---|---|---|
| #powerbi | 19 | 19 | 11 | 9 | 0 | 2 | 57 % |
| #ofertalaboral | 30 | 30 | 11 | 4 | 7 | 0 | 37 % |
| #bogotá | 34 | 34 | 11 | 3 | 8 | 0 | 32 % |
| #talentohumano | 46 | 46 | 11 | 3 | 8 | 0 | 24 % |
| #empleo | 33 | 33 | 8 | 3 | 5 | 0 | 24 % |
| #recursoshumanos | 15 | 15 | 7 | 0 | 7 | 0 | 47 % |
| #oportunidadlaboral | 37 | 37 | 7 | 5 | 2 | 0 | 19 % |
| #estamoscontratando | 29 | 29 | 6 | 3 | 3 | 0 | 21 % |
| #businessintelligence | 8 | 8 | 5 | 5 | 0 | 0 | 62 % |
| #empleobogotá | 22 | 22 | 5 | 2 | 1 | 2 | 23 % |
| #dataanalytics | 6 | 6 | 4 | 4 | 0 | 0 | 67 % |
| #selección | 6 | 6 | 4 | 0 | 4 | 0 | 67 % |
| #analíticadedatos | 3 | 3 | 3 | 3 | 0 | 0 | 100 % |
| #automatización | 3 | 3 | 3 | 1 | 2 | 0 | 100 % |
| #python | 3 | 3 | 3 | 3 | 0 | 0 | 100 % |
| #analistadedatos | 4 | 4 | 3 | 3 | 0 | 0 | 75 % |
| #excelavanzado | 4 | 4 | 3 | 3 | 0 | 0 | 75 % |
| #medellín | 9 | 9 | 3 | 1 | 2 | 0 | 33 % |
| #vacante | 17 | 17 | 3 | 2 | 1 | 0 | 18 % |
| #aiengineer | 2 | 2 | 2 | 2 | 0 | 0 | 100 % |
| #atracción | 2 | 2 | 2 | 0 | 2 | 0 | 100 % |
| #auxiliardetalentohumano | 2 | 2 | 2 | 0 | 2 | 0 | 100 % |
| #datascience | 2 | 2 | 2 | 2 | 0 | 0 | 100 % |
| #dentisalud | 2 | 2 | 2 | 2 | 0 | 0 | 100 % |
| #generativeai | 2 | 2 | 2 | 2 | 0 | 0 | 100 % |
| #growthmarketing | 2 | 2 | 2 | 2 | 0 | 0 | 100 % |
| #hagamosequipo | 2 | 2 | 2 | 2 | 0 | 0 | 100 % |
| #iagenerativa | 2 | 2 | 2 | 2 | 0 | 0 | 100 % |
| #lappiz | 2 | 2 | 2 | 2 | 0 | 0 | 100 % |
| #operativos | 2 | 2 | 2 | 0 | 2 | 0 | 100 % |
| #powerautomate | 2 | 2 | 2 | 0 | 2 | 0 | 100 % |
| #procesos | 2 | 2 | 2 | 0 | 0 | 2 | 100 % |
| #rag | 2 | 2 | 2 | 2 | 0 | 0 | 100 % |
| #reclutando | 2 | 2 | 2 | 0 | 2 | 0 | 100 % |
| #rpa | 2 | 2 | 2 | 0 | 2 | 0 | 100 % |
| #teknei | 2 | 2 | 2 | 2 | 0 | 0 | 100 % |
| #vacanteactiva | 2 | 2 | 2 | 0 | 0 | 2 | 100 % |
| #alimentos | 3 | 3 | 2 | 0 | 2 | 0 | 67 % |
| #hiringnow | 3 | 3 | 2 | 0 | 1 | 1 | 67 % |
| #sql | 3 | 3 | 2 | 2 | 0 | 0 | 67 % |
<!-- ranking:fin -->
