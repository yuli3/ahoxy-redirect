#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

/**
 * ahoxy.com is a pure redirect shell, and its sitemap deliberately lists URLs
 * that 301. See scripts/generate-sitemap.mjs for why that is the intent rather
 * than a defect — in short, Googlebot was blocked from this host for a month
 * and the 301s have to be re-fetched before any equity moves.
 *
 * What this audit protects:
 *   - the sitemap exists and is non-empty (it was deleted once already)
 *   - every entry is an ahoxy.com URL drawn from the measured recrawl list
 *   - robots.txt advertises it, and still allows crawling
 */
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const robots = fs.readFileSync(path.join(root, "public/robots.txt"), "utf8");
const sitemapPath = path.join(root, "public/sitemap.xml");

if (!fs.existsSync(sitemapPath)) {
  throw new Error("sitemap.xml is missing; the 301s have no recrawl trigger (npm run sitemap)");
}

const sitemap = fs.readFileSync(sitemapPath, "utf8");
const locs = [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1]);
const { paths: expected } = JSON.parse(
  fs.readFileSync(path.join(root, "scripts/recrawl-sitemap-urls.json"), "utf8"),
);

if (locs.length === 0) {
  throw new Error("sitemap.xml lists no URL");
}
if (locs.length !== expected.length) {
  throw new Error(
    `sitemap.xml has ${locs.length} URL(s) but the recrawl list has ${expected.length}; run npm run sitemap`,
  );
}

const expectedUrls = new Set(expected.map((p) => `https://ahoxy.com${p}`));
const stray = locs.filter((u) => !expectedUrls.has(u));
if (stray.length) {
  throw new Error(`sitemap.xml lists URL(s) outside the measured recrawl list: ${stray.slice(0, 3).join(", ")}`);
}

if (!/^\s*Sitemap:\s*https:\/\/ahoxy\.com\/sitemap\.xml\s*$/m.test(robots)) {
  throw new Error("robots.txt must advertise https://ahoxy.com/sitemap.xml");
}
if (!/^\s*Allow:\s*\/\s*$/m.test(robots)) {
  throw new Error("crawling must stay allowed so the 301s can be discovered");
}

console.log(`Ahoxy sitemap audit: PASS (${locs.length} redirecting URL(s), advertised, crawling allowed)`);
