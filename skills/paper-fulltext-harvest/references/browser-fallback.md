# Browser fallback for paywalled publishers without TDM

When TDM API isn't available and OA sources don't have it, drive a logged-in browser via the user's profile. Reuses cookies, SSO sessions, and institutional proxy access.

## Prerequisites

1. **User's Chrome must be running** with the institutional VPN/proxy active (university SSO, EzProxy, etc.).
2. **Cloudflare-protected sites** (ACS, Wiley, T&F): user must have visited the site recently to have a valid `cf_clearance` cookie. If not, ask them to open one article manually first.
3. Tell the user before starting: "I'll be using your Chrome for ~N minutes to scrape M papers — your other tabs may be slower."

## Driving the browser

Two tools work for this; pick by environment:

### Option A: OpenClaw `browser` tool (with `profile="user"`)

Reuses the user's actual Chrome with all cookies. Works alongside `chrome-devtools-mcp` (which usually occupies port 9222 and locks Playwright out).

```python
# First call opens a new tab — capture targetId
result = browser(
    action="open",
    url="https://pubs.acs.org/doi/10.1021/acscatal.5c04133",
    profile="user",
    target="host",
)
target_id = result["targetId"]

# Subsequent calls reuse the same tab
browser(action="navigate", url=next_url, targetId=target_id, profile="user")
browser(action="act",
    request={"kind":"wait", "timeMs":3000},
    targetId=target_id,
    profile="user")

result = browser(
    action="act",
    request={
        "kind":"evaluate",
        "fn":"() => ({title: document.title, abs: document.querySelector('div.article_abstract-content')?.innerText})",
    },
    targetId=target_id,
    profile="user",
)
```

### Option B: Playwright connect_over_cdp (when port 9222 free)

```python
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        page = browser.contexts[0].pages[0]
        await page.goto(url)
        text = await page.text_content("div.article_abstract-content")

asyncio.run(main())
```

If you hit "DevToolsActivePort file doesn't exist" or "Browser is already in use", port 9222 is taken — use Option A.

## Per-publisher CSS selectors

| Publisher | Abstract selector | Full text selector | Notes |
|---|---|---|---|
| ACS | `div.article_abstract-content` | `div.article_content` | CF challenge ~30%, retry after 10s |
| Wiley Online | `section.article-section__abstract p` | `section.article-section__full p` | CF + bot detection, sometimes needs scroll-into-view |
| Taylor & Francis | `div.abstractSection` | `div.NLM_body` | Most aggressive CF, expect ~50% failures |
| RSC | `div.abstract` | `div#wrapper article` | Sometimes needs cookie consent click |
| Springer Link | `section[data-title="Abstract"] p` | `div.main-content section.Abstract p` | OA papers easier |
| Nature | `div#Abs1-content p` | `div#main-content article` | |
| AIP | `div.abstractSection` (varies by journal) | `div.NLM_body` | Many short notes, no abs |
| APS | `section.article-section .article-body` | (subscription needed) | |
| 物化学报 (whxb.pku.edu.cn) | `div.article_abstract` | `div.article_content` | Sometimes scripted |
| 化学学报 (sioc-journal.cn) | `div#abstract` | `div#htmlContent` | |
| 中国科学 (scichina.com) | `.abstractCon` | `.fullTextCon` | |

Always **inspect one page manually first** to confirm selectors — they change frequently. Use browser devtools to find the right query.

## Loop pattern (single tab reuse)

```python
# Good: open one tab, only navigate within it
target_id = browser_open(start_url, profile="user")
results = []
for doi in todo:
    url = build_url(doi, publisher)
    browser_navigate(url, targetId=target_id, profile="user")
    browser_wait(timeMs=3000, targetId=target_id, profile="user")
    text = browser_evaluate(selector_fn, targetId=target_id, profile="user")

    if text and not is_cf_challenge(text):
        results.append({"doi": doi, "text": text})
    else:
        # Cloudflare challenge — wait longer and retry once
        browser_wait(timeMs=10000, targetId=target_id, profile="user")
        text = browser_evaluate(selector_fn, ...)
        results.append({"doi": doi, "text": text, "retried": True})
```

**Anti-pattern:** opening a new tab per DOI. Leaks tabs, slows browser, may exhaust memory.

## Detecting Cloudflare

```python
def is_cf_challenge(text: str) -> bool:
    if not text:
        return True
    return any(s in text for s in [
        "Just a moment...",
        "Checking your browser",
        "cf-challenge",
        "Verify you are human",
        "Performing security verification",
    ])
```

## Throughput expectations

| Publisher | Speed | Success rate (with valid login) |
|---|---|---|
| ACS | ~5 sec/paper | 70-90% |
| Wiley | ~5 sec/paper | 70-85% |
| T&F | ~8 sec/paper | 50-70% |
| RSC | ~4 sec/paper | 80-95% |
| Springer (subscription pages) | ~5 sec/paper | 80-95% |
| CN journals | varies | 30-70% (selector-dependent) |

**Plan for ~12 min per 100 papers** with breaks.

## Stopping cleanly

Build in a kill switch — the user might need their Chrome back:

```python
import os
KILL_FILE = "/tmp/stop_scrape"
for doi in todo:
    if os.path.exists(KILL_FILE):
        log("Stopped by kill file")
        break
    ...
```

Tell the user: "Touch /tmp/stop_scrape to stop me cleanly between papers."

## Saving the result

Whatever the browser extracts (HTML, text, PDF blob), save to disk per-DOI. Same convention as the TDM clients:

```
output_dir/
├── 10.1021_jacs.5c00001/
│   └── article.html        (or .pdf, .txt)
├── 10.1002_anie.202500001/
│   └── article.html
└── ...
```

For PDF binary fetches via `fetch()` in evaluate context — encode to base64 first, then decode in Python:

```python
fn = """
async () => {
    const resp = await fetch('PDF_URL', {credentials: 'include'});
    const buf = await resp.arrayBuffer();
    return btoa(String.fromCharCode(...new Uint8Array(buf)));
}
"""
b64 = browser_evaluate(fn, targetId=target_id, profile="user")
import base64
Path("article.pdf").write_bytes(base64.b64decode(b64))
```

## When to give up

If TDM API + OA + browser all fail for a paper, accept it. Common reasons:
- Paper is genuinely paywalled with no institutional access
- It's a Comment / Erratum with no real abstract or full-text
- DOI is broken (e.g., `.abs` suffix, replaced DOI, withdrawn paper)
- Publisher has zero OA presence (some Chinese journals, old conference proceedings)

Mark as `fetch_failed` in your output and move on. **Don't burn a week on the last 0.5%.**
