---
title: "Saturación de CPU en el host de servicios"
doc_type: runbook
lang: es
services: [webapp, postgres-demo, nginx]
---

## Síntomas

- Latencia alta y generalizada en todos los servicios a la vez, sin errores claros.
- `load average` por encima del número de núcleos; respuestas lentas pero correctas.
- El dashboard muestra CPU al 100% sostenido.

## Diagnóstico

1. Ver qué contenedor consume la CPU:

   ```bash
   docker stats --no-stream --format '{{.Name}} {{.CPUPerc}}' | sort -t. -k1 -rn | head
   ```

2. Dentro del contenedor culpable, identificar el proceso/consulta:

   ```bash
   docker compose exec postgres-demo psql -U demo -c "SELECT pid, now()-query_start AS dur, query FROM pg_stat_activity WHERE state='active' ORDER BY dur DESC LIMIT 5;"
   ```

3. Distinguir carga legítima (pico de tráfico) de un proceso desbocado (bucle, consulta
   sin índice que hace full scan repetido).

## Resolución

- Si es una consulta desbocada, atacar su causa (índice, ver rb-009).
- Si es carga legítima sostenida, escalar recursos; un reinicio solo da alivio temporal.

## Verificación

```bash
docker stats --no-stream --format '{{.Name}} {{.CPUPerc}}'
```

Cerrar cuando la CPU vuelva a su línea base y la latencia se normalice 10 min.
