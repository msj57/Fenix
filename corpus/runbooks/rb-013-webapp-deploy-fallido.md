---
title: "Webapp no arranca tras un despliegue (variable de entorno faltante)"
doc_type: runbook
lang: es
services: [webapp]
---

## Síntomas

- Tras un deploy, el contenedor de la webapp queda en `Restarting` o sale inmediatamente.
- Logs con `KeyError`, `pydantic.ValidationError` o `Missing required environment variable`.
- El healthcheck nunca pasa a `healthy`; nginx empieza a dar 502.

## Diagnóstico

1. Leer el error de arranque (suele ser la primera línea tras el reinicio):

   ```bash
   docker compose logs --tail 40 webapp
   ```

2. Comparar las variables de entorno presentes con las que el servicio espera:

   ```bash
   docker compose exec webapp env | grep -E "DB_|REDIS_|SECRET_" | sort
   ```

3. Revisar el diff del `.env` o del compose entre el deploy bueno y el actual.

## Resolución

- Añadir la variable que falta al `.env` y recrear el servicio:

  ```bash
  docker compose up -d --force-recreate webapp
  ```

- Causa raíz: nueva variable obligatoria introducida en el código sin actualizar el
  `.env.example` ni el pipeline de deploy. Toda env var nueva debe ir documentada y
  validada al arranque con un mensaje claro, no con un stacktrace.

## Verificación

```bash
docker compose ps webapp --format '{{.Status}}'                 # esperado: healthy
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/healthz   # esperado: 200
```
