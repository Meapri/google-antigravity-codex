---
name: google-grounded-search
description: "Use consent-gated Google-grounded search for current facts, source checks, versions, policies, prices, schedules, and verification."
---

# Google Grounded Search

After confirming explicit consent, use `google_grounded_search` for current or
source-backed questions. Keep `direct_source_retry` enabled unless raw redirect
behavior is being debugged.

Treat the response as evidence rather than final truth. Prefer resolved
canonical HTTPS publisher URLs, map claims to sources where available, and say
when `needs_manual_source_check` indicates thin evidence.
