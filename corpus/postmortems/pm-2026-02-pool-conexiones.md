---
title: "Postmortem 2026-02-18: caída de la web por agotamiento del pool de conexiones"
doc_type: postmortem
lang: es
services: [webapp, postgres-demo, nginx]
---

## Resumen

El 18 de febrero de 2026, entre las 11:42 y las 13:05 (83 minutos), la web pública
devolvió errores 502/500 al ~70% de las peticiones. Causa raíz: un endpoint nuevo
abría una transacción por petición y no la cerraba en la rama de error, agotando el
pool de conexiones de la webapp y los slots de Postgres.

## Cronología

- **11:38** — Despliegue de la versión 2.14 de la webapp (incluía el endpoint `/export`).
- **11:42** — Primeras alertas de latencia; nginx empieza a registrar 502 esporádicos.
- **11:55** — On-call reinicia la webapp: mejora durante ~8 minutos y vuelve a degradarse.
- **12:10** — Se detectan 47 conexiones `idle in transaction` en `pg_stat_activity`.
- **12:31** — Se identifica el endpoint `/export` como origen: cada llamada con filtros
  inválidos dejaba la transacción abierta.
- **12:48** — Rollback a la versión 2.13 y `pg_terminate_backend` de las transacciones zombi.
- **13:05** — Métricas normalizadas; fin del incidente.

## Causa raíz

El handler de `/export` hacía `BEGIN` explícito y solo ejecutaba `COMMIT` en el camino
feliz. Las peticiones con parámetros inválidos retornaban error 422 sin `ROLLBACK`,
dejando la conexión secuestrada. Con un pool de 20 conexiones, bastaron ~25 peticiones
malformadas para agotar el servicio.

## Lo que funcionó / lo que no

- ✅ La alerta de latencia saltó en 4 minutos.
- ✅ `pg_stat_activity` señaló la causa con precisión.
- ❌ El primer reinicio enmascaró el problema y retrasó el diagnóstico 15 minutos.
- ❌ El endpoint nuevo no tenía test del camino de error con transacción abierta.

## Acciones

1. Context manager de transacción obligatorio en la capa de datos (commit/rollback
   garantizado) — hecho en 2.15.
2. Alerta sobre `idle in transaction > 5 min` — hecho.
3. Regla de revisión: ningún `BEGIN` manual fuera de la capa de datos.
4. Timeout de transacción (`idle_in_transaction_session_timeout = 10min`) en Postgres.
