---
title: "nginx devuelve 503 por límite de tasa (rate limiting)"
doc_type: runbook
lang: es
services: [nginx, webapp]
---

## Síntomas

- Picos de respuestas `503 Service Temporarily Unavailable` correlacionados con tráfico alto.
- En los logs de nginx: `limiting requests, excess: ... by zone`.
- Usuarios legítimos afectados durante campañas o picos, no de forma constante.

## Diagnóstico

1. Confirmar que el 503 viene del `limit_req` de nginx y no de la webapp caída:

   ```bash
   docker compose logs --tail 200 nginx | grep -E "limiting requests|delaying request"
   ```

2. Revisar la zona y el rate configurados:

   ```bash
   docker compose exec nginx grep -E "limit_req_zone|limit_req " /etc/nginx/nginx.conf
   ```

3. Comprobar si el pico es tráfico legítimo o abuso (una sola IP dominando):

   ```bash
   docker compose exec nginx awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head
   ```

## Resolución

- Si es abuso de una IP concreta, mantener el límite y bloquear el origen.
- Si es tráfico legítimo infraestimado, subir `rate` y `burst` con criterio y recargar:

  ```bash
  docker compose exec nginx nginx -t && docker compose exec nginx nginx -s reload
  ```

- Causa raíz: límites calibrados para tráfico normal sin contemplar picos previstos
  (campañas). Documentar los picos esperados y dimensionar la zona en consecuencia.

## Verificación

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/   # esperado: 200
docker compose logs --since 5m nginx | grep -c "limiting requests"  # debe tender a 0
```
