---
title: "Ticket #0076: el checkout falla a veces con timeout"
doc_type: ticket
lang: es
services: [nginx, webapp, postgres-demo]
---

## Conversación

**Cliente (13:10):** En la pasarela de pago, a veces se queda pensando y acaba dando un
error de tiempo de espera. No siempre.

**Soporte (13:25):** ¿Pasa más a ciertas horas o de forma aleatoria?

**Cliente (13:28):** Parece más por la tarde.

**Soporte (14:05):** Por la tarde hay más carga y algunas consultas de stock se quedaban
esperando un bloqueo en la base de datos. Hemos acortado esas transacciones y el timeout
desaparece.

**Cliente (14:12):** No hemos vuelto a ver el error. Gracias.

## Resolución

Timeouts en checkout por esperas de lock en Postgres bajo carga (relacionado con rb-015).
Transacciones acortadas y orden de bloqueo consistente.
