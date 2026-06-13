---
title: "Postmortem 2026-03-29: Postgres en read-only por disco lleno (logs sin rotar)"
doc_type: postmortem
lang: es
services: [postgres-demo, nginx, webapp]
---

## Resumen

El 29 de marzo de 2026, entre las 03:50 y las 05:10 (80 minutos, de madrugada), las
escrituras fallaron con `No space left on device` y Postgres pasó a read-only. Causa
raíz: los logs de acceso de nginx crecieron sin rotación hasta llenar el disco.

## Cronología

- **03:50** — El disco alcanza el 100%; Postgres no puede escribir el WAL y entra en read-only.
- **03:52** — Las escrituras de la webapp empiezan a fallar; alertas de error 500.
- **04:20** — On-call (madrugada) tarda en responder; identifica el disco lleno con `df -h`.
- **04:40** — `du` señala `/var/log/nginx/access.log` ocupando 38 GB.
- **04:55** — Se trunca el log en caliente (`truncate -s 0`) y se libera espacio.
- **05:10** — Postgres vuelve a aceptar escrituras; incidente cerrado.

## Causa raíz

`logrotate` no estaba configurado para los logs de nginx en el demo-env. Un pico de
tráfico de bots multiplicó el volumen de logs y, sin rotación, llenó el disco en horas.

## Lo que funcionó / lo que no

- ✅ Truncar en caliente liberó espacio sin reiniciar nada.
- ❌ La alerta de disco saltó al 100%, no al 80%: sin margen para actuar antes.
- ❌ Respuesta lenta de madrugada por falta de runbook claro enlazado en la alerta.

## Acciones

1. `logrotate` para todos los logs de servicios, con límite de tamaño y retención. Hecho.
2. Alerta de disco al 80% (no al 100%). Hecho.
3. Runbook rb-004 enlazado en la alerta.
