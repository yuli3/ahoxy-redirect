#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const sitemap = fs.readFileSync(path.join(root, "public/sitemap.xml"), "utf8");
const robots = fs.readFileSync(path.join(root, "public/robots.txt"), "utf8");
const urls = [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map((match) => match[1]);

if (urls.length !== 1 || urls[0] !== "https://ahoxy.com/ko/kbd/") {
  throw new Error(`Ahoxy sitemap must contain only the indexable kbd route; got ${JSON.stringify(urls)}`);
}
if (!robots.includes("Sitemap: https://ahoxy.com/sitemap.xml")) {
  throw new Error("robots.txt must advertise the canonical sitemap");
}
if (/utm_|\/404|https:\/\/ahoxy\.com\/$/.test(sitemap)) {
  throw new Error("redirect, bridge, or tracking URL leaked into sitemap");
}

console.log("Ahoxy sitemap audit: PASS (1 indexable URL; no bridge/redirect URLs)");
