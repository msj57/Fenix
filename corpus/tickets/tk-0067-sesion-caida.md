---
title: "Ticket #0067: me cierra la sesión sola cada poco"
doc_type: ticket
lang: es
services: [redis-demo, webapp]
---

## Conversación

**Cliente (12:05):** Llevo toda la mañana y cada 10-15 minutos me echa y tengo que volver
a entrar. Es muy molesto.

**Soporte (12:14):** ¿Empezó hoy o lleva días?

**Cliente (12:16):** Hoy de repente.

**Soporte (12:40):** Lo vemos. Un proceso de informes llenó la memoria de la caché y la
política de borrado estaba expulsando también las sesiones. Hemos parado ese proceso y
separado las sesiones de la caché.

**Cliente (12:45):** Ya no me echa, gracias.

## Resolución

Evicción de claves de sesión por política `allkeys-lru` con la memoria llena (relacionado
con rb-010 y pm-2026-04-redis-eviction). Sesiones separadas en una DB lógica con `noeviction`.
