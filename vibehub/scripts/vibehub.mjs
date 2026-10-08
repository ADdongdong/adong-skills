#!/usr/bin/env node

import { readFileSync } from "node:fs";

const BUNDLED_CONFIG = JSON.parse(
  readFileSync(new URL("../vibehub.config.json", import.meta.url), "utf8"),
);

const HELP = `VibeHub terminology resolver

Usage:
  node scripts/vibehub.mjs resolve --query "Tooltip" [--query "Hover"] [options]

Options:
  --query <term>    Candidate term to verify. Repeat up to 3 times.
  --site-url <url>  VibeHub site origin. Overrides VIBEHUB_SITE_URL and bundled config.
  --limit <1-5>     Results per query. Defaults to 1.
  --compact         Return search summaries without fetching lesson details.
  --timeout <ms>    Request timeout. Defaults to 10000.
  --help            Show this help.
`;

const PRIVATE_VALUE_PATTERNS = [
  /\b(?:bearer\s+)[a-z0-9._~+/-]+=*/gi,
  /\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password|passwd|token)\s*[:=]\s*["']?[^\s"'&,;]+/gi,
  /\beyJ[a-zA-Z0-9_-]{16,}\.[a-zA-Z0-9_-]{8,}\.[a-zA-Z0-9_-]{8,}\b/g,
];

function parseArgs(argv) {
  const [command, ...rest] = argv;
  const options = {};
  for (let index = 0; index < rest.length; index += 1) {
    const token = rest[index];
    if (!token.startsWith("--")) throw new Error(`Unexpected argument: ${token}`);
    const key = token.slice(2).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
    if (key === "help" || key === "compact") {
      options[key] = true;
      continue;
    }
    const value = rest[index + 1];
    if (!value || value.startsWith("--")) throw new Error(`Missing value for ${token}`);
    if (key === "query") {
      options.query = [...(options.query || []), value];
    } else {
      options[key] = value;
    }
    index += 1;
  }
  return { command, options };
}

function normalizeSiteUrl(value) {
  const url = new URL(value);
  if (!["http:", "https:"].includes(url.protocol)) {
    throw new Error("site URL must use http or https");
  }
  url.pathname = url.pathname.replace(/\/+$/, "");
  url.search = "";
  url.hash = "";
  return url.toString().replace(/\/$/, "");
}

function configuredSiteUrl(options) {
  const value = options.siteUrl || process.env.VIBEHUB_SITE_URL || BUNDLED_CONFIG.siteUrl;
  if (!value) throw new Error("VibeHub site URL is missing from bundled config");
  return normalizeSiteUrl(value);
}

