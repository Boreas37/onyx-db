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
- `manifest.json` — update manifest advertising the full snapshot and recent
  deltas (plus the optional `popular` entry), consumed by `onyx update`

## Optional enrichment assets

Besides the vulnerability feed, the mirror publishes two **optional** assets
for offline scan enrichment. They are advertised separately from the feed and
are never required: clients must degrade gracefully (skip the feature) when
they are absent from a release or from the manifest.

### `popular.json.gz` (daily)

The most popular WordPress.org plugins and themes, refreshed on every daily
release. Shape:

```json
{
  "plugins": ["akismet", "contact-form-7", "..."],
  "themes":  ["twentytwentyfive", "generatepress", "..."],
  "counts_plugins": {"akismet": 5000000, "contact-form-7": 4000000, "..."},
  "counts_themes":  {"twentytwentyfive": 3000000, "generatepress": 2000000, "..."}
}
```

- Slug arrays are lowercase, deduplicated, ordered by popularity descending,
  capped at 500 plugins / 100 themes (the wordpress.org API may return fewer).
- `counts_plugins` / `counts_themes` map each slug to its wordpress.org
  `active_installs` figure (integer >= 0), covering exactly the slugs that
  made the list. If the API omits `active_installs` for an item the slug stays
  in the list with a count of `0`.
- Both counts maps are **optional**: clients that do not need install counts
  ignore them, and absence of the keys means "no counts available" (older
  releases / clients degrade gracefully).
- Built from `https://api.wordpress.org/plugins/info/1.2/` and
  `https://api.wordpress.org/themes/info/1.2/` (`browse=popular`).
- Deterministic `gzip -9 -n`; signed with the same onyx-minisign key as the
  feed (verify with `ONYX_DB_PUBKEY`).
- Advertised in `manifest.json` under the optional top-level `popular` field:
  `{"popular": {"sha256": "<hex>", "size": N, "path": "<release>/popular.json.gz"}}`.
  If the wordpress.org API is unreachable the daily release still goes out —
  the `popular` key is simply omitted, which clients read as "not available".

### `fingerprints.json.gz` (weekly + manual dispatch)

A WordPress core asset fingerprint table for onyx's `--fingerprint-db`,
built by the `fingerprints` workflow (weekly schedule + `workflow_dispatch`).
Shape:

```json
{
  "files": {
    "wp-includes/js/wp-emoji-release.min.js": {
      "<md5hex>": ["7.1", "7.0"]
    }
  }
}
```

- Covers the last 6 stable WordPress versions (current + 5 previous) and
  four stable static core files (`wp-includes/js/wp-emoji-release.min.js`,
  `wp-includes/js/wp-embed.min.js`, `wp-includes/js/wp-util.min.js`,
  `wp-admin/js/common.min.js`) fetched from
  `https://core.svn.wordpress.org/tags/<version>/`.
- Each file path maps md5 hex digests onto the versions carrying them,
  newest version first (clients take the first listed). Files that do not
  exist in a version (404) are simply skipped.
- Deterministic `gzip -9 -n`; signed with the same onyx-minisign key
  (verify with `ONYX_DB_PUBKEY`).
- Published onto the latest daily `v<date>` release when one exists,
  otherwise on a standalone `fingerprints-<date>` release. All failures are
  soft: a failed build warns and publishes nothing; clients are unaffected.

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
