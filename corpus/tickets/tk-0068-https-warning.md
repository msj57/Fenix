---
title: "Ticket #0068: browser says the site is not secure"
doc_type: ticket
lang: en
services: [nginx]
---

## Conversación

**Customer (08:02):** This morning my browser shows "Your connection is not private" and
blocks the site. Yesterday it was fine.

**Support (08:09):** That message at a round hour usually means the TLS certificate
expired. Can you tell me what the error code says?

**Customer (08:12):** NET::ERR_CERT_DATE_INVALID.

**Support (08:30):** Confirmed expired certificate. We reissued it and reloaded the proxy.
Please reload the page.

**Customer (08:34):** Green padlock again. Thanks.

## Resolución

Expired TLS certificate (related to rb-006, pm-2026-03-cert-expiry). Reissued and reloaded;
expiry alerting added.
