---
name: paper-fulltext-harvest
description: Batch download academic paper full-text (PDF/XML) from a list of DOIs. Handles publisher TDM (Text and Data Mining) APIs requiring institutional subscription (Elsevier ScienceDirect, Wiley Online, Springer Nature), Open Access sources (Crossref, Unpaywall, OpenAlex), and a browser-based fallback for paywalled publishers without TDM access (ACS, RSC, T&F, Chinese journals). Use when the user wants to harvest, scrape, fetch, or bulk-download papers from a DOI list, savedrecs export, or Excel; or wants to fill missing full-text PDFs for an existing literature collection. Triggers on phrases like "批量下载文献", "下载全文", "harvest papers", "scrape full text", "TDM API", "下载 Elsevier 全文", "Wiley 批量下载", "下载 PDF".
---

# Paper Full-text Harvest

Pipeline for downloading academic paper full-text at scale. Handles the three classes of sources that exist in 2026:

1. **Publisher TDM APIs** (Elsevier / Wiley / Springer) — for paywalled content where the institution has a subscription
2. **OA aggregators** (Unpaywall / OpenAlex / Crossref) — for Open Access copies regardless of publisher
3. **Browser fallback** (logged-in user profile) — for paywalled publishers without a TDM API (ACS / RSC / T&F / many CN journals)

## Decision tree

```
Have a DOI list?
├── DOIs from Elsevier (10.1016, 10.1006, ...)
│   └── Use ElsevierClient (TDM XML API)             → §1
├── DOIs from Wiley (10.1002, ...)
│   └── Use WileyClient (TDM PDF API)                → §1
├── DOIs from Springer (10.1007, 10.1038, ...)
│   ├── OA papers → SpringerClient OA API            → §1
│   └── Subscription papers → fall through to OA/browser
├── Other publishers
│   ├── Try OA first via UnpaywallClient/OpenAlexClient → §2
│   └── Last resort: browser fallback                → §3
└── Mixed list (typical case)
    └── Use the orchestrated CLI (handles all of the above) → §0
```

## §0. Quick start (orchestrated CLI)

For a typical mixed list of DOIs from Web of Science / Scopus export:

```bash
# Setup once
cp scripts/.env.example .env
# Edit .env to fill API keys (see §4 "Configuration")

# Run
python -m auto_paper_download \
    --savedrecs your_export.xls \
    --output-dir ./downloads/ \
    --delay 2.0
```

The CLI:
- Parses DOIs from WoS savedrecs (or pass multiple `--savedrecs`)
- Routes each DOI to the right client by prefix
- Handles rate limiting + retries
- Per-publisher success summary at end

For **resume-safe Elsevier bulk** (the most common large run, e.g. 5000+ Elsevier DOIs):

```bash
python scripts/redownload_elsevier.py \
    --excel papers.xlsx \
    --output-dir ./elsevier_xml/ \
    --resume \
    --long-pause-every 200 \
    --long-pause-sec 300
```

## §1. Publisher TDM APIs

Read `references/tdm-apis.md` for full per-publisher details.

**Quick reference:**

| Publisher | API | Auth env var | Output | Rate limit |
|---|---|---|---|---|
| **Elsevier** | `api.elsevier.com/content/article/doi/{DOI}?view=FULL` | `ELSEVIER_API_KEY` + `ELSEVIER_INSTTOKEN` | XML (full-text) | ~5 req/sec |
| **Wiley** | `api.wiley.com/onlinelibrary/tdm/v1/articles/{DOI}` | `WILEY_TDM_TOKEN` | PDF | 3 req/sec hard cap |
| **Springer (OA)** | `api.springernature.com/openaccess/json` | `SPRINGER_API_KEY` | JSON+text | 1 req/sec free |
| **Crossref TDM** | URL from `link[]` field with `intended-application: text-mining` | `CR_CLICKTHROUGH_TOKEN` | varies | varies |

**Critical:** All TDM APIs require **institutional IP allowlisting** — must run from the institution's network or VPN. Test with one DOI before bulk runs.

**Instantiate clients directly:**

```python
from auto_paper_download.clients import ElsevierClient, WileyClient

elsevier = ElsevierClient()  # reads env vars
xml_path = elsevier.download_structured_full_text(
    doi="10.1016/j.ces.2025.123003",
    article_dir=Path("downloads/10.1016_j.ces.2025.123003"),
)

wiley = WileyClient()
pdf_path = wiley.download_pdf(
    doi="10.1002/anie.202500001",
    article_dir=Path("downloads/10.1002_anie.202500001"),
)
```

## §2. OA fallback (Unpaywall / OpenAlex / Crossref)

For papers that may have OA copies regardless of publisher.

```python
from auto_paper_download.clients import UnpaywallClient, OpenAlexClient, CrossrefClient

# Unpaywall: best OA PDF URL
up = UnpaywallClient()
pdf_path = up.download_pdf(doi=doi, article_dir=Path("downloads/.."))

# OpenAlex: alternative OA source
oa = OpenAlexClient()
pdf_path = oa.download_pdf(doi=doi, article_dir=Path("downloads/.."))

# Crossref: tries to find publisher PDF link
cr = CrossrefClient()
pdf_path = cr.download_pdf(doi=doi, article_dir=Path("downloads/.."))
```

