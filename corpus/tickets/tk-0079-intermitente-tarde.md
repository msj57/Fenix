---
title: "Ticket #0079: web slow only in the afternoon"
doc_type: ticket
lang: en
services: [webapp, postgres-demo, nginx]
---

## Conversación

**Customer (17:00):** The whole site drags in the afternoons. Mornings are fine.

**Support (17:12):** Is it everything slowing down together, or one feature?

**Customer (17:15):** Everything, across the board.

**Support (17:50):** Afternoon traffic was pushing CPU to 100% on the host, so everything
queued. We've scaled the resources for peak hours; it should stay responsive now.

**Customer (18:00):** Much better this afternoon, thanks.

## Resolución

Across-the-board afternoon slowness from CPU saturation under peak load (related to
rb-019). Resources scaled for peak; reinforced with monitoring.
