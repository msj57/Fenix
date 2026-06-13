---
title: "Postmortem 2026-05-21: degradación por consulta sin índice tras migración"
doc_type: postmortem
lang: en
services: [postgres-demo, webapp]
---

## Summary

On May 21st, 2026, between 12:40 and 13:25 (45 minutes), the orders listing degraded to
multi-second response times. Root cause: a schema migration dropped and did not recreate
an index, turning a fast lookup into a sequential scan.

## Timeline

- **12:35** — Migration 0042 runs as part of the deploy; it rebuilds the orders table.
- **12:40** — `/orders` latency climbs from ~80 ms to ~4 s; other endpoints unaffected.
- **12:58** — On-call runs `EXPLAIN ANALYZE` and sees a `Seq Scan` where an `Index Scan`
  was expected.
- **13:10** — `pg_indexes` confirms `idx_orders_customer` is missing post-migration.
- **13:20** — Index recreated with `CREATE INDEX CONCURRENTLY`.
- **13:25** — Latency back to baseline.

## Root cause

The migration recreated the table but the index creation was omitted from the migration
script. The planner fell back to a sequential scan on a large table.

## What went well / what didn't

- ✅ `EXPLAIN ANALYZE` pinpointed the missing index quickly.
- ❌ The migration was not reviewed for index parity before/after.
- ❌ No query-latency regression test on critical endpoints.

## Action items

1. Migration checklist: assert index parity before merge. Done.
2. Latency budget assertion for `/orders` in the smoke suite.
3. Runbook rb-009 linked from the slow-query alert.
