---
title: "Configuración de nginx inválida tras un cambio"
doc_type: runbook
lang: es
services: [nginx, webapp]
---

## Síntomas

- Tras editar la configuración, `nginx -s reload` falla y nginx sigue sirviendo la
  versión anterior, o el contenedor no arranca y queda en `Restarting`.
- En los logs: `nginx: [emerg] ...` señalando fichero y línea (directiva desconocida,
  llave sin cerrar, `upstream` duplicado, `server_name` repetido).
- Si el contenedor estaba parado, la web devuelve `Connection refused` en el puerto 80/443.

## Diagnóstico

1. Validar la sintaxis sin recargar (lo primero, siempre):

   ```bash
   docker compose exec nginx nginx -t
   ```

   La salida `[emerg]` indica el fichero y la línea exacta del error. No hay que adivinar.

2. Si el contenedor no arranca, leer el motivo en sus logs:

   ```bash
   docker compose logs --tail 30 nginx
   ```

3. Comparar la configuración activa con el último cambio conocido bueno:

   ```bash
   docker compose exec nginx cat /etc/nginx/nginx.conf
   git diff HEAD~1 -- deploy/ | grep -A3 -B3 nginx
   ```

4. Errores frecuentes: `upstream` referenciado en `proxy_pass` pero no definido,
   bloque `server` sin `listen`, o un `include` apuntando a un fichero inexistente.

## Resolución

- Corregir la directiva señalada por `nginx -t`. No recargar hasta que `nginx -t`
  devuelva `syntax is ok` y `test is successful`.

  ```bash
  docker compose exec nginx nginx -t && docker compose exec nginx nginx -s reload
  ```

- Si el cambio vino de un commit reciente y la corrección no es obvia, revertir primero
  y diagnosticar con calma:

  ```bash
  git revert --no-edit HEAD
  docker compose restart nginx
  ```

- Nunca aplicar un `reload` "a ciegas" esperando que funcione: con la config rota, nginx
  ignora el reload y se queda con la última válida, dando una falsa sensación de arreglo.

## Verificación

```bash
docker compose exec nginx nginx -t                                   # test is successful
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/        # esperado: 200
docker compose ps nginx --format '{{.Status}}'                       # esperado: healthy
```

El incidente se cierra cuando `nginx -t` pasa, el contenedor está `healthy` y la web
responde 200 de forma estable.
