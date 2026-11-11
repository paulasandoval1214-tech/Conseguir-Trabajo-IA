# Privacidad y buenas prácticas

## Qué nunca va al repositorio

- Teléfonos, correos personales, direcciones, documentos de identidad.
- Hojas de vida, cartas, fotos (`cvs/`, `*.pdf`, `*.docx`).
- El perfil real (`config/perfil.yaml`) y el histórico (`datos/`).
- Credenciales y tokens (`secretos/`, `.env`, `credentials*.json`, `token*.json`).

Todo eso está en `.gitignore`. Antes de cada commit:

```bash
git status            # que no aparezca nada de lo anterior
git diff --cached | grep -nE "[0-9]{3}[ -]?[0-9]{3}[ -]?[0-9]{4}|@[a-z0-9-]+\.(com|co|org)"
```

Los datos de ejemplo de `tests/` usan dominios ficticios (`*-ejemplo.com`).

## Identidad de los commits

Los commits llevan el nombre de la persona dueña del proyecto y un correo `noreply` de GitHub,
para no exponer un correo personal:

```bash
git config user.name "Miguel Muñoz"
git config user.email "<ID>+<usuario>@users.noreply.github.com"
```

## Uso responsable

- **Un correo por vacante real**, a la dirección publicada para postular, con el CV que
  corresponde. Nada de listas de correos ni envíos a quien no publicó una vacante.
- Siempre borradores; una persona revisa y envía.
- No se recolectan perfiles de personas ni se escribe por mensaje directo.
- LinkedIn con sesión automatizada: apagado por defecto (riesgo de bloqueo de cuenta).
- Si alguien pide no recibir más correos, se marca "Descartada" en el histórico y no se vuelve a
  escribir.
