---
title: "Fallo de handshake TLS entre servicios (certificado no confiable)"
doc_type: runbook
lang: es
services: [nginx, webapp]
---

## Síntomas

- Llamadas HTTPS internas fallan con `SSL: CERTIFICATE_VERIFY_FAILED` o `unable to get
  local issuer certificate`.
- Ocurre tras rotar un certificado o cambiar la CA, no de forma espontánea.
- El certificado es válido en fecha (distinto de rb-006), pero no se confía en él.

## Diagnóstico

1. Reproducir el handshake y ver el error exacto:

   ```bash
   docker compose exec webapp openssl s_client -connect nginx:443 -servername demo.local
   ```

2. Comprobar qué CA firma el certificado servido y si está en el almacén de confianza
   del cliente:

   ```bash
   docker compose exec webapp ls /etc/ssl/certs/ | grep -i demo
   ```

## Resolución

- Añadir la CA correcta al almacén de confianza del cliente (o montar el bundle correcto)
  y reiniciar el servicio que llama.
- Causa raíz: rotación de CA sin actualizar el bundle de confianza de los clientes.
  No desactivar la verificación TLS "para que funcione": eso abre la puerta a MITM.

## Verificación

```bash
docker compose exec webapp openssl s_client -connect nginx:443 -verify_return_error </dev/null && echo "verify OK"
```

Cerrar cuando el handshake verifique sin errores.
