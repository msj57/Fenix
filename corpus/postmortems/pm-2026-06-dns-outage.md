---
title: "Postmortem 2026-06-02: intermittent failures from a stale internal DNS cache"
doc_type: postmortem
lang: en
services: [webapp, postgres-demo, nginx]
---

## Summary

On June 2nd, 2026, between 09:05 and 09:40 (35 minutes), the webapp intermittently failed
to reach the database with `could not translate host name`. Root cause: a Compose network
recreation left a stale embedded-DNS state in the running webapp container.

## Timeline

- **09:00** — A network change is applied and some services are recreated, but the webapp
  container is not.
- **09:05** — The webapp intermittently fails to resolve `postgres-demo`; IP-based health
  probes still pass, masking the issue.
- **09:20** — On-call resolves the name from inside the webapp container and gets an empty
  answer from `127.0.0.11`.
- **09:35** — `docker compose up -d --force-recreate webapp` refreshes DNS.
- **09:40** — Resolution stable.

## Root cause

Recreating the network without recreating all attached containers left the webapp with a
stale view of the embedded DNS resolver, so it could not resolve names that had moved.

## What went well / what didn't

- ✅ The IP-vs-name distinction quickly ruled out the database being down.
- ❌ Partial recreation of the stack is an easy mistake under pressure.
- ❌ Health probes used IPs, hiding a name-resolution problem.

## Action items

1. Always recreate all attached containers after a network change. Documented in rb-007.
2. Add a name-resolution check (not just IP) to service health.
3. Avoid manual network surgery on the demo-env; script it.
