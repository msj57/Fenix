---
title: "Ticket #0082: blank page after the latest update"
doc_type: ticket
lang: en
services: [nginx, webapp]
---

## Conversación

**Customer (10:05):** After your update this morning I just get a blank white page. No
error, nothing.

**Support (10:14):** A blank page with no error often means a static asset or config
mismatch after a deploy. Did it work before today?

**Customer (10:16):** Yes, fine yesterday.

**Support (10:45):** The deploy changed an nginx config and the reload had silently kept
the old one because of a syntax error. We fixed the config, validated it, and reloaded.

**Customer (10:52):** Page loads now. Thanks.

## Resolución

Blank page from an nginx config that failed validation so the reload was ignored (related
to rb-005, pm-2026-01-nginx-config). Config fixed, validated with nginx -t, reloaded.
