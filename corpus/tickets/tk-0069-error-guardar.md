---
title: "Ticket #0069: error al guardar, dice algo de espacio"
doc_type: ticket
lang: es
services: [postgres-demo, webapp]
---

## Conversación

**Cliente (04:30):** No puedo guardar nada, me da error al darle a guardar. Sale algo de
"no space".

**Soporte (04:48):** Buenas noches. Eso apunta a disco lleno en el servidor. Lo estamos
revisando ahora mismo.

**Soporte (05:10):** El disco se había llenado con logs sin rotar y eso dejó la base de
datos en solo-lectura. Liberado el espacio y ya acepta escrituras.

**Cliente (05:14):** Confirmo que ya guarda. Gracias por la rapidez de madrugada.

## Resolución

Disco lleno por logs sin rotar → Postgres read-only (relacionado con rb-004,
pm-2026-03-disco-lleno). Espacio liberado; logrotate y alerta al 80% configurados.
