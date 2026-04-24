# TDM (Text and Data Mining) APIs

Detailed setup for each publisher's TDM/full-text API.

## Elsevier ScienceDirect API

**Endpoint:** `https://api.elsevier.com/content/article/doi/{DOI}?view=FULL`

**Auth headers:**
```
X-ELS-APIKey: <your_api_key>
X-ELS-Insttoken: <your_insttoken>
Accept: text/xml
```

**Get keys:**
- API key: register free at https://dev.elsevier.com/
- Institutional token: contact your library — they request it from Elsevier on behalf of the institution

**Critical:** Must request `view=FULL`. Default `META` returns metadata only (no `<ce:para>` body).

**Output:** `<full-text-retrieval-response>` XML. Body is in:
```
xocs:doc/xocs:serial-item/{ja:article|ja:simple-article}/ja:body/ce:sections
```

**Validation marker:** Check for `<ce:para` substring in response. If absent, you got metadata-only — re-request or skip.

**Rate limit:** ~10 req/sec. Weekly quota varies by institution (typically 10k-100k/week).

**Failure modes:**
- `RESOURCE_NOT_FOUND` (404) — DOI not in Elsevier's corpus (often because DOI is malformed, e.g., trailing `.abs`)
- `AUTHENTICATION_ERROR` (401) — wrong key or expired insttoken
- `QUOTA_EXCEEDED` (429) — back off, retry next day

**Sample request:**
```python
import httpx

resp = httpx.get(
    f"https://api.elsevier.com/content/article/doi/{doi}",
    params={"view": "FULL"},
    headers={
        "X-ELS-APIKey": API_KEY,
        "X-ELS-Insttoken": INST_TOKEN,
        "Accept": "text/xml",
    },
    timeout=60,
)
```

The `ElsevierClient` in `auto_paper_download/clients.py` handles all of this automatically.

## Wiley Online Library TDM API

**Endpoint:** `https://api.wiley.com/onlinelibrary/tdm/v1/articles/{URL_ENCODED_DOI}`

**Auth:** `Wiley-TDM-Client-Token: <your_token>` header (NOT Bearer)

**Get token:** https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining

Institution must have signed Wiley's TDM agreement. Then a token is issued to a single contact person at the institution.

**Output:** PDF (binary). Returns 302 redirect to actual PDF on success.

**Critical:** Requires institutional IP. Won't work from home/cloud unless on institutional VPN.

**Rate limit:** **3 req/sec hard cap** — exceeding returns 429 immediately and may temp-ban your token.

**Sample:**
```python
import httpx, urllib.parse

doi_enc = urllib.parse.quote(doi, safe='')
url = f"https://api.wiley.com/onlinelibrary/tdm/v1/articles/{doi_enc}"
resp = httpx.get(
    url,
    headers={"Wiley-TDM-Client-Token": TOKEN},
    follow_redirects=True,
    timeout=120,
)
if resp.status_code == 200 and resp.content[:4] == b"%PDF":
    save(resp.content)
```

## Springer Nature APIs

**Two APIs:**

### 1. OpenAccess full-text (only OA articles)
```
https://api.springernature.com/openaccess/json?api_key={KEY}&q=doi:{DOI}
```
Returns JSON with `text` field containing full-text. Free key tier: 1 req/sec.

### 2. PDF direct (subscription content)
```
https://link.springer.com/content/pdf/{DOI}.pdf
```

Works with institutional cookies / IP. **Pitfall:** This URL serves a 200 with HTML "subscribe" page when not authenticated. **Always check first 4 bytes for `%PDF`**.

**Get key:** https://dev.springernature.com/ — free key for OpenAccess API.

## RSC (Royal Society of Chemistry)

**No public TDM API.** Bulk download requires direct deal with RSC. Browser fallback only — see `browser-fallback.md`.

URL pattern (must be discovered from article landing page):
```
https://pubs.rsc.org/en/content/articlepdf/{YEAR}/{JOURNAL}/{ARTICLE_ID}
```

## ACS (American Chemical Society)

**No public TDM API** for general subscribers. ACS offers paid TDM subscription separately (contact ACS directly).

Browser fallback URL patterns:
- Abstract page: `https://pubs.acs.org/doi/{DOI}`
- PDF (403 unless subscribed): `https://pubs.acs.org/doi/pdf/{DOI}`

## Other publishers

- **Taylor & Francis:** No public TDM. Browser via `https://www.tandfonline.com/doi/pdf/{DOI}`. Aggressive Cloudflare.
- **AIP:** No TDM. Browser via `https://pubs.aip.org/aip/{journal}/article/...`.
- **APS:** No TDM. Browser via `https://journals.aps.org/{journal}/abstract/{DOI}`.
- **IOP:** Has TDM-like API but requires per-institution agreement.

## Crossref TDM (cross-publisher)

For some publishers, Crossref's `link[]` field contains a TDM-licensed URL:

```python
import httpx

data = httpx.get(f"https://api.crossref.org/works/{doi}").json()
for link in data["message"].get("link", []):
    if link.get("intended-application") == "text-mining":
        url = link["URL"]
        # Need Crossref click-through token if license requires it:
        resp = httpx.get(
            url,
            headers={"CR-Clickthrough-Client-Token": CR_TOKEN},
            follow_redirects=True,
        )
```

**Get token:** https://www.crossref.org/services/click-through-service/

## OA aggregators (no auth, just email)

| API | URL | Auth | Notes |
|---|---|---|---|
| OpenAlex | `https://api.openalex.org/works/doi:{DOI}?mailto={EMAIL}` | Email (polite pool) | Returns `open_access.oa_url` for OA copy |
| Unpaywall | `https://api.unpaywall.org/v2/{DOI}?email={EMAIL}` | Email | Returns `best_oa_location.pdf_url` |
| EuroPMC | `https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:{DOI}` | None | Full-text for life sciences via PMCID |

Use these for any DOI to find OA copies regardless of publisher. The `UnpaywallClient` and `OpenAlexClient` in this package wrap these.
