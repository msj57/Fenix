---
title: "Ticket #0071: a veces se duplican los pedidos"
doc_type: ticket
lang: es
services: [webapp, postgres-demo]
---

## Conversación

**Cliente (10:20):** Algunos clientes nos dicen que les llega el pedido por duplicado si
le dan dos veces al botón cuando va lento.

**Soporte (10:35):** ¿Ocurre solo cuando la web va lenta y pulsan varias veces?

**Cliente (10:38):** Exacto, cuando tarda en responder.

**Soporte (11:20):** Entendido. No hay protección contra doble envío cuando la respuesta
tarda. Lo hemos pasado a desarrollo para añadir idempotencia en la creación de pedidos;
mientras, hemos puesto un bloqueo en el botón al primer clic.

**Cliente (11:25):** El bloqueo del botón ya ayuda. Esperamos la solución de fondo.

## Resolución

Doble envío en respuestas lentas por falta de idempotencia. Mitigación: bloqueo del botón.
Fondo: clave de idempotencia en el endpoint de creación de pedidos.
