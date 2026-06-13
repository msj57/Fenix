---
title: "Ticket #0042: la web va muy lenta desde esta mañana"
doc_type: ticket
lang: es
services: [webapp, postgres-demo]
---

## Conversación

**Cliente (09:12):** Desde esta mañana la web tarda muchísimo en cargar, sobre todo
el listado de pedidos. Ayer iba bien. ¿Estáis caídos?

**Soporte (09:20):** Buenos días. No hay incidente abierto ahora mismo. ¿El resto de
secciones también va lento o solo el listado de pedidos?

**Cliente (09:24):** Sobre todo pedidos. El resto va normal tirando a lento.

**Soporte (09:41):** Lo hemos reproducido. El listado de pedidos hace una consulta
que desde la subida de datos de esta noche ha dejado de usar el índice. Lo está
revisando el equipo.

**Soporte (10:15):** Hemos lanzado un `ANALYZE` sobre la tabla de pedidos y la
consulta vuelve a usar el índice. Tiempos de respuesta normalizados (<300 ms).
¿Puedes confirmar de tu lado?

**Cliente (10:22):** Confirmado, vuelve a ir fluida. Gracias.

## Resolución

`ANALYZE pedidos;` tras una carga masiva nocturna que dejó las estadísticas del
planificador desactualizadas. Acción preventiva: `autovacuum_analyze_scale_factor`
ajustado para esa tabla y aviso al equipo de datos para lanzar `ANALYZE` al final
de sus cargas.