**Always validate downloaded PDFs:** First 4 bytes must be `%PDF` and file size > 50KB. The clients in this skill do this automatically.

Expected hit rate for OA fallback: 40-60% on a generic chemistry/biology list. Recent papers (>2023) have higher OA rates.

## §3. Browser fallback (paywalled, no TDM)

For publishers where API isn't available but the user has institutional Cloudflare/SSO access via browser cookies. **Slowest path — only use after exhausting §1–§2**.

Read `references/browser-fallback.md` before starting. It covers:
- How to drive the user's logged-in Chrome via OpenClaw `browser` tool with `profile="user"`
- Per-publisher CSS selectors for ACS, Wiley, RSC, T&F, Springer, Nature, AIP, and 3 major Chinese journals
- Cloudflare detection + retry strategy
- Single-tab reuse pattern (don't open a new tab per DOI — leaks)
- Kill-switch via `/tmp/stop_scrape`

**Hard reality:** ACS / Wiley / T&F use Cloudflare. Even with a logged-in profile, expect:
- ~30% Cloudflare challenges (retry after 10s usually clears)
- Some sites detect headless and hard-block — only the user's real Chrome with active session works
- Throughput: ~5 sec/paper, ~70-90% success

## §4. Configuration

Required env vars (set in `.env`, see `scripts/.env.example`):

| Variable | Required for | How to get |
|---|---|---|
| `ELSEVIER_API_KEY` | Elsevier | https://dev.elsevier.com/ (free key) |
| `ELSEVIER_INSTTOKEN` | Elsevier institutional access | Contact your library |
| `WILEY_TDM_TOKEN` | Wiley | https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining (institution must sign TDM agreement) |
| `SPRINGER_API_KEY` | Springer OA | https://dev.springernature.com/ (free key) |
| `CROSSREF_MAILTO` | Crossref polite pool (recommended) | Just your email |
| `OPENALEX_MAILTO` | OpenAlex polite pool (recommended) | Just your email |
| `UNPAYWALL_EMAIL` | Unpaywall (required) | Just your email |

**Notes:**
- All env vars are optional — missing ones simply disable that source
- `CROSSREF_REQUEST_DELAY` / `WILEY_REQUEST_DELAY` allow tuning per-source delay

## Core principles

1. **Cache directory structure**: each DOI gets its own folder named `<safe_doi>/` (with `/` replaced by `_`). This makes resume trivial — check if folder exists with non-empty file.
2. **Cascade sources, cheapest first**: TDM API for known publisher → OA aggregator → browser. Each fallback is more expensive (rate, time, fragility).
3. **Respect rate limits**: defaults are conservative (`--delay 2.0`). For long runs use `--long-pause-every` and `--long-pause-sec` to avoid cumulative ban.
4. **Don't trust HTTP 200**: many publisher APIs return 200 with HTML "subscribe to read" page. Validate content (PDF magic bytes, XML body markers like `<ce:para>`).
5. **Validate before declaring done**: spot-check 5 random files manually before reporting success.

## Common pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| Empty PDF/XML directories created on failure | "Downloaded N papers" but files are 0 bytes | Validate file size; remove empty dirs (this code does it via `_cleanup_article_dir`) |
| Cloudflare blocks headless Playwright | 403 / "Just a moment..." | Use OpenClaw `browser` with `profile="user"`, not headless |
| Rate-limited mid-batch | 429s, then permanent block | Increase `--delay`, set `--long-pause-every 200`, respect `Retry-After` |
| Springer subscription returns HTML "subscribe" | Saved 0-byte or junk PDF | Code checks `%PDF` magic bytes — use the SpringerClient, don't bypass |
| DOI case sensitivity | Some publishers 404 on uppercase | Code normalizes; if writing your own, always `.lower()` |
| `.abs` suffix on Crossref DOIs | 404 from Crossref | Strip `.abs` before query |

## When to ask the user

- Before running >1000 publisher API requests (institution may have weekly quota)
- Before browser scrape loop (will tie up their Chrome for ~5 sec/paper)
- When >30% of fetches fail unexpectedly (network / auth problem — investigate before continuing)
- When you detect a publisher with no API + no OA — confirm whether to skip or try browser

## File layout

```
paper-fulltext-harvest/
├── SKILL.md                       (this file)
├── references/
│   ├── tdm-apis.md                Per-publisher TDM API details
│   └── browser-fallback.md        Browser scraping guide for paywalled non-TDM publishers
└── scripts/
    ├── .env.example               Template for API keys
    ├── pyproject.toml             Dependencies (pip/uv installable)
    ├── redownload_elsevier.py     Resume-safe Elsevier bulk downloader
    └── auto_paper_download/       Main package
        ├── __init__.py
        ├── __main__.py            CLI entrypoint
        ├── clients.py             ElsevierClient, WileyClient, SpringerClient, CrossrefClient, UnpaywallClient, OpenAlexClient
        ├── downloader.py          Orchestration: parse savedrecs, route by publisher, batch download
        └── supplements.py         Supplementary file downloader
```
