---
title: "Ticket #0063: no se cargan las imágenes de los productos"
doc_type: ticket
lang: es
services: [nginx, webapp]
---

## Conversación

**Cliente (16:30):** Las fichas de producto cargan pero las imágenes salen rotas. El texto
sí aparece.

**Soporte (16:38):** ¿Te sale algún código si abres una imagen directamente en otra pestaña?

**Cliente (16:42):** Pone 404.

**Soporte (17:05):** Lo tenemos. Tras el último despliegue cambió la ruta donde se sirven
los estáticos y nginx seguía apuntando a la carpeta antigua. Corregido el `alias` y
recargado nginx.

**Cliente (17:10):** Ahora se ven, gracias.

## Resolución

Ruta de estáticos desalineada entre webapp y nginx tras un deploy. Corregido el bloque
`location /static` y recargado nginx con validación previa (rb-005).
