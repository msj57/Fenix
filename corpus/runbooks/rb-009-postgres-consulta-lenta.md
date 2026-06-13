---
title: "Consulta lenta en PostgreSQL por estadísticas o índice"
doc_type: runbook
lang: es
services: [postgres-demo, webapp]
---

## Síntomas

- Un endpoint concreto (típicamente un listado o informe) se vuelve lento mientras el
  resto de la web responde con normalidad.
- La lentitud aparece de golpe tras una carga masiva de datos o un despliegue, no de
  forma gradual.
- En los logs de Postgres, consultas que antes tardaban milisegundos ahora superan el
  `log_min_duration_statement`.

## Diagnóstico

1. Identificar la consulta lenta y su plan de ejecución real:

   ```sql
   EXPLAIN (ANALYZE, BUFFERS) SELECT ... ;  -- la consulta del endpoint afectado
   ```

   Un `Seq Scan` sobre una tabla grande donde se esperaba `Index Scan` es la señal clave.

2. Comprobar si las estadísticas del planificador están desactualizadas:

   ```sql
   SELECT relname, last_analyze, last_autoanalyze, n_mod_since_analyze
   FROM pg_stat_user_tables ORDER BY n_mod_since_analyze DESC LIMIT 10;
   ```

3. Confirmar que existe el índice que la consulta debería usar:

   ```sql
   SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'pedidos';
   ```

## Resolución

- Si las estadísticas están viejas tras una carga masiva, actualizarlas (suele ser la
  causa: el planificador cree que la tabla es pequeña y elige `Seq Scan`):

  ```sql
  ANALYZE pedidos;
  ```

- Si falta el índice adecuado para el filtro u ordenación, crearlo sin bloquear:

  ```sql
  CREATE INDEX CONCURRENTLY idx_pedidos_fecha ON pedidos (fecha);
  ```

- Causa raíz: cargas masivas que no lanzan `ANALYZE` al terminar, o
  `autovacuum_analyze_scale_factor` demasiado alto para tablas que cambian mucho.
  Reiniciar la webapp no cambia nada: el problema está en el plan de Postgres.

## Verificación

```sql
EXPLAIN (ANALYZE) SELECT ... ;   -- debe mostrar Index Scan y tiempo < umbral
```

```bash
curl -s -o /dev/null -w "%{time_total}s\n" http://localhost:8080/pedidos   # esperado: < 0.3s
```

Cerrar cuando el plan use el índice y la latencia del endpoint vuelva a su línea base.
