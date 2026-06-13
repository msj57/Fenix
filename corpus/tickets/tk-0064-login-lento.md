---
title: "Ticket #0064: el login tarda muchísimo"
doc_type: ticket
lang: es
services: [webapp, redis-demo]
---

## Conversación

**Cliente (09:50):** Entrar con usuario y contraseña tarda como 10 segundos. Antes era
instantáneo.

**Soporte (10:02):** ¿El resto de la web va a velocidad normal una vez dentro?

**Cliente (10:05):** Sí, solo el login.

**Soporte (10:30):** El login valida la sesión contra Redis y la caché estaba lenta por
un comando KEYS que recorría todas las claves en cada intento. Lo hemos sustituido por
acceso directo por clave.

**Cliente (10:36):** Ahora entra al momento. Gracias.

## Resolución

Latencia de login por un `KEYS *` bloqueante en Redis (relacionado con rb-018). Sustituido
por acceso directo a la clave de sesión.
