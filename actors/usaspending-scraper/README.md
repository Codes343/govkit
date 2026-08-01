# USAspending Scraper — Federal Contracts & Grants Award Data

Extract **US federal contract, grant and loan awards** from USAspending.gov as clean, structured data. Search by agency, recipient, keyword, state, date range or dollar amount, and get back recipient name, award amount, awarding agency and sub-agency, period of performance and description — as JSON, CSV, Excel or Google Sheets.

No API key. No login. No paging logic to write.

## What you can do with it

- **Find who won federal contracts in your market** — filter by agency and keyword, sort by value.
- **Competitive intelligence on GovCon rivals** — pull every award to a named recipient.
- **Track an agency's spending** — DoD, HHS, DOE, VA, DHS and every other federal agency.
- **Find expiring contracts** — filter by end date to spot recompete windows before they're announced.
- **Journalism and research** — build a spending dataset over any date range.
- **Feed an AI agent** — exposed over MCP, so agents can query federal spending directly.

## Input

Everything is optional. With no input you get the 1,000 largest contracts active since 2020.

| Field | Type | Default | Description |
|---|---|---|---|
| `awardCategory` | string | `contracts` | `contracts`, `grants`, `direct_payments`, `loans`, `other`, `idvs` |
| `startDate` | string | `2020-01-01` | Awards active on or after this ISO date |
| `endDate` | string | today | Awards active on or before this ISO date |
| `keywords` | array | — | Free text, e.g. `["cybersecurity"]` |
| `agencies` | array | — | e.g. `["Department of Defense"]` |
| `recipients` | array | — | e.g. `["Lockheed"]` |
| `states` | array | — | Place of performance, e.g. `["VA","TX"]` |
| `awardAmountMin` / `awardAmountMax` | integer | — | Dollar bounds |
| `maxItems` | integer | `1000` | Stop after N awards (max 50,000) |

### Example input

```json
{
  "awardCategory": "contracts",
  "keywords": ["cybersecurity"],
  "agencies": ["Department of Defense"],
  "startDate": "2025-01-01",
  "awardAmountMin": 1000000,
  "maxItems": 5000
}
```

## Output

One row per award.

```json
{
  "awardId": "HT940216C0001",
  "recipientName": "HUMANA GOVERNMENT BUSINESS INC",
  "awardAmount": 51269205263.03,
  "totalOutlays": 0.0,
  "description": "IGF::OT::IGF",
  "awardingAgency": "Department of Defense",
  "awardingSubAgency": "Defense Health Agency",
  "startDate": "2016-08-01",
  "endDate": "2025-12-31",
  "recipientId": "1068e466-707d-6b6f-367f-0255fab79b8c-C",
  "agencySlug": "department-of-defense",
  "url": "https://www.usaspending.gov/award/CONT_AWD_HT940216C0001_9700_-NONE-_-NONE-",
  "source": "usaspending.gov"
}
```

Fields that are genuinely absent are omitted rather than returned as `null` or `""`.

## Why not just call the API yourself?

You can — USAspending is free and public. This actor exists because the raw API makes you:

- **know the award type codes**: contracts are `A,B,C,D`, grants are `02,03,04,05`, loans are `07,08`. Mix families in one request and it errors — this actor exposes them as named categories instead.
- **send a matching `fields` array**, which differs per award family
- **build nested filter objects** for agencies (`{type, tier, name}`), locations and amount bounds
- **page manually** on `page_metadata.hasNext`, with a hard 100-row limit per request
- **construct award URLs** yourself from `generated_internal_id`

This actor handles all of it, retries with backoff, and gives you a stable schema with scheduling and export.

## Pricing

Pay per event — you are billed only for results actually delivered.

| Event | Price |
|---|---|
| Actor start | $0.005 per run |
| Result | $0.003 per award |

1,000 awards ≈ **$3.01**. Apify's free plan includes $5 of monthly credit, so your first ~1,600 results cost nothing.

## Data source and legality

Data comes from the official USAspending.gov REST API (`api.usaspending.gov/api/v2`), operated by the US Treasury under the DATA Act. It requires no authentication. US federal government works are public domain under 17 U.S.C. § 105. No login is used, no access control is circumvented, and no personal data is collected.

## Reliability

Upstream endpoints are smoke-tested daily by CI. If USAspending has an outage the run fails with a plain-English message instead of returning partial garbage — and you are not billed for results you did not receive.

## Related actors

- **Grants.gov Scraper** — funding opportunities you can still apply for
- **Federal Register Scraper** — proposed and final rules, notices, executive orders
- **FDA Recalls Scraper** — food, drug and device enforcement actions
- **ClinicalTrials.gov Scraper** — trials by condition, sponsor and phase
