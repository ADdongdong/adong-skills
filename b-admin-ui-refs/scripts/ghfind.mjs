#!/usr/bin/env node
/**
 * ghfind - locate files inside a GitHub repo, for finding UI component references.
 *
 * Usage:
 *   node ghfind.mjs <owner/repo> <keyword...>      list matching file paths
 *   node ghfind.mjs <owner/repo> --tree            list all paths (limited)
 *   node ghfind.mjs <owner/repo> --get <path>      print one file's content
 *
 * Options:
 *   --ext tsx,ts,css    filter by file extension
 *   --limit 40          max output lines (default 40)
 *   --branch main       use a specific branch (default: repo default branch)
 *   --json              machine readable output
 *
 * Notes:
 *   - Uses api.github.com (anonymous limit: 60 requests/hour). Set GITHUB_TOKEN to raise it.
 *   - File content is fetched via jsDelivr, falling back to raw.githubusercontent.com.
 *     github.com:443 is flaky on this machine, so git clone is intentionally NOT used.
 *   - Huge repos may return a truncated tree; narrow it down with --ext and keywords.
 */

const API = 'https://api.github.com';
const TOKEN = process.env.GITHUB_TOKEN || process.env.GH_TOKEN || '';

const HEADERS = {
  'User-Agent': 'b-admin-ui-refs',
  Accept: 'application/vnd.github+json',
};
if (TOKEN) HEADERS.Authorization = `Bearer ${TOKEN}`;

/* ---------------------------- args ---------------------------- */
const argv = process.argv.slice(2);
const args = { _: [] };
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === '--get') args.get = argv[++i];
  else if (a === '--limit') args.limit = Number(argv[++i]) || 40;
  else if (a === '--ext') args.ext = argv[++i];
  else if (a === '--branch') args.branch = argv[++i];
  else if (a === '--json') args.json = true;
  else if (a === '--tree') args.tree = true;
  else if (a === '-h' || a === '--help') args.help = true;
  else args._.push(a);
}

const repo = args._[0];
const words = args._.slice(1);
const limit = args.limit || 40;

if (args.help || !repo) usage();

if (!/^[\w.-]+\/[\w.-]+$/.test(repo)) {
  fail(`repo must look like owner/repo, got: ${repo}`);
}

/* ---------------------------- helpers ---------------------------- */
function usage() {
  console.log(`ghfind - locate files in a GitHub repo (UI reference hunting)

  node ghfind.mjs <owner/repo> <keyword...>      list matching paths
  node ghfind.mjs <owner/repo> --tree            list all paths
  node ghfind.mjs <owner/repo> --get <path>      print a file

Options:
  --ext tsx,ts,css   filter by extension
  --limit 40         max lines (default 40)
  --branch <name>    use a specific branch
  --json             machine readable

Examples:
  node ghfind.mjs twentyhq/twenty "record-table" --ext tsx
  node ghfind.mjs tabler/tabler --get README.md
  node ghfind.mjs nocodb/nocodb --tree --ext vue --limit 80`);
  process.exit(0);
}

function fail(msg) {
  console.error(`ERROR: ${msg}`);
  process.exit(1);
}

function apiUrl(path) {
  return `${API}${path}`;
}

async function getJson(url) {
  const r = await fetch(url, { headers: HEADERS });
  if (r.ok) return r.json();
  if (r.status === 403 || r.status === 429) {
    fail('GitHub API rate limited (anonymous: 60 req/hour). Set GITHUB_TOKEN env var to raise the limit.');
  }
  if (r.status === 404) fail(`not found: ${url}`);
  fail(`GitHub API error ${r.status} ${r.statusText} for ${url}`);
}

const lower = (s) => String(s).toLowerCase();

/* ---------------------------- actions ---------------------------- */
async function defaultBranch(full) {
  const j = await getJson(apiUrl(`/repos/${full}`));
  return j.default_branch || 'main';
}

async function fetchFile(full, branch, path) {
  const [owner, name] = full.split('/');
  const b = branch || (await defaultBranch(full));
  const urls = [
    `https://cdn.jsdelivr.net/gh/${owner}/${name}@${b}/${path}`,
    `https://raw.githubusercontent.com/${owner}/${name}/${b}/${path}`,
  ];
  for (const u of urls) {
    try {
      const r = await fetch(u, { headers: { 'User-Agent': HEADERS['User-Agent'] } });
      if (r.ok) return { text: await r.text(), from: u };
    } catch (_) {
      /* try next */
    }
  }
  fail(`could not fetch ${path} (tried jsDelivr and raw.githubusercontent.com)`);
}

async function fetchTree(full, branch) {
  const b = branch || (await defaultBranch(full));
  const j = await getJson(apiUrl(`/repos/${full}/git/trees/${b}?recursive=1`));
  const paths = (j.tree || []).filter((n) => n.type === 'blob').map((n) => n.path);
  return { branch: b, paths, truncated: !!j.truncated, count: paths.length };
}

/* ---------------------------- main ---------------------------- */
if (args.get) {
  const { text, from } = await fetchFile(repo, args.branch, args.get);
  if (!args.json) console.error(`# source: ${from}`);
  process.stdout.write(text.endsWith('\n') ? text : text + '\n');
  process.exit(0);
}

const tree = await fetchTree(repo, args.branch);

let hits = tree.paths;
const exts = String(args.ext || '')
  .split(',')
  .map((s) => s.trim().toLowerCase())
  .filter(Boolean);
if (exts.length) hits = hits.filter((p) => exts.some((e) => lower(p).endsWith('.' + e)));
if (words.length) {
  hits = hits.filter((p) => words.every((w) => lower(p).includes(lower(w))));
}

if (!args.tree && !words.length && !exts.length) {
  fail('nothing to search: pass keywords, or --tree / --ext to widen. See --help.');
}

/* rank: filename match first, then shallower path */
hits.sort((a, b) => {
  const an = lower(a.split('/').pop());
  const bn = lower(b.split('/').pop());
  const aw = words.some((w) => an.includes(lower(w))) ? 0 : 1;
  const bw = words.some((w) => bn.includes(lower(w))) ? 0 : 1;
  if (aw !== bw) return aw - bw;
  const ad = a.split('/').length;
  const bd = b.split('/').length;
  if (ad !== bd) return ad - bd;
  return a.length - b.length;
});

const shown = hits.slice(0, limit);

if (args.json) {
  console.log(JSON.stringify({
    repo, branch: tree.branch, totalFiles: tree.count, truncated: tree.truncated,
    matched: hits.length, shown: shown.length, paths: shown,
  }, null, 2));
} else {
  console.log(`# ${repo}@${tree.branch}  files=${tree.count}  matched=${hits.length}`);
  if (tree.truncated) console.log('# WARNING: GitHub returned a truncated tree - narrow with --ext or more specific keywords.');
  if (!hits.length) console.log('# no match. try: fewer keywords / --ext / --tree');
  for (const p of shown) console.log(p);
  if (hits.length > shown.length) console.log(`# ... ${hits.length - shown.length} more (raise --limit)`);
}
