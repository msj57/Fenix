---
title: "Certificado TLS caducado en nginx"
doc_type: runbook
lang: es
services: [nginx]
---

## Síntomas

- Los navegadores muestran `NET::ERR_CERT_DATE_INVALID` o "Tu conexión no es privada".
- Clientes y `curl` fallan con `certificate has expired` (código de error 10 en OpenSSL).
- Las llamadas entre servicios por HTTPS empiezan a fallar de golpe, a una hora redonda
  (los certificados caducan a medianoche UTC de su fecha de expiración).

## Diagnóstico

1. Comprobar la fecha de expiración del certificado servido:

   ```bash
   echo | openssl s_client -connect localhost:443 -servername demo.local 2>/dev/null \
     | openssl x509 -noout -dates
   ```

   `notAfter` en el pasado confirma la caducidad.

2. Revisar el certificado en disco directamente (por si el servido no es el esperado):

   ```bash
   docker compose exec nginx openssl x509 -enddate -noout -in /etc/nginx/certs/demo.crt
   ```

3. Confirmar que nginx apunta al certificado correcto:

   ```bash
   docker compose exec nginx grep -E "ssl_certificate" /etc/nginx/nginx.conf
   ```

## Resolución

- Renovar o regenerar el certificado. En el demo-env, regenerar uno autofirmado válido:

  ```bash
  docker compose exec nginx openssl req -x509 -newkey rsa:2048 -nodes \
    -keyout /etc/nginx/certs/demo.key -out /etc/nginx/certs/demo.crt \
    -days 365 -subj "/CN=demo.local"
  ```

- Recargar nginx para que tome el certificado nuevo (sin cortar conexiones activas):

  ```bash
  docker compose exec nginx nginx -t && docker compose exec nginx nginx -s reload
  ```

- Causa raíz: ausencia de renovación automática y de alerta de proximidad. Reiniciar
  nginx no arregla nada si el certificado en disco sigue caducado.

## Verificación

```bash
echo | openssl s_client -connect localhost:443 -servername demo.local 2>/dev/null \
  | openssl x509 -noout -checkend 0 && echo "vigente"
curl -s -o /dev/null -w "%{http_code}" https://localhost:443/   # esperado: 200
```

Cerrar cuando `checkend` confirme vigencia y, sobre todo, tras configurar una alerta a
30 días de la próxima expiración.
