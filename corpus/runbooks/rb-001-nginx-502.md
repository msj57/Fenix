---
title: "Diagnóstico de 502 Bad Gateway en nginx"
doc_type: runbook
lang: es
services: [nginx, webapp]
---

## Síntomas

- La web pública devuelve `502 Bad Gateway` de forma intermitente o constante.
- Alertas de healthcheck fallando en `webapp`.
- En los logs de acceso de nginx aparecen respuestas 502 con upstream `webapp:8000`.

## Diagnóstico

1. Confirmar el estado de los servicios:

   ```bash
   docker compose ps nginx webapp
   ```

2. Revisar los logs de error de nginx; el patrón típico indica a qué upstream no llega:

   ```bash
   docker compose logs --tail 100 nginx | grep -E "connect\(\) failed|upstream"
   ```

   - `connect() failed (111: Connection refused)` → el proceso de webapp no escucha (caído o reiniciando).
   - `upstream timed out (110)` → webapp acepta conexiones pero no responde a tiempo (ver rb-002 si hay sospecha de base de datos).

3. Comprobar la webapp directamente, saltándose nginx:

   ```bash
   curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/healthz
   ```

4. Si la webapp está caída, revisar sus últimos logs antes de la caída:

   ```bash
   docker compose logs --tail 50 webapp
   ```

## Resolución

- Webapp caída o colgada: reiniciar el servicio y vigilar el arranque.

  ```bash
  docker compose restart webapp
  ```

- Configuración de nginx corrupta (tras un cambio reciente): validar y recargar.

  ```bash
  docker compose exec nginx nginx -t && docker compose exec nginx nginx -s reload
  ```

- Si el 502 reaparece a los pocos minutos, no insistir con reinicios: buscar la causa raíz aguas abajo (pool de conexiones, memoria) antes de tocar nada más.

## Verificación

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/        # esperado: 200
docker compose ps --format '{{.Name}} {{.Status}}' | grep -i healthy
```

El incidente se considera cerrado tras 10 minutos sin nuevos 502 en los logs de nginx.
