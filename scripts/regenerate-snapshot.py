#!/usr/bin/env python3
"""Regenerate scripts/expected-redirects.snapshot.json from route ownership.

Only needed when an oiyo canonical URL moves. ahoxy.com is a finished redirect
shell, so the normal state is "never run this".

Requires the coding/ monorepo checked out next to (or containing) this repo,
because the source of truth lives there:

    coding/docs/route-ownership.json
    coding/docs/audit-ahoxy-redirects.py

If the local ahoxy checkout was deleted (2026-08-04 plan) clone it back first:

    git clone https://github.com/yuli3/ahoxy-redirect.git
"""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE / "expected-redirects.snapshot.json"

# Try the monorepo layout (coding/ahoxy/scripts) first, then a sibling checkout.
CANDIDATES = [
    HERE.parents[1] / "docs",
    HERE.parents[2] / "coding" / "docs",
]


def find_docs() -> Path:
    for candidate in CANDIDATES:
        if (candidate / "audit-ahoxy-redirects.py").is_file():
            return candidate
    sys.exit(
        "coding/docs not found. Checked:\n  "
        + "\n  ".join(str(c) for c in CANDIDATES)
        + "\nClone or place the coding/ monorepo alongside this repo and retry."
    )


def main() -> int:
    docs = find_docs()
    spec = importlib.util.spec_from_file_location("aar", docs / "audit-ahoxy-redirects.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    specs = module.expected_redirect_specs(module.load_manifest())

    previous = json.loads(SNAPSHOT.read_text(encoding="utf-8")) if SNAPSHOT.is_file() else {}
    payload = {
        "_comment": previous.get("_comment", []),
        "generatedAt": date.today().isoformat(),
        "sourceManifest": "coding/docs/route-ownership.json",
        "specs": specs,
    }
    SNAPSHOT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    before = len(previous.get("specs", []))
    print(f"snapshot regenerated: {before} -> {len(specs)} spec(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
