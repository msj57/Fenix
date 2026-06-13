---
title: "Disco lleno en el host de servicios"
doc_type: runbook
lang: es
services: [postgres-demo, nginx, webapp]
---

## Síntomas

- Postgres en `read-only` o caído con `No space left on device` en sus logs.
- nginx no puede escribir logs de acceso; la webapp falla al subir ficheros.
- Alertas de disco > 90% en el dashboard de infraestructura.

## Diagnóstico

1. Confirmar qué sistema de ficheros está lleno:

   ```bash
   df -h | sort -k5 -hr | head
   ```

2. Localizar los directorios que más ocupan (en contenedores, mirar también volúmenes):

   ```bash
   du -xh --max-depth=2 /var/lib/docker | sort -hr | head -15
   docker system df -v
   ```

3. Sospechosos habituales, por orden: logs sin rotar, imágenes y contenedores
   huérfanos de Docker, WAL de Postgres creciendo por replicación rota.

## Resolución

- Liberar espacio rápido y sin riesgo:

  ```bash
  docker system prune -f          # contenedores parados e imágenes colgantes
  journalctl --vacuum-size=200M
  ```

- Si el causante son logs de un servicio, truncar en caliente (no borrar el fichero
  abierto, el proceso mantendría el espacio reservado):

  ```bash
  truncate -s 0 /var/log/nginx/access.log
  ```

- Si es el WAL de Postgres, NO borrar ficheros a mano jamás: diagnosticar por qué
  no se archiva (slot de replicación huérfano) y eliminar el slot con `pg_drop_replication_slot`.

- Causa raíz: configurar logrotate y una alerta a 80% para actuar antes del incidente.

## Verificación

```bash
df -h /var/lib/docker | awk 'NR==2 {print $5}'   # esperado: < 80%
docker compose ps --format '{{.Name}} {{.Status}}' | grep -i healthy
```

Postgres debe aceptar escrituras de nuevo: `CREATE TABLE _smoke (x int); DROP TABLE _smoke;`
