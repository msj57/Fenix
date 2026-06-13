---
title: "Ticket #0077: dashboard shows old numbers"
doc_type: ticket
lang: en
services: [postgres-demo, webapp]
---

## Conversación

**Customer (11:00):** The reporting dashboard is showing yesterday's totals even though
we've made sales today.

**Support (11:10):** Does a hard refresh change anything, or is it always stale?

**Customer (11:13):** Always stale, even after refresh.

**Support (11:40):** The dashboard reads from a replica and replication had fallen behind
because of a long-running report query holding things up. We cleared it and the replica
caught up.

**Customer (11:47):** Numbers are current now. Thanks.

## Resolución

Replication lag on the read replica caused stale dashboard data (related to rb-016). Long
read terminated; standby delay tuned.
