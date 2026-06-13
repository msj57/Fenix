---
title: "Replication lag growing on the PostgreSQL replica"
doc_type: runbook
lang: en
services: [postgres-demo]
---

## Symptoms

- Read queries on the replica return stale data; users see "saved" changes disappear.
- Monitoring shows replication lag growing into seconds or minutes.
- WAL accumulates on the primary, risking the disk-full scenario (see rb-004).

## Diagnosis

1. Measure the lag from the primary's point of view:

   ```sql
   SELECT client_addr, state, pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) AS lag_bytes
   FROM pg_stat_replication;
   ```

2. On the replica, check whether replay is blocked by a long-running read query:

   ```sql
   SELECT now() - query_start AS dur, query FROM pg_stat_activity
   WHERE state = 'active' ORDER BY dur DESC LIMIT 5;
   ```

## Resolution

- If a long read on the replica blocks replay, terminate it or set
  `max_standby_streaming_delay` appropriately.
- If the primary produces WAL faster than the replica applies it, the replica is
  under-resourced (CPU/IO) — scale it; do not drop the slot, that risks WAL buildup.

## Verification

```sql
SELECT pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) FROM pg_stat_replication;  -- near 0
```

Close when lag returns to its baseline and the replica serves fresh reads.
