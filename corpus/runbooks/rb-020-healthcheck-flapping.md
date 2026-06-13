---
title: "Healthcheck flapping: a service oscillates between healthy and unhealthy"
doc_type: runbook
lang: en
services: [webapp, nginx]
---

## Symptoms

- `docker compose ps` shows a service flipping between `healthy` and `unhealthy`.
- nginx intermittently routes 502s as the upstream drops in and out of rotation.
- No single clear failure; the service "works" when checked manually.

## Diagnosis

1. Inspect recent healthcheck results:

   ```bash
   docker inspect fenix-webapp-1 --format '{{json .State.Health}}' | python3 -m json.tool
   ```

2. Check whether the healthcheck timeout is too tight for a loaded service:

   ```bash
   docker compose config | grep -A4 healthcheck
   ```

3. Correlate the flapping with load — a check that times out only under load points to
   the check budget, not the service being truly down.

## Resolution

- If the check is too strict (short timeout, heavy endpoint), point it at a cheap
  `/healthz` and widen the timeout/retries to realistic values.
- If the service genuinely degrades under load, that is the real incident — treat the
  flapping as a symptom and chase the underlying resource limit.

## Verification

```bash
docker compose ps webapp --format '{{.Status}}'   # stable healthy for 10 min
```
