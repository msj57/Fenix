---
title: "High Redis latency caused by slow commands"
doc_type: runbook
lang: en
services: [redis-demo, webapp]
---

## Symptoms

- Webapp endpoints that hit the cache become slow while Redis stays up and within memory.
- Latency is spiky, not constant; it correlates with specific operations.
- `redis-cli --latency` reports values far above the usual sub-millisecond range.

## Diagnosis

1. Measure baseline latency:

   ```bash
   docker compose exec redis-demo redis-cli --latency
   ```

2. Find slow commands in the slowlog (the usual culprits: `KEYS *`, big `SMEMBERS`,
   large `LRANGE`):

   ```bash
   docker compose exec redis-demo redis-cli SLOWLOG GET 10
   ```

3. Confirm no `KEYS` is being run against production (it blocks the single thread):

   ```bash
   docker compose logs --tail 200 webapp | grep -i "KEYS"
   ```

## Resolution

- Replace blocking commands: `SCAN` instead of `KEYS`, paginate large collection reads.
- Redis is single-threaded; one slow `O(N)` command stalls everyone. The fix is the
  access pattern, not more memory.

## Verification

```bash
docker compose exec redis-demo redis-cli --latency   # back to sub-ms
docker compose exec redis-demo redis-cli SLOWLOG RESET
```

Close after 10 minutes with no new slowlog entries and normal endpoint latency.
