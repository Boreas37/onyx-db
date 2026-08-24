#!/usr/bin/env python3
"""Generate popular.json — the most popular WordPress.org plugins and themes.

Output shape (exactly what the onyx client expects):
    {"plugins": ["akismet", "contact-form-7", ...],
     "themes":  ["twentytwentyfive", "generatepress", ...],
     "counts_plugins": {"akismet": 5000000, ...},
     "counts_themes":  {"twentytwentyfive": 3000000, ...}}

Slugs are lowercase, deduplicated, in popularity-descending order (the order
the wordpress.org API returns them), capped at 500 plugins / 100 themes.
The counts_* maps hold the wordpress.org `active_installs` figure (int >= 0)
for exactly the slugs that made the list; an item whose active_installs is
missing is kept in the slug list with a count of 0. The counts maps are
optional on the client side: absence means "no counts available".
Pure stdlib, no external dependencies.

Usage: python3 gen_popular.py [OUTPUT.json]   (default: popular.json)
Exit status: 0 on success; 1 when the API is unreachable or the payload
cannot be parsed — callers treat that as "publish without the asset".
"""

import json
import sys
import urllib.parse
import urllib.request

PLUGINS_URL = "https://api.wordpress.org/plugins/info/1.2/"
THEMES_URL = "https://api.wordpress.org/themes/info/1.2/"
TIMEOUT = 30
PLUGIN_CAP = 500
THEME_CAP = 100
USER_AGENT = "onyx-db-mirror (popular seed generator)"


def fetch(url, params):
    query = urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url + "?" + query,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.load(resp)


def collect(section, cap):
    slugs = []
    counts = {}
    seen = set()
    for item in section:
        slug = item.get("slug")
        if not slug:
            continue
        slug = str(slug).strip().lower()
        if not slug or slug in seen:
            continue
        seen.add(slug)
        count = item.get("active_installs", 0)
        if count is None:
            count = 0
        else:
            try:
                count = int(count)
            except (TypeError, ValueError):
                count = 0
        counts[slug] = count if count >= 0 else 0
        slugs.append(slug)
        if len(slugs) >= cap:
            break
    return slugs, counts


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "popular.json"
    try:
        plugins = fetch(PLUGINS_URL, {
            "action": "query_plugins",
            "request[browse]": "popular",
            "request[per_page]": PLUGIN_CAP,
            "request[page]": 1,
        })
        themes = fetch(THEMES_URL, {
            "action": "query_themes",
            "request[browse]": "popular",
            "request[per_page]": THEME_CAP,
            "request[page]": 1,
        })
    except Exception as exc:
        print(f"error: wordpress.org API unreachable: {exc}", file=sys.stderr)
        return 1
    plugins_slugs, plugins_counts = collect(plugins.get("plugins", []), PLUGIN_CAP)
    themes_slugs, themes_counts = collect(themes.get("themes", []), THEME_CAP)
    if not plugins_slugs and not themes_slugs:
        print("error: both popular lists came back empty", file=sys.stderr)
        return 1
    doc = {
        "plugins": plugins_slugs,
        "themes": themes_slugs,
        "counts_plugins": plugins_counts,
        "counts_themes": themes_counts,
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(doc, ensure_ascii=True, separators=(",", ":")))
    print(f"wrote {out_path}: {len(plugins_slugs)} plugins, {len(themes_slugs)} themes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
