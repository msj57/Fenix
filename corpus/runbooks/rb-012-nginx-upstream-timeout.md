---
title: "nginx upstream timed out (504) hacia la webapp"
doc_type: runbook
lang: es
services: [nginx, webapp]
---

## Síntomas

- La web devuelve `504 Gateway Timeout` en endpoints concretos, no en todos.
- En los logs de nginx: `upstream timed out (110: Connection timed out) while reading response`.
- Los endpoints rápidos funcionan; los pesados (informes, exportaciones) cortan.

## Diagnóstico

1. Identificar qué ruta agota el timeout:

   ```bash
   docker compose logs --tail 200 nginx | grep "upstream timed out"
   ```

2. Medir cuánto tarda realmente la webapp en esa ruta, saltándose nginx:

   ```bash
   curl -s -o /dev/null -w "%{time_total}s\n" http://localhost:8000/reports/monthly
   ```

3. Comparar con `proxy_read_timeout` (por defecto 60 s):

   ```bash
   docker compose exec nginx grep -E "proxy_read_timeout|proxy_connect_timeout" /etc/nginx/nginx.conf
   ```

## Resolución

- Mitigación: subir el timeout solo de la ruta lenta (no global), y recargar:

  ```bash
  docker compose exec nginx nginx -t && docker compose exec nginx nginx -s reload
  ```

- Fondo: mover el trabajo pesado a un job asíncrono con aviso, para no depender de
  timeouts del proxy. Subir el timeout global esconde lentitud real aguas abajo.

## Verificación

```bash
curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" http://localhost:8080/reports/monthly
```

Cerrar cuando la ruta responda dentro del timeout o se haya movido a asíncrono.
