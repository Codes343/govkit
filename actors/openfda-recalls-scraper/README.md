# FDA Recalls Scraper — Food, Drug & Device Enforcement Data

Extract **FDA recall and enforcement reports** for food, drugs and medical devices as clean, structured data. Filter by product category, recall classification, status, date range, firm or keyword, and get back the recall reason, product description, recalling firm, distribution pattern and every relevant date — as JSON, CSV, Excel or Google Sheets.

No API key. No login. Recall classes explained in plain English on every row.

## What you can do with it

- **Monitor recalls affecting your products** — schedule a daily run on a keyword and route new rows to Slack or email.
- **Supplier risk screening** — pull every recall for a named manufacturer.
- **Retail and grocery compliance** — Class I food recalls, filtered to your date range.
- **Pharma and device competitive intelligence** — track enforcement across an entire category.
- **Research a recall pattern** — full history by ingredient, allergen or failure mode.
- **Feed an AI agent** — exposed over MCP, so agents can query FDA enforcement directly.

## Input

Everything is optional. With no input you get the 1,000 most recent food recalls reported since 2026-01-01.

| Field | Type | Default | Description |
|---|---|---|---|
| `categories` | array | `["food"]` | `food`, `drug`, `device` |
| `reportedAfter` | string | — | ISO date, e.g. `"2026-01-01"` |
| `reportedBefore` | string | — | ISO date |
| `classifications` | array | — | `Class I`, `Class II`, `Class III` |
| `statuses` | array | — | `Ongoing`, `Completed`, `Terminated`, `Pending` |
| `recallingFirm` | string | — | e.g. `"Abbott"` |
| `keyword` | string | — | Searches reason + product, e.g. `"listeria"` |
| `maxItems` | integer | `1000` | Stop after N recalls (max 50,000) |

### Example input

```json
{
  "categories": ["food"],
  "classifications": ["Class I"],
  "keyword": "listeria",
  "reportedAfter": "2025-01-01",
  "maxItems": 2000
}
```

## Output

One row per recall record.

```json
{
  "recallNumber": "H-0814-2026",
  "eventId": "98822",
  "category": "food",
  "status": "Ongoing",
  "classification": "Class I",
  "classificationMeaning": "Reasonable probability of serious health consequences or death",
  "recallingFirm": "PS Seasoning & Spices, Inc.",
  "productDescription": "Ellsworth Sour Cream + Onion Seasoning, Part #: 180000113...",
  "reasonForRecall": "Undeclared milk allergen",
  "distributionPattern": "Nationwide",
  "voluntaryOrMandated": "Voluntary: Firm initiated",
  "reportDate": "2026-03-18",
  "recallInitiationDate": "2026-02-27",
  "city": "Iron Ridge",
  "state": "WI",
  "country": "United States",
  "source": "api.fda.gov"
}
```

Fields that are genuinely absent are omitted rather than returned as `null` or `""`.

## Why not just call the API yourself?

You can — openFDA is free and public. This actor exists because the raw API makes you:

- **write Lucene queries by hand**: `report_date:[20250101 TO 20261231] AND classification:("Class I")` — with quoting rules that fail silently when you get them wrong
- **use `YYYYMMDD` dates** with no separators, unlike every other field you have
- **handle HTTP 404 as "no matches"**, which will crash naive client code
- **respect an undocumented `skip` ceiling of 25,000**, beyond which paging simply stops
- **query three separate endpoints** (food, drug, device) and merge the results yourself
- **look up what "Class II" actually means** somewhere else entirely

This actor does all of it, adds a plain-English `classificationMeaning` to every row, and gives you a stable schema with scheduling and export.

## Pricing

Pay per event — you are billed only for results actually delivered.

| Event | Price |
|---|---|
| Actor start | $0.005 per run |
| Result | $0.003 per recall |

1,000 recalls ≈ **$3.01**. Apify's free plan includes $5 of monthly credit, so your first ~1,600 results cost nothing.

## Data source and legality

Data comes from the official openFDA API (`api.fda.gov`), operated by the US Food and Drug Administration. It requires no authentication. US federal government works are public domain under 17 U.S.C. § 105. No login is used, no access control is circumvented, and no personal data is collected.

**Note:** the FDA states that openFDA data is not validated for clinical use. Do not rely on it to make decisions about medical care.

## Reliability

Upstream endpoints are smoke-tested daily by CI. If openFDA has an outage the run fails with a plain-English message instead of returning partial garbage — and you are not billed for results you did not receive.

## Related actors

- **Grants.gov Scraper** — federal funding opportunities, award amounts and deadlines
- **USAspending Scraper** — federal contract and grant awards, by recipient and agency
- **Federal Register Scraper** — proposed and final rules, notices, executive orders
- **ClinicalTrials.gov Scraper** — trials by condition, sponsor and phase
