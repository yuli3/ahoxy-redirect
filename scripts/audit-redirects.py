#!/usr/bin/env python3
"""Validate Ahoxy migration redirects against a frozen expectation snapshot.

Self-contained: reads only files inside this repository, so CI can run it with
just ahoxy-redirect checked out. (Until 2026-08-04 this was invoked as
`python3 ../docs/audit-ahoxy-redirects.py`, which does not exist in a GitHub
Actions checkout - CI had been failing on that since 2026-07-30.)

Where the expectations come from: coding/docs/route-ownership.json decides where
legacy ahoxy.com traffic should go. ahoxy.com is now a finished redirect shell
that no longer changes, so those expectations are frozen into
scripts/expected-redirects.snapshot.json rather than re-derived on every run.

Trade-off, stated plainly: if an oiyo canonical URL moves, this audit will not
notice. That is the accepted cost of letting the local ahoxy checkout go away.
Regenerate the snapshot with scripts/regenerate-snapshot.py when the coding/
monorepo is available.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "scripts" / "expected-redirects.snapshot.json"
REDIRECTS_PATH = ROOT / "public" / "_redirects"

VARIABLES = {
    "BLOG": "https://blog.oiyo.net",
    "OIYO": "https://oiyo.net",
}

# ahoxy/public/_redirects is generated (scripts/generate-redirects.mjs) with
# one literal rule per locale rather than a single ":locale" placeholder rule,
# e.g. "/ko/height-converter ... 301" + "/en/height-converter ... 301" instead
# of "/:locale/height-converter ...". These are the locales it expands.
KNOWN_LOCALES = ("ko", "en", "ja", "es")
LOCALE_SOURCE_RE = re.compile(r"^/(" + "|".join(KNOWN_LOCALES) + r")(/.*)$")

# "<source> <destination> <status>" — comment lines start with "#".
REDIRECT_LINE_RE = re.compile(r"^(\S+)\s+(\S+)\s+(\d{3})$")

PERMANENT_STATUSES = {"301", "308"}

CRITICAL_REDIRECTS = [
    {
        "routeId": "critical.ahoxy.root.aim-trainer",
        "source": "/aim-trainer",
        "target": "https://game.oiyo.net/ko/aim-trainer",
        "campaign": "aim-trainer",
    },
    {
        "routeId": "critical.ahoxy.root.gomoku",
        "source": "/gomoku",
        "target": "https://game.oiyo.net/ko/gomoku",
        "campaign": "gomoku",
    },
    {
        "routeId": "critical.ahoxy.root.tier",
        "source": "/tier",
        "target": "https://game.oiyo.net/ko/tier-list",
        "campaign": "tier-list",
    },
    {
        "routeId": "critical.ahoxy.root.minesweeper",
        "source": "/minesweeper",
        "target": "https://game.oiyo.net/ko/minesweeper",
        "campaign": "minesweeper",
    },
    {
        "routeId": "critical.ahoxy.root.wordle",
        "source": "/wordle",
        "target": "https://game.oiyo.net/ko/wordle",
        "campaign": "wordle",
    },
    {
        "routeId": "critical.ahoxy.root.kbd2",
        "source": "/kbd2",
        "target": "https://blog.oiyo.net/ko/game-keyboard-reaction-test",
        "campaign": "game-keyboard-reaction-test",
    },
    {
        "routeId": "critical.ahoxy.root.typing-test",
        "source": "/typing-test",
        "target": "https://blog.oiyo.net/en/typing-test",
        "campaign": "typing-test",
    },
    {
        "routeId": "critical.ahoxy.locale.typing-test",
        "source": "/:locale/typing-test",
        "target": "https://blog.oiyo.net/{locale}/typing-test",
        "campaign": "typing-test",
    },
    {
        "routeId": "critical.ahoxy.root.menu",
        "source": "/menu",
        "target": "https://blog.oiyo.net/ko/tool-life-utilities",
        "campaign": "tool-life-utilities",
    },
    {
        "routeId": "critical.ahoxy.root.name",
        "source": "/name",
        "target": "https://blog.oiyo.net/ko/tool-life-utilities",
        "campaign": "tool-life-utilities",
    },
    {
        "routeId": "critical.ahoxy.root.emoji",
        "source": "/emoji",
        "target": "https://blog.oiyo.net/ko/tool-life-utilities",
        "campaign": "tool-life-utilities",
    },
    {
        "routeId": "critical.ahoxy.root.worldclock",
        "source": "/worldclock",
        "target": "https://blog.oiyo.net/ko/tool-life-utilities",
        "campaign": "tool-life-utilities",
    },
    {
        "routeId": "critical.ahoxy.root.height-converter",
        "source": "/height-converter",
        "target": "https://blog.oiyo.net/en/height-converter",
        "campaign": "height-converter",
    },
    {
        "routeId": "critical.ahoxy.root.percent-converter",
        "source": "/percent-converter",
        "target": "https://blog.oiyo.net/en/percent-converter",
        "campaign": "percent-converter",
    },
    {
        "routeId": "critical.ahoxy.root.angle-converter",
        "source": "/angle-converter",
        "target": "https://blog.oiyo.net/en/angle-converter",
        "campaign": "angle-converter",
    },
    {
        "routeId": "critical.ahoxy.root.fraction-converter",
        "source": "/fraction-converter",
        "target": "https://blog.oiyo.net/en/fraction-converter",
        "campaign": "fraction-converter",
    },
    {
        "routeId": "critical.ahoxy.root.scientific-notation",
        "source": "/scientific-notation",
        "target": "https://blog.oiyo.net/en/scientific-notation-converter",
        "campaign": "scientific-notation",
    },
    {
        "routeId": "critical.ahoxy.root.hex-converter",
        "source": "/hex-converter",
        "target": "https://blog.oiyo.net/en/color-converter",
        "campaign": "hex-converter",
    },
    {
        "routeId": "critical.ahoxy.root.resolution",
        "source": "/resolution",
        "target": "https://blog.oiyo.net/en/aspect-ratio-calculator",
        "campaign": "resolution",
    },
    {
        "routeId": "critical.ahoxy.root.number-converter",
        "source": "/number-converter",
        "target": "https://blog.oiyo.net/en/number-base-converter",
        "campaign": "number-converter",
    },
    {
        "routeId": "critical.ahoxy.root.ratio",
        "source": "/ratio",
        "target": "https://blog.oiyo.net/en/ratio-calculator",
        "campaign": "ratio",
    },
    {
        "routeId": "critical.ahoxy.root.universal-converter",
        "source": "/universal-converter",
        "target": "https://blog.oiyo.net/en/universal-converter",
        "campaign": "universal-converter",
    },
    {
        "routeId": "critical.ahoxy.root.wage",
        "source": "/wage",
        "target": "https://blog.oiyo.net/ko/salary-calculator-complete-guide",
        "campaign": "salary-calculator-complete-guide",
    },
    {
        "routeId": "critical.ahoxy.locale.wage",
        "source": "/:locale/wage",
        "target": "https://blog.oiyo.net/ko/salary-calculator-complete-guide",
        "campaign": "salary-calculator-complete-guide",
    },
    {
        "routeId": "critical.ahoxy.locale.menu",
        "source": "/:locale/menu",
        "target": "https://oiyo.net/{locale}/menu/roulette",
        "campaign": "menu-roulette",
        "trailingSlash": True,
    },
    {
        "routeId": "critical.ahoxy.locale.dday",
        "source": "/:locale/dday",
        "target": "https://blog.oiyo.net/{locale}/dday-counter",
        "campaign": "dday-counter",
        "trailingSlash": True,
    },
    {
        "routeId": "critical.ahoxy.locale.empathy-test",
        "source": "/:locale/empathy-test",
        "target": "https://oiyo.net/{locale}/empathy/test",
        "campaign": "empathy-test",
        "trailingSlash": True,
    },
    {
        "routeId": "critical.ahoxy.locale.mbti",
        "source": "/:locale/mbti",
        "target": "https://oiyo.net/{locale}/mbti/test",
        "campaign": "mbti-test",
        "trailingSlash": True,
    },
    {
        "routeId": "critical.ahoxy.locale.animal-type",
        "source": "/:locale/animal-type",
        "target": "https://oiyo.net/{locale}/animal-personality-test",
        "campaign": "animal-personality-test",
        "trailingSlash": True,
    },
    {
        "routeId": "critical.ahoxy.locale.chimp-test",
        "source": "/:locale/chimp-test",
        "target": "https://oiyo.net/{locale}/chimp-test",
        "campaign": "chimp-test",
        "trailingSlash": True,
    },
    {
        "routeId": "critical.ahoxy.locale.comstyle",
        "source": "/:locale/comstyle",
        "target": "https://oiyo.net/{locale}/communication-style-test",
        "campaign": "communication-style-test",
        "trailingSlash": True,
    },
    {
        "routeId": "critical.ahoxy.locale.kurodoko",
        "source": "/:locale/kurodoko",
        "target": "https://game.oiyo.net/{locale}/kurodoko",
        "campaign": "kurodoko",
        "trailingSlash": True,
    },
    {
        "routeId": "critical.ahoxy.locale.digital-balance",
        "source": "/:locale/digital-balance",
        "target": "https://oiyo.net/{locale}/digital-balance-test",
        "campaign": "digital-balance-test",
        "trailingSlash": True,
    },
    {
        "routeId": "critical.ahoxy.locale.digital-wellbeing",
        "source": "/:locale/digital-wellbeing",
        "target": "https://oiyo.net/{locale}/digital-balance-test",
        "campaign": "digital-balance-test",
        "trailingSlash": True,
    },
]


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(2)


def load_snapshot() -> list[dict[str, Any]]:
    try:
        data = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"snapshot not found: {SNAPSHOT_PATH}")
    except json.JSONDecodeError as exc:
        fail(f"invalid snapshot JSON: {exc.lineno}:{exc.colno}: {exc.msg}")
    specs = data.get("specs")
    if not isinstance(specs, list):
        fail("snapshot must contain a 'specs' list")
    return specs


def expand_destination(raw: str) -> str:
    expanded = raw
    for name, value in VARIABLES.items():
        expanded = expanded.replace("${" + name + "}", value)
    return expanded


def normalize_target(raw: str) -> str:
    expanded = expand_destination(raw)
    parts = urlsplit(expanded)
    if not parts.scheme or not parts.netloc:
        return expanded.rstrip("/")
    path = parts.path.rstrip("/") or "/"
    path = path.replace("/:locale", "/{locale}")
    path = re.sub(r"/:([A-Za-z0-9_]+)", r"/{\1}", path)
    return f"{parts.scheme}://{parts.netloc}{path}"


def query_params(raw: str) -> dict[str, str]:
    parts = urlsplit(expand_destination(raw))
    parsed = parse_qs(parts.query, keep_blank_values=True)
    return {key: values[-1] if values else "" for key, values in parsed.items()}


def source_from_legacy_pattern(pattern: str) -> str:
    parts = urlsplit(pattern)
    if parts.netloc and parts.netloc != "ahoxy.com":
        fail(f"unsupported legacy host in pattern: {pattern}")
    path = parts.path.rstrip("/") or "/"
    return re.sub(r"/\{([A-Za-z0-9_]+)\}", r"/:\1", path)


def _synthesize_locale_wildcards(
    redirects: dict[str, list[dict[str, Any]]],
    locale_groups: dict[str, dict[str, dict[str, Any]]],
) -> None:
    """Rebuild ":locale" wildcard sources the manifest expects.

    route-ownership.json expresses ahoxy legacy paths as e.g.
    "https://ahoxy.com/{locale}/height-converter", which source_from_legacy_pattern()
    turns into the literal source "/:locale/height-converter". The deployed
    _redirects file has no such wildcard rule — generate-redirects.mjs expands it
    into one literal rule per locale instead. Reconstruct a single aggregate entry
    per suffix so those manifest-driven specs still have something to match against.
    """
    for suffix, by_locale in locale_groups.items():
        # A wildcard contract represents every Ahoxy locale. Never synthesize it
        # from a partial group, or one missing generated locale could pass audit.
        if set(by_locale) != set(KNOWN_LOCALES):
            continue
        wildcard_source = f"/:locale{suffix}"
        if wildcard_source in redirects:
            continue

        destinations = {entry["destination"] for entry in by_locale.values()}
        if len(destinations) == 1:
            # Every locale funnels to the same fixed target (not locale-preserving,
            # e.g. /en|ja|es/wage all landing on the ko guide). Keep it as-is.
            template_destination = next(iter(destinations))
        else:
            templated_destinations: set[str] = set()
            consistent = True
            for locale, entry in by_locale.items():
                parts = urlsplit(entry["destination"])
                prefix = f"/{locale}"
                if parts.path != prefix and not parts.path.startswith(prefix + "/"):
                    consistent = False
                    break
                templated_path = "/:locale" + parts.path[len(prefix):]
                templated_destinations.add(
                    urlunsplit((parts.scheme, parts.netloc, templated_path, parts.query, parts.fragment))
                )
            if not consistent or len(templated_destinations) != 1:
                # Locale segment doesn't map cleanly (e.g. differs per locale for
                # reasons other than the locale itself) — leave unresolved so the
                # audit surfaces a missing-source error instead of guessing.
                continue
            template_destination = next(iter(templated_destinations))

        lines = sorted(entry["line"] for entry in by_locale.values())
        redirects[wildcard_source] = [
            {
                "source": wildcard_source,
                "destination": template_destination,
                "permanent": all(entry["permanent"] for entry in by_locale.values()),
                "line": lines[0],
            }
        ]


def load_redirects() -> dict[str, list[dict[str, Any]]]:
    try:
        text = REDIRECTS_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"redirects file not found: {REDIRECTS_PATH}")

    redirects: dict[str, list[dict[str, Any]]] = {}
    locale_groups: dict[str, dict[str, dict[str, Any]]] = {}

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = REDIRECT_LINE_RE.match(line)
        if not match:
            fail(f"unparseable _redirects line {line_no}: {raw_line!r}")
        source, destination, status = match.groups()
        entry = {
            "source": source,
            "destination": destination,
            "permanent": status in PERMANENT_STATUSES,
            "line": line_no,
        }
        redirects.setdefault(source, []).append(entry)

        locale_match = LOCALE_SOURCE_RE.match(source)
        if locale_match:
            locale, suffix = locale_match.groups()
            locale_groups.setdefault(suffix, {})[locale] = entry

    _synthesize_locale_wildcards(redirects, locale_groups)
    return redirects



def audit() -> tuple[list[str], list[str], int]:
    redirects = load_redirects()
    specs = load_snapshot() + CRITICAL_REDIRECTS

    errors: list[str] = []
    warnings: list[str] = []

    for spec in specs:
        source = spec["source"]
        candidates = redirects.get(source, [])
        if not candidates:
            errors.append(f"{spec['routeId']}: missing redirect source {source}")
            continue

        matching = [item for item in candidates if normalize_target(item["destination"]) == spec["target"]]
        if not matching:
            details = ", ".join(
                f"line {item['line']} -> {normalize_target(item['destination'])}" for item in candidates
            )
            errors.append(f"{spec['routeId']}: {source} does not target {spec['target']} ({details})")
            continue

        item = matching[0]
        if not item["permanent"]:
            errors.append(f"{spec['routeId']}: {source} redirect must be permanent")

        params = query_params(item["destination"])
        if params.get("utm_source") != "ahoxy":
            errors.append(f"{spec['routeId']}: {source} missing utm_source=ahoxy")
        if params.get("utm_medium") != "redirect":
            errors.append(f"{spec['routeId']}: {source} missing utm_medium=redirect")
        campaign = spec.get("campaign")
        if campaign and params.get("utm_campaign") != campaign:
            errors.append(f"{spec['routeId']}: {source} missing utm_campaign={campaign}")
        if spec.get("trailingSlash"):
            path = urlsplit(expand_destination(item["destination"])).path
            if not path.endswith("/"):
                errors.append(f"{spec['routeId']}: {source} destination must end with / to avoid a normalization hop")

    if not specs:
        warnings.append("no configured ahoxy migration redirects found in the expectation snapshot")

    return errors, warnings, len(specs)


def main() -> int:
    errors, warnings, count = audit()
    for warning in warnings:
        print(f"WARN: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    print(f"ahoxy redirect audit: {count} migration redirect(s), {len(warnings)} warnings, {len(errors)} errors")
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
