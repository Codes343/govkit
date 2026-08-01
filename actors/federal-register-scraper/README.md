# Federal Register Scraper — Rules, Notices & Regulations API

Extract **Federal Register documents** — proposed rules, final rules, notices and presidential documents — as clean, structured data. Search by keyword, agency, document type or publication date, and get back abstracts, comment deadlines, effective dates, docket IDs, RINs and CFR references as JSON, CSV, Excel or Google Sheets.

No API key. No login. No pagination headaches.

## What you can do with it

- **Track new regulations affecting your industry** — schedule a daily run on a keyword and route new rows to Slack or email.
- **Never miss a comment deadline** — every record carries `commentsCloseDate` and `effectiveDate`.
- **Monitor a specific agency** — EPA, FDA, SEC, FCC, DOT, DOL and every other Federal Register publisher.
- **Build a regulatory dataset** — pull a full date range for analysis or model training.
- **Compliance and legal research** — filter by CFR part or docket ID.
- **Feed an AI agent** — exposed over MCP, so agents can query federal rulemaking directly.

## Input

Everything is optional. With no input you get the 1,000 most recent documents.

| Field | Type | Default | Description |
|---|---|---|---|
| `term` | string | — | Full-text search, e.g. `"PFAS"` |
| `documentTypes` | array | — | `RULE`, `PRORULE`, `NOTICE`, `PRESDOCU` |
| `publishedAfter` | string | — | ISO date, e.g. `"2026-01-01"` |
| `publishedBefore` | string | — | ISO date, e.g. `"2026-12-31"` |
| `agencies` | array | — | Agency slugs, e.g. `["environmental-protection-agency"]` |
| `order` | string | `newest` | `newest`, `oldest`, `relevance` |
| `maxItems` | integer | `1000` | Stop after N documents (max 50,000) |

### Example input

```json
{
  "term": "artificial intelligence",
  "documentTypes": ["PRORULE", "RULE"],
  "publishedAfter": "2026-01-01",
  "maxItems": 2000
}
```

## Output

One row per document.

```json
{
  "documentNumber": "2026-15123",
  "title": "Review of Submarine Cable Landing License Rules and Procedures...",
  "documentType": "Rule",
  "abstract": "In this document, the Federal Communications Commission adopted a Second Report and Order...",
  "action": "Final rule.",
  "publicationDate": "2026-07-29",
  "effectiveDate": "2026-09-01",
  "commentsCloseDate": null,
  "agencies": ["Federal Communications Commission"],
  "docketIds": ["IB Docket No. 24-523"],
  "regulationIdNumbers": [],
  "cfrReferences": ["47 CFR 1"],
  "pageLength": 42,
  "url": "https://www.federalregister.gov/documents/2026/07/29/2026-15123/...",
  "pdfUrl": "https://www.govinfo.gov/content/pkg/FR-2026-07-29/pdf/2026-15123.pdf",
  "source": "federalregister.gov"
}
```

Fields that are genuinely absent are omitted rather than returned as `null` or `""`.

## Why not just call the API yourself?

You can — the Federal Register API is free and public. This actor exists because the raw API gives you:

- **offset pagination that silently caps out** — you must follow an opaque `next_page_url` cursor to get past the first few thousand results
- **PHP-style bracket parameters** (`conditions[type][]`, `fields[]`) that are easy to get subtly wrong
- **nested agency objects** with both `name` and `raw_name`, duplicated across parent and child agencies
- **CFR references as `{title, part}` objects**, not readable citations
- no retries, no backoff, no scheduling, no export

This actor handles the cursor, flattens the nesting, formats the citations, retries with backoff, and gives you a stable schema with scheduling and export.

## Pricing

Pay per event — you are billed only for results actually delivered.

| Event | Price |
|---|---|
| Actor start | $0.005 per run |
| Result | $0.003 per document |

1,000 documents ≈ **$3.01**. Apify's free plan includes $5 of monthly credit, so your first ~1,600 results cost nothing.

## Data source and legality

Data comes from the official Federal Register public REST API (`federalregister.gov/api/v1`), operated by the Office of the Federal Register and the Government Publishing Office. It requires no authentication. US federal government works are public domain under 17 U.S.C. § 105. No login is used, no access control is circumvented, and no personal data is collected.

## Reliability

Upstream endpoints are smoke-tested daily by CI. If the Federal Register API has an outage the run fails with a plain-English message instead of returning partial garbage — and you are not billed for results you did not receive.

## Related actors

- **Grants.gov Scraper** — federal funding opportunities, award amounts and deadlines
- **USAspending Scraper** — federal contract and grant awards, by recipient and agency
- **openFDA Recalls Scraper** — food, drug and device enforcement actions
- **ClinicalTrials.gov Scraper** — trials by condition, sponsor and phase
