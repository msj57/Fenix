---
title: "Internal DNS resolution failure between services"
doc_type: runbook
lang: en
services: [nginx, webapp, postgres-demo, redis-demo]
---

## Symptoms

- Services fail to reach each other by name: `could not translate host name "postgres-demo"`,
  `getaddrinfo failed`, or `host not found in upstream "webapp"`.
- The failure is all-or-nothing per name and often appears right after a restart or a
  Compose network change, not gradually.
- IP-based connections still work, which is the tell that the problem is name resolution,
  not the service itself.

## Diagnosis

1. Confirm it is DNS and not the target being down — resolve the name from inside the
   calling container:

   ```bash
   docker compose exec webapp getent hosts postgres-demo
   docker compose exec webapp nslookup postgres-demo 127.0.0.11
   ```

   Compose runs an embedded DNS server at `127.0.0.11`; an empty answer points to DNS.

2. Check that both services share a Docker network:

   ```bash
   docker network inspect fenix_default --format '{{range .Containers}}{{.Name}} {{end}}'
   ```

3. Verify the service name matches what the client expects (a renamed service or a
   custom `container_name` is a classic cause of name mismatch).

## Resolution

- If the services are on different networks, attach them to a shared one in
  `docker-compose.yml` and recreate:

  ```bash
  docker compose up -d --force-recreate webapp
  ```

- If the embedded resolver is stale after manual network surgery, recreate the affected
  containers so they pick up fresh DNS:

  ```bash
  docker compose up -d --force-recreate
  ```

- Root cause: hardcoded hostnames that drift from service names, or services split across
  networks. Never hardcode container IPs — they change on every recreate.

## Verification

```bash
docker compose exec webapp getent hosts postgres-demo   # must return an IP
docker compose exec webapp getent hosts redis-demo      # must return an IP
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/   # expected: 200
```

Close once every service resolves its dependencies by name and the webapp is healthy.
