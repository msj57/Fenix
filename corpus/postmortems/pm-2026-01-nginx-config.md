---
title: "Postmortem 2026-01-22: caída total por configuración de nginx inválida"
doc_type: postmortem
lang: es
services: [nginx, webapp]
---

## Resumen

El 22 de enero de 2026, entre las 14:03 y las 14:21 (18 minutos), la web pública quedó
completamente inaccesible (`Connection refused`). Causa raíz: un cambio en la
configuración de nginx con un bloque `upstream` duplicado dejó al contenedor en bucle
de reinicio tras un `reload` aplicado sin validar.

## Cronología

- **14:00** — Se aplica un cambio de configuración para añadir una nueva ruta `/api/v2`.
- **14:03** — `nginx -s reload` ejecutado sin `nginx -t` previo; el contenedor se reinicia
  y no vuelve a arrancar. Caída total.
- **14:08** — On-call recibe la alerta de healthcheck y revisa logs de nginx.
- **14:14** — `nginx -t` revela `duplicate upstream "webapp"` en la línea 42.
- **14:19** — Revert del cambio y `docker compose restart nginx`.
- **14:21** — Web restaurada.

## Causa raíz

El cambio introdujo un segundo bloque `upstream webapp` sin eliminar el anterior. nginx
rechaza la configuración entera, y al reiniciarse el contenedor no encontró una config
válida que cargar.

## Lo que funcionó / lo que no

- ✅ El revert fue limpio y rápido una vez identificado el error.
- ❌ Se aplicó `reload` sin `nginx -t` previo: regla básica saltada bajo prisa.
- ❌ No había validación de configuración en el pipeline antes de desplegar.

## Acciones

1. `nginx -t` obligatorio como paso de CI antes de cualquier deploy de configuración. Hecho.
2. Pre-commit que valida la sintaxis de los ficheros de nginx del repo.
3. Runbook rb-005 enlazado en la alerta de "nginx unhealthy".
