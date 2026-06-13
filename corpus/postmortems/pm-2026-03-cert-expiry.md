---
title: "Postmortem 2026-03-11: outage caused by an expired TLS certificate"
doc_type: postmortem
lang: en
services: [nginx]
---

## Summary

On March 11th, 2026, from 00:00 to 00:48 UTC (48 minutes), all HTTPS traffic failed with
certificate errors. Root cause: the TLS certificate expired at midnight UTC and no
renewal or alerting was in place.

## Timeline

- **00:00** — Certificate `notAfter` passes; browsers and API clients start rejecting
  the connection with `CERT_DATE_INVALID`.
- **00:12** — First user reports; monitoring did not catch it (no cert-expiry alert).
- **00:30** — On-call confirms expiry via `openssl s_client`.
- **00:44** — A new certificate is issued and nginx reloaded.
- **00:48** — HTTPS restored.

## Root cause

The certificate had a fixed 1-year validity and was renewed manually the previous year.
The reminder was lost; nothing alerted on approaching expiry, so it lapsed silently.

## What went well / what didn't

- ✅ Once diagnosed, reissue and reload took under 5 minutes.
- ❌ No alerting on certificate expiry — users noticed before the team did.
- ❌ Manual renewal with no calendar or automation is a single point of human failure.

## Action items

1. Alert at 30 and 7 days before any certificate expiry. Done.
2. Automate renewal where possible; document the manual path otherwise (rb-006).
3. Add cert `notAfter` to the Ops dashboard.