function sanitizeRemoteText(value, maxLength) {
  let text = String(value || "")
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/https?:\/\/[^\s<>"')\]]+/gi, " ")
    .replace(/\b[A-Z]:\\(?:[^\\\s]+\\)*[^\\\s]*/gi, " ")
    .replace(/(?:^|[\s("'`])\/(?:Users|home|var|private|opt|srv|workspace|projects?)\/[^\s"'`)]+/g, " ")
    .replace(/\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi, " ");
  for (const pattern of PRIVATE_VALUE_PATTERNS) text = text.replace(pattern, " ");
  return text.replace(/\s+/g, " ").trim().slice(0, maxLength);
}

function output(value) {
  process.stdout.write(`${JSON.stringify(value, null, 2)}\n`);
}

function fail(code, message) {
  output({ ok: false, error: { code, message } });
  process.exitCode = 1;
}

async function fetchJson(url, { timeout, label }) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(url, {
      headers: { Accept: "application/json" },
      signal: controller.signal,
    });
    const payload = await response.json().catch(() => null);
    if (!response.ok) {
      const apiMessage = payload?.error?.message;
      throw new Error(`${label} returned HTTP ${response.status}${apiMessage ? `: ${apiMessage}` : ""}`);
    }
    if (!payload || typeof payload !== "object") throw new Error(`${label} did not return JSON`);
    return payload;
  } finally {
    clearTimeout(timer);
  }
}

function requireData(payload, label) {
  if (!payload.data || typeof payload.data !== "object") {
    throw new Error(`${label} response is missing data`);
  }
  return payload.data;
}

function compactCandidate(summary, detail) {
  return {
    id: detail.id || summary.id,
    title: detail.title || summary.title,
    secondaryTitle: detail.secondaryTitle || summary.secondaryTitle || null,
    aliases: detail.aliases || summary.aliases || [],
    tagline: detail.tagline || summary.tagline || "",
    description: detail.description || "",
    url: detail.url || summary.url,
    distinctions: detail.distinctions || [],
    usage: detail.usage || { use: [], avoid: [], scenarios: [] },
    boundary: detail.boundary || null,
    match: {
      score: summary.score,
      fields: summary.matchedFields || [],
    },
  };
}

function compactSearchCandidate(summary) {
  return {
    id: summary.id,
    title: summary.title,
    secondaryTitle: summary.secondaryTitle || null,
    aliases: summary.aliases || [],
    tagline: summary.tagline || "",
    url: summary.url,
    match: {
      score: summary.score,
      fields: summary.matchedFields || [],
    },
  };
}

function normalizeQueries(values) {
  const queries = [];
  const seen = new Set();
  for (const value of values || []) {
    const query = sanitizeRemoteText(value, 120);
    const key = query.toLocaleLowerCase();
    if (!query || seen.has(key)) continue;
    seen.add(key);
    queries.push(query);
  }
  if (!queries.length) throw new Error("--query is required");
  if (queries.length > 3) throw new Error("--query may be repeated at most 3 times");
  return queries;
}

async function resolve(options) {
  const queries = normalizeQueries(options.query);

  const limit = Number(options.limit || 1);
  if (!Number.isInteger(limit) || limit < 1 || limit > 5) {
    throw new Error("--limit must be an integer from 1 to 5");
  }

  const timeout = Number(options.timeout || 10000);
  if (!Number.isInteger(timeout) || timeout < 1000 || timeout > 60000) {
    throw new Error("--timeout must be an integer from 1000 to 60000");
  }

  const siteUrl = configuredSiteUrl(options);
  const manifestPayload = await fetchJson(`${siteUrl}/.well-known/vibehub.json`, {
    timeout,
    label: "VibeHub manifest",
  });
  const manifest = requireData(manifestPayload, "VibeHub manifest");
  if (!manifest.apiBaseUrl || !manifest.schemaVersion) {
    throw new Error("VibeHub manifest is missing apiBaseUrl or schemaVersion");
  }

  const apiBaseUrl = manifest.apiBaseUrl.replace(/\/$/, "");
  const detailRequests = new Map();
  const getDetail = (summary) => {
    if (!detailRequests.has(summary.id)) {
      const lessonUrl = `${apiBaseUrl}/lessons/${encodeURIComponent(summary.id)}`;
      detailRequests.set(summary.id, fetchJson(lessonUrl, {
        timeout,
        label: `VibeHub lesson ${summary.id}`,
      }).then(
        (payload) => requireData(payload, `VibeHub lesson ${summary.id}`),
        () => null,
      ));
    }
    return detailRequests.get(summary.id);
  };

  const results = await Promise.all(queries.map(async (query) => {
    const searchUrl = new URL(`${apiBaseUrl}/search`);
    searchUrl.searchParams.set("q", query);
    searchUrl.searchParams.set("limit", String(limit));
    const search = requireData(
      await fetchJson(searchUrl, { timeout, label: `VibeHub search "${query}"` }),
      `VibeHub search "${query}"`,
    );
    if (!Array.isArray(search.results)) {
      throw new Error(`VibeHub search "${query}" response is missing results`);
    }

    const candidates = options.compact
      ? search.results.map(compactSearchCandidate)
      : await Promise.all(search.results.map(async (summary) => (
        compactCandidate(summary, await getDetail(summary) || summary)
      )));

    return { query, count: candidates.length, candidates };
  }));

  const response = {
    ok: true,
    source: "vibehub",
    schemaVersion: manifest.schemaVersion,
    revision: manifest.revision || manifestPayload.revision || null,
    mode: options.compact ? "compact" : "full",
  };

  if (results.length === 1) return { ...response, ...results[0] };
  return { ...response, queries, results };
}

async function main() {
  let parsed;
  try {
    parsed = parseArgs(process.argv.slice(2));
  } catch (error) {
    fail("invalid_arguments", error.message);
    return;
  }

  if (parsed.options.help || parsed.command === "--help" || !parsed.command) {
    process.stdout.write(HELP);
    return;
  }
  if (parsed.command !== "resolve") {
    fail("unknown_command", `Unknown command: ${parsed.command}`);
    return;
  }

  try {
    output(await resolve(parsed.options));
  } catch (error) {
    const code = error.name === "AbortError" ? "request_timeout" : "resolver_failed";
    fail(code, error.message);
  }
}

await main();
