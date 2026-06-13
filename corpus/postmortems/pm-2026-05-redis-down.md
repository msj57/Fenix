---
title: "Postmortem 2026-05-06: pérdida de sesiones por caída de Redis sin failover"
doc_type: postmortem
lang: es
services: [redis-demo, webapp]
---

## Resumen

El 6 de mayo de 2026, entre las 10:15 y las 10:38 (23 minutos), todos los usuarios
perdieron la sesión y la web mostró errores intermitentes. Causa raíz: Redis se reinició
por OOM del host y la webapp no toleraba su ausencia, cayendo en lugar de degradar.

## Cronología

- **10:15** — El host mata Redis por presión de memoria; la webapp empieza a registrar
  `Connection refused` contra `redis-demo:6379`.
- **10:18** — Endpoints que usan sesión devuelven 500; los que solo tocan DB siguen bien.
- **10:25** — On-call confirma Redis caído y lo levanta.
- **10:30** — Redis arranca vacío: todas las sesiones perdidas, usuarios deslogueados.
- **10:38** — Servicio estable; se asume la pérdida de sesiones como daño aceptado.

## Causa raíz

Dos fallos encadenados: Redis sin límite de memoria propio (compitió con la webapp por
la RAM del host) y un cliente de caché que lanzaba excepción en vez de degradar cuando
Redis no respondía.

## Lo que funcionó / lo que no

- ✅ Los endpoints sin dependencia de Redis siguieron sirviendo.
- ❌ La webapp trató la caché como dependencia dura: sin Redis, caía entera.
- ❌ Redis sin `maxmemory` propio permitió la competencia por RAM con la webapp.

## Acciones

1. El cliente de caché degrada (sirve sin caché) si Redis no responde, no lanza. Hecho.
2. `maxmemory` y límite de contenedor para Redis. Hecho.
3. Runbook rb-017 enlazado; alerta de "redis down".
