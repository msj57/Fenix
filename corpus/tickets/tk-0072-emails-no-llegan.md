---
title: "Ticket #0072: confirmation emails are delayed"
doc_type: ticket
lang: en
services: [webapp, redis-demo]
---

## Conversación

**Customer (15:00):** Order confirmation emails are arriving 20-30 minutes late, sometimes
not at all.

**Support (15:12):** Are orders themselves going through correctly, just the emails delayed?

**Customer (15:15):** Yes, orders are fine, only the emails lag.

**Support (15:45):** The email queue runs on Redis and it had filled up because the worker
was stuck on a slow batch. We restarted the worker and the backlog drained.

**Customer (15:52):** Emails flowing normally now, thanks.

## Resolución

Email worker stalled, backlog in the Redis queue. Worker restarted; added a queue-depth
alert and a worker healthcheck.
