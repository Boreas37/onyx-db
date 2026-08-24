#!/usr/bin/env python3
"""Generate fingerprints.json — md5 digests of stable WordPress core assets
per version, for onyx's --fingerprint-db.

Output shape (exactly what the onyx client expects):
    {"files": {"wp-includes/js/wp-emoji-release.min.js":
                  {"<md5hex>": ["7.1", "7.0"], ...}, ...}}

Each file path maps an md5 hex digest of its release content onto the core
versions known to carry it, newest version first (clients take vers[0]).

Sources:
    - version list: https://api.wordpress.org/core/version-check/1.7/ (offers)
    - asset bytes:  https://core.svn.wordpress.org/tags/<version>/<path>

Covers the last 6 stable versions (current + 5 previous); per-file download
failures are skipped with a warning so partial data still publishes. Pure
stdlib, no external dependencies.

Usage: python3 gen_fingerprints.py [OUTPUT.json]   (default: fingerprints.json)
Exit status: 0 on success; 1 when the version list cannot be fetched.
"""

import hashlib
import json
import re
import sys
import urllib.error
import urllib.request

VERSION_CHECK_URL = "https://api.wordpress.org/core/version-check/1.7/"
BASE_URL = "https://core.svn.wordpress.org/tags"
STABLE_RE = re.compile(r"^\d+\.\d+(?:\.\d+)?$")
MAX_VERSIONS = 6
TIMEOUT = 30
USER_AGENT = "onyx-db-mirror (fingerprint generator)"
FILES = [
    "wp-includes/js/wp-emoji-release.min.js",
    "wp-includes/js/wp-embed.min.js",
    "wp-includes/js/wp-util.min.js",
    "wp-admin/js/common.min.js",
]


def version_key(v):
    return tuple(int(part) for part in v.split("."))


def fetch_json(url):
    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.load(resp)


def fetch_bytes(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def stable_versions():
    doc = fetch_json(VERSION_CHECK_URL)
    versions = set()
    if doc.get("current"):
        versions.add(doc["current"])
    for offer in doc.get("offers", []):
        v = offer.get("version")
        if v and STABLE_RE.match(v):
            versions.add(v)
    ordered = sorted(versions, key=version_key, reverse=True)
    return ordered[:MAX_VERSIONS]


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "fingerprints.json"
    try:
        versions = stable_versions()
    except Exception as exc:
        print(f"error: wordpress.org version check unreachable: {exc}", file=sys.stderr)
        return 1
    print(f"fingerprinting {len(versions)} stable versions: {', '.join(versions)}")
    if not versions:
        print("error: no stable versions found", file=sys.stderr)
        return 1
    files = {path: {} for path in FILES}
    for version in versions:
        for path in FILES:
            url = f"{BASE_URL}/{version}/{path}"
            try:
                body = fetch_bytes(url)
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    print(f"  skip {version} {path} (404)")
                else:
                    print(f"  warn {version} {path}: HTTP {exc.code}", file=sys.stderr)
                continue
            except Exception as exc:
                print(f"  warn {version} {path}: {exc}", file=sys.stderr)
                continue
            digest = hashlib.md5(body).hexdigest()
            files[path].setdefault(digest, []).append(version)
            print(f"  {version} {path} -> {digest}")
    doc = {"files": {p: files[p] for p in files if files[p]}}
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(doc, ensure_ascii=True, separators=(",", ":"), sort_keys=True))
    total = sum(len(hashes) for hashes in doc["files"].values())
    print(f"wrote {out_path}: {len(doc['files'])} files, {total} distinct md5 entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
