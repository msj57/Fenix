---
title: "Redis out of memory: evictions and OOM errors"
doc_type: runbook
lang: en
services: [redis-demo, webapp]
---

## Symptoms

- Webapp logs show `OOM command not allowed when used memory > 'maxmemory'`.
- Cache hit ratio drops sharply; response times increase across the board.
- If sessions live in Redis, users get logged out unexpectedly.

## Diagnosis

1. Check memory usage and configured limit:

   ```bash
   docker compose exec redis-demo redis-cli INFO memory | grep -E "used_memory_human|maxmemory_human|maxmemory_policy"
   ```

2. Review eviction and keyspace stats:

   ```bash
   docker compose exec redis-demo redis-cli INFO stats | grep -E "evicted_keys|keyspace"
   ```

3. Identify what is filling memory — biggest keys first:

   ```bash
   docker compose exec redis-demo redis-cli --bigkeys
   ```

4. A `maxmemory_policy` of `noeviction` plus a writer that never expires keys is the
   usual culprit: writes fail outright instead of evicting old entries.

## Resolution

- Immediate relief — flush only if the data is a disposable cache (never blind-flush
  session or queue data):

  ```bash
  docker compose exec redis-demo redis-cli FLUSHDB
  ```

- Set an eviction policy appropriate for cache workloads:

  ```bash
  docker compose exec redis-demo redis-cli CONFIG SET maxmemory-policy allkeys-lru
  ```

- Root cause: find writers that omit TTLs (`SET` without `EX`) and fix them. Raising
  `maxmemory` without an eviction policy just delays the next incident.

## Verification

```bash
docker compose exec redis-demo redis-cli INFO memory | grep used_memory_human
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/   # expected: 200
```

Memory should stay below `maxmemory` and webapp logs must show no OOM errors for
10 minutes.
