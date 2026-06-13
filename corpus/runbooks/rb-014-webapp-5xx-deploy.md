---
title: "Webapp returns 500 errors after a deploy (regression)"
doc_type: runbook
lang: en
services: [webapp]
---

## Symptoms

- A spike of HTTP 500 errors begins right after a deployment; healthcheck may still pass.
- Application logs show tracebacks from new code paths (often a single endpoint).
- Error rate correlates exactly with the deploy timestamp.

## Diagnosis

1. Confirm the deploy is the trigger by correlating the error spike with the release time:

   ```bash
   docker compose logs --since 30m webapp | grep -E "Traceback|ERROR" | head
   ```

2. Identify the failing endpoint and exception:

   ```bash
   docker compose logs --tail 200 webapp | grep -A5 Traceback | sort | uniq -c | sort -rn
   ```

3. Check what changed in the release (the smallest diff that explains the error):

   ```bash
   git log --oneline -5
   git diff HEAD~1 -- apps/
   ```

## Resolution

- Fastest safe action — roll back to the previous known-good image:

  ```bash
  docker compose up -d --force-recreate webapp   # after pinning the previous tag
  ```

- Once stable, fix forward with a test that covers the broken path. Never re-deploy the
  same broken image hoping the error was transient.

## Verification

```bash
docker compose logs --since 10m webapp | grep -c ERROR   # should trend to 0
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/   # expected: 200
```
