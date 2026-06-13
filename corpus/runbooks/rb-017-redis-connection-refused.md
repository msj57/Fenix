---
title: "Redis connection refused: la webapp no conecta con la caché"
doc_type: runbook
lang: es
services: [redis-demo, webapp]
---

## Síntomas

- La webapp registra `Error 111 connecting to redis-demo:6379. Connection refused`.
- Funcionalidades que dependen de caché o sesión fallan, pero las que solo tocan DB siguen.
- Tras un reinicio del host o de Redis, el error aparece de golpe.

## Diagnóstico

1. Confirmar si Redis está vivo:

   ```bash
   docker compose ps redis-demo
   docker compose exec redis-demo redis-cli PING   # esperado: PONG
   ```

2. Si responde, comprobar que la webapp apunta al host/puerto correctos:

   ```bash
   docker compose exec webapp env | grep -E "REDIS_HOST|REDIS_PORT"
   ```

3. Si no responde, ver por qué no arrancó:

   ```bash
   docker compose logs --tail 30 redis-demo
   ```

## Resolución

- Si Redis está caído, levantarlo y vigilar el arranque:

  ```bash
  docker compose up -d redis-demo
  ```

- Si el problema es de configuración (host equivocado), corregir el `.env` y recrear la
  webapp. La webapp debe tolerar Redis ausente degradando (sin caché), no cayendo entera.

## Verificación

```bash
docker compose exec redis-demo redis-cli PING                   # PONG
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/   # esperado: 200
```
