---
title: "Redis evicting live data due to wrong eviction policy"
doc_type: runbook
lang: en
services: [redis-demo, webapp]
---

## Symptoms

- Users are logged out at random, or queued jobs vanish, even though Redis is up and
  `used_memory` is below `maxmemory`.
- `INFO stats` shows `evicted_keys` climbing while the application reports missing keys
  it never deleted.
- The problem worsens whenever a cache-heavy workload runs (reports, bulk imports).

## Diagnosis

1. Inspect the current policy and memory headroom:

   ```bash
   docker compose exec redis-demo redis-cli CONFIG GET maxmemory-policy
   docker compose exec redis-demo redis-cli INFO memory | grep -E "used_memory_human|maxmemory_human"
   ```

2. Confirm eviction is actually happening (not expiry):

   ```bash
   docker compose exec redis-demo redis-cli INFO stats | grep -E "evicted_keys|expired_keys"
   ```

3. Distinguish the two failure shapes:
   - `allkeys-lru` on a mixed workload → durable keys (sessions, queues) get evicted as
     if they were cache. This is the dangerous one.
   - `noeviction` → writes fail with OOM instead, but nothing is silently lost (see rb-003).

## Resolution

- Separate durable data from disposable cache. Keep cache on `allkeys-lru`; move
  sessions/queues to a logical DB or instance with `noeviction`:

  ```bash
  docker compose exec redis-demo redis-cli CONFIG SET maxmemory-policy allkeys-lru
  ```

- Enforce TTLs on cache writes so the cache self-limits before eviction kicks in. A
  `SET` without `EX` on cache data is the root cause to hunt down.

- Never pick an eviction policy to "make the errors stop" without knowing which keys are
  durable — that just trades visible failures for silent data loss.

## Verification

```bash
docker compose exec redis-demo redis-cli INFO stats | grep evicted_keys   # should stop growing
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/   # expected: 200
```

Close after 10 minutes with no new evictions of durable keys and stable sessions.
