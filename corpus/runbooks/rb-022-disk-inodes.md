---
title: "No space left on device with disk usage under 100% (inode exhaustion)"
doc_type: runbook
lang: en
services: [postgres-demo, webapp, nginx]
---

## Symptoms

- Writes fail with `No space left on device` even though `df -h` shows free space.
- Often caused by millions of tiny files (session files, cache fragments, log shards).
- Distinct from rb-004: there bytes ran out; here it is the inode table.

## Diagnosis

1. Check inode usage, not just bytes:

   ```bash
   df -i | sort -k5 -hr | head
   ```

2. Find the directory holding the most files:

   ```bash
   for d in /tmp /var/lib/docker /var/log; do echo -n "$d "; find $d -xdev 2>/dev/null | wc -l; done
   ```

## Resolution

- Delete or consolidate the flood of small files (old sessions, cache shards). Truncating
  one big log does not help here — the problem is file count, not size.
- Root cause: a writer creating one file per item with no cleanup. Switch to a single
  append-only file or a TTL-based cleanup job.

## Verification

```bash
df -i / | awk 'NR==2 {print $5}'   # expected: well under 100%
```

Close when inode usage is healthy and writes succeed.
