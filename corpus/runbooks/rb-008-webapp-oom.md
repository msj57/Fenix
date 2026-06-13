---
title: "Webapp killed by OOM (memory leak or unbounded load)"
doc_type: runbook
lang: en
services: [webapp]
---

## Symptoms

- The webapp container restarts repeatedly; `docker compose ps` shows recent uptime and
  a rising restart count.
- Container logs end abruptly with no traceback, and `docker inspect` reports
  `OOMKilled: true` with exit code 137.
- Memory usage climbs steadily between restarts (a leak) or spikes under specific
  endpoints (unbounded in-memory work).

## Diagnosis

1. Confirm the kill was OOM, not a crash:

   ```bash
   docker inspect fenix-webapp-1 --format '{{.State.OOMKilled}} {{.State.ExitCode}}'
   ```

   `true 137` confirms the kernel OOM killer terminated it.

2. Watch live memory against the container limit:

   ```bash
   docker stats fenix-webapp-1 --no-stream --format '{{.MemUsage}} {{.MemPerc}}'
   ```

3. Correlate growth with traffic — a leak grows even when idle; load-driven OOM tracks
   request volume to a specific route:

   ```bash
   docker compose logs --tail 200 webapp | grep -iE "export|report|/upload"
   ```

## Resolution

- Immediate relief — restart to reclaim memory and stop the crash loop:

  ```bash
  docker compose restart webapp
  ```

- If a single endpoint drives the spike (e.g. loading a full dataset into memory),
  disable or rate-limit that route while the fix ships. Streaming or paginating the
  heavy endpoint is the real fix.

- If it is a slow leak, raising the container memory limit only delays the next OOM;
  the leak must be found (object retention, unbounded caches, missing connection close).

- Setting a memory limit with no leak fix turns a slow leak into a periodic crash loop —
  treat the limit as a safety net, not a cure.

## Verification

```bash
docker inspect fenix-webapp-1 --format '{{.State.OOMKilled}}'   # expected: false
docker stats fenix-webapp-1 --no-stream --format '{{.MemPerc}}' # stable, well under 100%
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/   # expected: 200
```

Close after 10 minutes with no restart and flat memory.
