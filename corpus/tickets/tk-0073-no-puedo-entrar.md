---
title: "Ticket #0073: no puedo entrar, error 500"
doc_type: ticket
lang: es
services: [webapp]
---

## Conversación

**Cliente (18:05):** Desde hace media hora no puedo entrar, me sale "Error 500" en
cualquier página.

**Soporte (18:12):** ¿Recuerdas si justo antes hubo algún aviso de mantenimiento?

**Cliente (18:14):** No, estaba usándola normal y de repente.

**Soporte (18:40):** Coincide con un despliegue que hicimos a las 17:30. Una parte del
código fallaba con pedidos antiguos. Hemos revertido a la versión anterior.

**Cliente (18:44):** Ya entra, gracias.

## Resolución

Regresión introducida por un deploy que fallaba en registros antiguos (relacionado con
rb-014, pm-2026-04-deploy-regression). Revertido a la versión estable.
