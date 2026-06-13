---
title: "Postmortem 2026-04-19: 500 error spike from an unguarded deploy"
doc_type: postmortem
lang: en
services: [webapp]
---

## Summary

On April 19th, 2026, between 17:30 and 18:05 (35 minutes), ~30% of requests to the
orders endpoint returned HTTP 500. Root cause: a deploy shipped a code path that assumed
a field always present, which is null for legacy records.

## Timeline

- **17:28** — Release 3.02 deployed.
- **17:30** — Error rate on `/orders` jumps; healthcheck still green (it does not hit `/orders`).
- **17:41** — On-call correlates the spike with the 17:28 deploy.
- **17:52** — Traceback points to `KeyError: 'discount'` on legacy orders.
- **17:58** — Rollback to 3.01.
- **18:05** — Error rate back to baseline.

## Root cause

New code read `order["discount"]` directly. Legacy orders predate that field, so the key
was absent. No test covered legacy-shaped records.

## What went well / what didn't

- ✅ Rollback path was well rehearsed and fast.
- ❌ Healthcheck gave false confidence: it never exercised the failing endpoint.
- ❌ No test fixture for legacy data shapes.

## Action items

1. Use `.get("discount", 0)` and add a fixture with legacy records. Done in 3.03.
2. Synthetic check that exercises `/orders` post-deploy, not just `/healthz`.
3. Canary deploys for the orders service.
