---
title: "Ticket #0081: error de conexión nada más entrar"
doc_type: ticket
lang: es
services: [webapp, redis-demo]
---

## Conversación

**Cliente (08:50):** Al abrir la web me sale un error de conexión y no carga nada. He
probado en dos navegadores.

**Soporte (08:58):** ¿Te sale algún detalle del error o solo "error de conexión"?

**Cliente (09:01):** Solo eso, una pantalla genérica.

**Soporte (09:25):** El servicio de caché no había arrancado tras un reinicio de
madrugada y la web no toleraba su ausencia. Lo hemos levantado y ya carga. Además vamos a
hacer que la web funcione aunque la caché no esté.

**Cliente (09:29):** Ya entro, gracias.

## Resolución

Caché caída tras reinicio y webapp sin tolerancia a su ausencia (relacionado con rb-017,
pm-2026-05-redis-down). Redis levantado; pendiente degradación elegante sin caché.
