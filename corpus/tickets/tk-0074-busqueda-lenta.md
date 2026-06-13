---
title: "Ticket #0074: search got slow after the weekend"
doc_type: ticket
lang: en
services: [postgres-demo, webapp]
---

## Conversación

**Customer (09:30):** Product search has been crawling since Monday. It used to be instant.

**Support (09:40):** Did anything change over the weekend on your side — a big import maybe?

**Customer (09:43):** We did load the new catalog on Saturday night.

**Support (10:15):** That's it. The bulk import left the planner's statistics stale, so
search stopped using its index. We ran ANALYZE and it's fast again.

**Customer (10:20):** Confirmed, snappy again. Thanks.

## Resolución

Stale planner statistics after a bulk import caused a sequential scan on search (related
to rb-009, tk-0042). Fixed with ANALYZE; autovacuum tuned for that table.
