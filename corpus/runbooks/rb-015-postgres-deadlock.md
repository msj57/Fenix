---
title: "Deadlocks y bloqueos en PostgreSQL"
doc_type: runbook
lang: es
services: [postgres-demo, webapp]
---

## Síntomas

- La webapp registra `deadlock detected` o esperas largas con `lock timeout`.
- Operaciones que normalmente son instantáneas se quedan colgadas de forma intermitente.
- En los logs de Postgres: `Process ... waits for ShareLock on transaction`.

## Diagnóstico

1. Ver qué procesos están bloqueados y quién los bloquea:

   ```sql
   SELECT blocked.pid AS bloqueado, blocking.pid AS bloqueante,
          blocked.query AS q_bloqueada, blocking.query AS q_bloqueante
   FROM pg_stat_activity blocked
   JOIN pg_stat_activity blocking ON blocking.pid = ANY(pg_blocking_pids(blocked.pid));
   ```

2. Revisar el orden en que las transacciones adquieren locks (causa típica del deadlock):
   dos transacciones tomando las mismas filas en orden distinto.

## Resolución

- Alivio inmediato — terminar el proceso bloqueante más antiguo si está claramente colgado:

  ```sql
  SELECT pg_terminate_backend(<pid_bloqueante>);
  ```

- Causa raíz: ordenar siempre las escrituras de forma consistente (p. ej. por clave
  primaria ascendente) para que no se crucen, y mantener las transacciones cortas.

## Verificación

```sql
SELECT count(*) FROM pg_stat_activity WHERE wait_event_type = 'Lock';   -- esperado: 0
```

Cerrar cuando no haya esperas por lock y la webapp responda sin colgarse durante 10 min.
