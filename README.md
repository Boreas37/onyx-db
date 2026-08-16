# Onyx DB — Local WordPress Vulnerability Database Mirror

**Onyx** is a local-first WordPress vulnerability scanner. This repository is the
**data mirror** — a daily-synced, gzip-compressed copy of the Wordfence
Intelligence Vulnerability Database, served via GitHub Releases so the `onyx`
CLI can update locally without any API calls.

## Data Source

The vulnerability data in this repository is from the
[Wordfence Intelligence Vulnerability Database](https://www.wordfence.com/threat-intel/)
(Production Feed), which is licensed **free for personal and commercial use**,
including redistribution, under the
[Wordfence Intelligence Terms and Conditions](https://www.wordfence.com/wordfence-intelligence-terms-and-conditions/).

Copyright notice per the license:

> © Wordfence — a division of Defiant, Inc. All rights reserved.
> Wordfence Intelligence: https://www.wordfence.com/threat-intel/

This mirror includes the Wordfence copyright designation and this license notice
in compliance with the redistribution terms. Onyx does not claim ownership of
the data — the scanner code is the project's own contribution.

## Files

- `wordfence-latest.json.gz` — gzip-compressed Wordfence Production Feed
  (~11.8MB compressed / ~151MB raw, ~38,800+ vulnerability records)

## Updating

A daily cron job (in the owner's infrastructure) re-pulls the Wordfence feed
from the API and publishes a new GitHub Release. The `onyx` CLI fetches the
latest release asset:

```
onyx update
```

## License

- **Data:** Wordfence Intelligence T&C (free for personal & commercial use;
  redistribution permitted with copyright retention — see above).
- **Tool:** see the main `onyx` repository for the scanner's license.
