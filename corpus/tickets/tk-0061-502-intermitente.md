---
title: "Ticket #0061: a veces da error 502 al entrar"
doc_type: ticket
lang: es
services: [nginx, webapp]
---

## Conversación

**Cliente (11:03):** A ratos al entrar a la web me sale una pantalla de "502 Bad Gateway"
y si recargo ya entra. Pasa varias veces al día.

**Soporte (11:15):** Gracias. Ese 502 intermitente suele ser la aplicación reiniciándose
o saturada por debajo. ¿Recuerdas si coincide con alguna hora concreta?

**Cliente (11:20):** Sobre todo a media mañana, cuando hay más gente.

**Soporte (11:48):** Confirmado: la webapp se queda sin conexiones a base de datos en los
picos y nginx devuelve 502 mientras tanto. Estamos ajustando el pool. Mientras, recargar
funciona porque pillas otra conexión libre.

**Cliente (11:52):** Ok, gracias por la explicación.

## Resolución

502 intermitente por agotamiento del pool de conexiones en picos (relacionado con
rb-002). Mitigado subiendo el pool y añadiendo alerta de saturación.
