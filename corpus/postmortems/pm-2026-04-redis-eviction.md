---
title: "Postmortem 2026-04-07: session logouts caused by Redis eviction policy"
doc_type: postmortem
lang: en
services: [redis-demo, webapp]
---

## Summary

On April 7th, 2026, between 09:20 and 10:15 (55 minutes), roughly 40% of logged-in
users were forcibly logged out and could not maintain sessions. Root cause: Redis
reached `maxmemory` and the eviction policy `allkeys-lru` — appropriate for cache,
wrong for a mixed workload — evicted live session keys.

## Timeline

- **09:05** — A batch job started caching large report payloads in Redis without TTL.
- **09:20** — `used_memory` hit `maxmemory` (512 MB); evictions began. First user
  complaints about being logged out.
- **09:40** — On-call confirmed `evicted_keys` growing fast via `INFO stats`.
- **09:55** — Batch job stopped; report keys deleted with a `SCAN`-based cleanup.
- **10:10** — Eviction stopped, sessions stable.
- **10:15** — Incident closed after verification.

## Root cause

Two workloads with different durability needs shared one Redis instance and one
eviction policy. The cache workload (reports) flooded memory, and `allkeys-lru`
treated session keys as evictable cache entries.

## What went well / what didn't

- ✅ `INFO stats` made the eviction storm obvious in minutes.
- ❌ No alert on `evicted_keys` rate — users noticed before monitoring did.
- ❌ The batch job had no review for cache TTLs or memory budget.

## Action items

1. Split workloads: dedicated logical DB (and later instance) for sessions, with
   `noeviction`; cache stays on `allkeys-lru`. Done.
2. Alert on `evicted_keys` rate and on `used_memory > 80% maxmemory`. Done.
3. Mandatory TTL on all cache writes, enforced by the cache client wrapper.
