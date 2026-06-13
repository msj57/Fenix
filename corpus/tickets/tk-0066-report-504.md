---
title: "Ticket #0066: report export times out"
doc_type: ticket
lang: en
services: [nginx, webapp]
---

## Conversación

**Customer (14:10):** Exporting the full customer report fails with a 504 after about a
minute. Smaller exports work fine.

**Support (14:18):** Thanks — the size dependency tells us it is processing time, not an
outage. How many rows is the full export?

**Customer (14:22):** Around 220,000.

**Support (14:50):** Confirmed: generation takes ~80s and the proxy cuts at 60s. We raised
the timeout on the export route to 120s as a stopgap and queued the work to move exports
to a background job.

**Customer (14:58):** Works now, thanks.

## Resolución

Proxy read timeout shorter than real generation time for large exports (related to
rb-012, tk-0057). Mitigated by raising the route timeout; async job planned.
