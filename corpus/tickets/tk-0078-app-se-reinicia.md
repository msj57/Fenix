---
title: "Ticket #0078: la app se reinicia sola y pierde lo que escribo"
doc_type: ticket
lang: es
services: [webapp]
---

## Conversación

**Cliente (16:40):** Estoy rellenando un formulario largo y a media tarde la web "se
recarga" sola y pierdo lo escrito. Van tres veces hoy.

**Soporte (16:52):** ¿Sucede más cuando llevas un rato o subiendo algo grande?

**Cliente (16:55):** Subiendo adjuntos grandes, ahora que lo dices.

**Soporte (17:30):** El servicio se quedaba sin memoria al procesar adjuntos grandes y el
sistema lo reiniciaba. Hemos limitado el tamaño y estamos procesando los adjuntos en
streaming para no cargarlos enteros en memoria.

**Cliente (17:35):** Probaré mañana con uno grande. Gracias.

## Resolución

Reinicios por OOM al cargar adjuntos grandes en memoria (relacionado con rb-008). Límite
de tamaño y procesamiento en streaming.
