---
title: "Ticket #0057: error 504 Gateway Timeout al generar informes"
doc_type: ticket
lang: es
services: [nginx, webapp]
---

## Conversación

**Cliente (16:02):** Al generar el informe mensual me sale "504 Gateway Timeout".
Lo he probado tres veces. Los informes pequeños sí salen.

**Soporte (16:10):** Gracias por el detalle de que los pequeños funcionan — eso
apunta a tiempo de proceso, no a caída. ¿De cuántos registros hablamos en el mensual?

**Cliente (16:14):** Unos 180.000.

**Soporte (16:35):** Confirmado: la generación tarda ~75 segundos y el proxy corta
en 60 (`proxy_read_timeout`). El informe en realidad termina, pero la conexión ya
se ha cerrado.

**Soporte (16:50):** Hemos subido el timeout del endpoint de informes a 120 s como
mitigación. Te hemos reenviado el informe generado. A medio plazo el informe pasará
a generarse en segundo plano con aviso por email, para no depender de timeouts.

**Cliente (17:01):** Recibido el informe y probado de nuevo: funciona. Gracias.

## Resolución

`proxy_read_timeout` de nginx (60 s) menor que el tiempo real de generación (~75 s)
para informes grandes. Mitigado subiendo el timeout específico de la ruta `/reports`
a 120 s. Acción de fondo registrada: mover la generación de informes pesados a un
job asíncrono.
