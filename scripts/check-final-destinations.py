#!/usr/bin/env python3
"""Follow every ahoxy redirect to its final destination and flag extra hops.

audit-redirects.py checks only the first hop against a frozen snapshot. That
missed destinations that moved again later (2026-11-09: /menu landed on a
deleted blog hub, /:locale/menu went oiyo.net -> tools.oiyo.net). This script
looks past the first hop.

Two modes:

  offline (default): resolve chains through the family repos' own
    public/_redirects files. Pass each checkout as HOST=PATH, e.g.
      python3 scripts/check-final-destinations.py \
        blog.oiyo.net=../blog-oiyo oiyo.net=../oiyo-astro
    Hosts without a checkout are treated as final.

  --online: send HEAD requests (no auto-follow) and chase Location headers.
    Use after a deploy. Slow on purpose (one request at a time).

  --write: (offline) also save scripts/family-final.json, a map from each
    first-hop URL to its final URL. generate-redirects.mjs applies it, so the
    shell 301s straight to the final page. Re-run after any family URL move.

Exit code 1 when any rule needs more than one hop or ends in 4xx/5xx.
Query strings (utm) are ignored when matching.
"""
from __future__ import annotations

import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
LINE_RE = re.compile(r"^(\S+)\s+(\S+)\s+(\d{3})$")
MAX_HOPS = 6


def load_rules(path: Path) -> dict[str, str]:
    rules: dict[str, str] = {}
    if not path.exists():
        return rules
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = LINE_RE.match(line)
        if not m or not m.group(3).startswith("3"):
            continue
        src, dst = m.group(1), m.group(2)
        if "*" in src or ":" in src:
            continue  # only exact rules; splats are rare in the family files
        rules.setdefault(src, dst)
    return rules


def offline_next(url: str, families: dict[str, dict[str, str]]) -> str | None:
    parts = urlsplit(url)
    rules = families.get(parts.netloc)
    if rules is None:
        return None
    path = parts.path or "/"
    for candidate in (path, path.rstrip("/") or "/", path.rstrip("/") + "/"):
        if candidate in rules:
            nxt = rules[candidate]
            if nxt.startswith("/"):
                nxt = f"{parts.scheme}://{parts.netloc}{nxt}"
            return nxt
    return None


class NoFollow(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # noqa: D401
        return None


OPENER = urllib.request.build_opener(NoFollow)


def online_step(url: str) -> tuple[int, str | None]:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "ahoxy-redirect-audit"})
    try:
        resp = OPENER.open(req, timeout=15)
        return resp.status, None
    except urllib.error.HTTPError as err:
        loc = err.headers.get("Location")
        if loc and loc.startswith("/"):
            p = urlsplit(url)
            loc = f"{p.scheme}://{p.netloc}{loc}"
        return err.code, loc


def strip_query(url: str) -> str:
    p = urlsplit(url)
    return f"{p.scheme}://{p.netloc}{p.path}"


def main(argv: list[str]) -> int:
    online = "--online" in argv
    families: dict[str, dict[str, str]] = {}
    for arg in argv:
        if "=" in arg and not arg.startswith("--"):
            host, path = arg.split("=", 1)
            families[host] = load_rules(Path(path) / "public" / "_redirects")

    ahoxy = load_rules(ROOT / "public" / "_redirects")
    problems = 0
    final_map: dict[str, str] = {}
    for src, first in sorted(ahoxy.items()):
        chain = [strip_query(first)]
        status = None
        url = first
        for _ in range(MAX_HOPS):
            if online:
                status, nxt = online_step(url)
            else:
                nxt = offline_next(url, families)
            if not nxt:
                break
            chain.append(strip_query(nxt))
            url = nxt
        bad_status = online and status is not None and status >= 400
        if len(chain) > 1:
            final_map[chain[0]] = chain[-1]
        if len(chain) > 1 or bad_status:
            problems += 1
            tail = f" [{status}]" if online else ""
            print(f"{src}: " + " -> ".join(chain) + tail)
    if "--write" in argv and not online:
        import json

        out = ROOT / "scripts" / "family-final.json"
        merged = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
        merged.update(final_map)
        out.write_text(json.dumps(dict(sorted(merged.items())), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {out.name}: {len(merged)} entries")
    print(f"final-destination check: {len(ahoxy)} rule(s), {problems} with extra hops or errors")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
