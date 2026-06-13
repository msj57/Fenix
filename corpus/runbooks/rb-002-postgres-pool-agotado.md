---
title: "Pool de conexiones de PostgreSQL agotado"
doc_type: runbook
lang: es
services: [postgres-demo, webapp]
---

## Síntomas

- La webapp responde con errores 500 o timeouts; nginx puede mostrar 502/504.
- En los logs de la webapp: `QueuePool limit of size N overflow M reached` o
  `FATAL: remaining connection slots are reserved`.
- Latencia creciente en endpoints que tocan base de datos mientras el resto funciona.

## Diagnóstico

1. Contar conexiones activas y su estado:

   ```sql
   SELECT state, count(*) FROM pg_stat_activity
   WHERE datname = 'demo' GROUP BY state;
   ```

2. Identificar consultas atascadas (posibles transacciones sin cerrar):

   ```sql
   SELECT pid, now() - xact_start AS duracion, state, query
   FROM pg_stat_activity
   WHERE state <> 'idle' ORDER BY duracion DESC LIMIT 10;
   ```

3. Comparar con el límite del servidor:

   ```sql
   SHOW max_connections;
   ```

4. Si `idle in transaction` domina el listado, el problema está en el código de la
   webapp (conexiones sin devolver al pool), no en Postgres.

## Resolución

- Alivio inmediato — matar las transacciones zombi (con criterio, anotando los pid):

  ```sql
  SELECT pg_terminate_backend(pid) FROM pg_stat_activity
  WHERE state = 'idle in transaction' AND now() - xact_start > interval '5 minutes';
  ```

- Reiniciar la webapp para que el pool arranque limpio:

  ```bash
  docker compose restart webapp
  ```

- Causa raíz: revisar el tamaño del pool de la webapp (`DB_POOL_SIZE`) frente a
  `max_connections`, y el código que abre transacciones sin `commit/rollback`.
  Subir `max_connections` sin más solo pospone la recurrencia.

## Verificación

```sql
SELECT count(*) FROM pg_stat_activity WHERE datname = 'demo';
```

El valor debe estabilizarse muy por debajo de `max_connections` y la webapp debe
responder 200 en `/healthz` durante 10 minutos seguidos.
