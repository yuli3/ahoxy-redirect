#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

/**
 * ahoxy.com is a pure redirect shell. Until 2026-08-12 it still served one real
 * page — the 아재패턴 trainer at /ko/kbd — and this audit asserted the sitemap
 * listed exactly that URL. The trainer now lives at
 * game.oiyo.net/:locale/lostark-ajae-pattern and /ko/kbd 301s to it, so there is
 * nothing left to index and the sitemap is gone.
 *
 * Crawling must stay allowed: the whole point of the shell is that search
 * engines read the 301s and move the equity to the family.
 */
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const robots = fs.readFileSync(path.join(root, "public/robots.txt"), "utf8");

if (fs.existsSync(path.join(root, "public/sitemap.xml"))) {
  throw new Error("this shell has no indexable page; a sitemap would advertise redirects");
}
if (/^\s*Sitemap:/m.test(robots)) {
  throw new Error("robots.txt still advertises a sitemap that no longer exists");
}
if (!/^\s*Allow:\s*\/\s*$/m.test(robots)) {
  throw new Error("crawling must stay allowed so the 301s can be discovered");
}

console.log("Ahoxy sitemap audit: PASS (redirect shell, no indexable URL, crawling allowed)");
