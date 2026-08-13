#!/usr/bin/env node
/**
 * Emit public/sitemap.xml listing the ahoxy URLs that still 301 into the family.
 *
 * A sitemap of redirecting URLs looks wrong, and on 2026-08-12 it was deleted
 * for exactly that reason ("no indexable page left"). That reasoning was made
 * without a fact that surfaced on 2026-08-13: ahoxy.com had been answering
 * Googlebot with 403 since roughly 2026-07-11 (Bot Fight Mode), so Google had
 * never read a single one of these 301s. Once the block was lifted the URLs
 * still needed a reason to be re-fetched, and the sitemap is Google's own
 * documented lever for exactly this — during a site move you submit the OLD
 * URLs so the redirects get processed.
 *
 * So: this file is a migration aid, not an index request. GSC will file every
 * entry under "Page with redirect", which is the intended outcome, not a defect.
 * Retire it once the destinations hold the rankings.
 *
 * The input is a measured list (scripts/recrawl-sitemap-urls.json): ahoxy paths
 * that earned at least one impression in the 90 days to 2026-08-11 AND were
 * confirmed live to answer 301. The ~600 mapped paths with no traffic are left
 * out on purpose — crawl budget is the family's bottleneck, so spending it on
 * URLs that hold no equity would work against the point.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const { paths } = JSON.parse(
  readFileSync(join(root, "scripts/recrawl-sitemap-urls.json"), "utf8"),
);

const lastmod = new Date().toISOString().slice(0, 10);
const body = paths
  .map((p) => `  <url><loc>https://ahoxy.com${p}</loc><lastmod>${lastmod}</lastmod></url>`)
  .join("\n");

writeFileSync(
  join(root, "public/sitemap.xml"),
  `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${body}\n</urlset>\n`,
);

console.log(`sitemap.xml: ${paths.length} redirecting URL(s), lastmod ${lastmod}`);
