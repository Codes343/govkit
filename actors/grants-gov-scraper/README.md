# Grants.gov Scraper — Federal Funding Opportunities API

Extract **US federal grant opportunities from Grants.gov** as clean, structured data. Search by keyword, agency, deadline, eligibility or Assistance Listing Number (ALN/CFDA), and get back award amounts, application deadlines, eligible applicant types, agency contact emails and full plain-text descriptions — as JSON, CSV, Excel or straight into Google Sheets.

No API key. No login. No rate-limit engineering. Point it at a keyword and get a dataset.

## What you can do with it

- **Find open grants for your organization** — filter by eligibility code and funding category, sorted by deadline.
- **Monitor new funding opportunities daily** — schedule the actor and pipe new rows to Slack, email or a webhook.
- **Build a grants database** — pull the full historical archive (`closed` + `archived`) for trend analysis.
- **Track a specific agency's funding** — NSF, NIH, USDA, DOE, HHS, DOD and every other Grants.gov publisher.
- **Feed an AI agent** — this actor is exposed over MCP, so agents can search federal funding directly.
- **Grant-writing prospecting** — award ceiling, cost-sharing requirement and contact email on every record.

## Input

Everything is optional. With no input at all you get the 1,000 most recent posted and forecasted opportunities.

| Field | Type | Default | Description |
|---|---|---|---|
| `keyword` | string | — | Full-text search, e.g. `"rural broadband"` |
| `oppStatuses` | array | `["posted","forecasted"]` | `forecasted`, `posted`, `closed`, `archived` |
| `includeDetails` | boolean | `true` | Fetch full synopsis, award amounts and contacts |
| `maxItems` | integer | `1000` | Stop after N opportunities (max 50,000) |
| `agencies` | array | — | Agency codes, e.g. `["NSF","HHS-NIH11"]` |
| `aln` | string | — | Assistance Listing Number, e.g. `"47.075"` |
| `opportunityNumber` | string | — | Look up one opportunity, e.g. `"PD-19-127Y"` |
| `fundingInstruments` | array | — | `G` grant, `CA` cooperative agreement, `PC` contract, `O` other |
| `eligibilities` | array | — | Eligibility codes, e.g. `["06","12"]` |
| `fundingCategories` | array | — | Category codes, e.g. `["ST","HL"]` |

### Example input

```json
{
  "keyword": "artificial intelligence",
  "oppStatuses": ["posted"],
  "agencies": ["NSF"],
  "includeDetails": true,
  "maxItems": 500
}
```

## Output

One row per funding opportunity.

```json
{
  "opportunityId": "320753",
  "opportunityNumber": "PD-19-127Y",
  "title": "Science of Learning and Augmented Intelligence",
  "agencyCode": "NSF",
  "agencyName": "U.S. National Science Foundation",
  "status": "posted",
  "docType": "synopsis",
  "postedDate": "2019-09-19",
  "closeDate": "2026-08-05",
  "alnNumbers": ["47.075"],
  "url": "https://grants.gov/search-results-detail/320753",
  "source": "grants.gov",

  "description": "Science of Learning and Augmented Intelligence (SL) supports potentially transformative research that develops basic theoretical insights...",
  "descriptionLength": 2841,
  "awardFloor": 550.0,
  "costSharingRequired": false,
  "eligibleApplicants": ["Unrestricted (i.e., open to any type of entity above), subject to any clarification in text"],
  "fundingCategories": ["Science and Technology and other Research and Development"],
  "fundingInstruments": ["Grant"],
  "responseDate": "2026-08-05",
  "archiveDate": "2033-09-02",
  "agencyContactName": "U.S. National Science Foundation",
  "agencyContactEmail": "grantsgovsupport@nsf.gov",
  "agencyContactPhone": "703-292-4203",
  "additionalInfoUrl": "http://www.nsf.gov/funding/pgm_summ.jsp?pims_id=505731",
  "opportunityCategory": "Discretionary",
  "version": 24
}
```

Fields that are genuinely absent are omitted rather than returned as `null`, `"none"` or `""`.

## Why not just call the API yourself?

You can — Grants.gov is free and public. This actor exists because the raw API hands you:

- award amounts as the **string** `"none"` instead of null
- dates in four different formats (`"Sep 19, 2019 12:00:00 AM EDT"`, `09/19/2019`, `2019-09-19-00-00-00`)
- descriptions as **HTML fragments** full of `&mdash;` and `<br>`
- filters as **pipe-delimited strings**, not arrays
- `HTTP 200` on logical errors, with the real status buried in an `errorcode` field
- detail only via a **second** endpoint, one request per opportunity

This actor normalizes all of it, parallelizes the detail fetches, retries with backoff, and gives you a stable schema plus scheduling, deduplication and export.

## Pricing

Pay per event — you are billed only for results actually delivered.

| Event | Price |
|---|---|
| Actor start | $0.005 per run |
| Result | $0.003 per opportunity |

1,000 fully-detailed opportunities ≈ **$3.01**. Apify's free plan includes $5 of monthly credit, so your first ~1,600 results cost nothing.

## Data source and legality

Data comes from the official Grants.gov public REST API (`api.grants.gov/v1/api/search2` and `/fetchOpportunity`), which Grants.gov documents as requiring no authentication or authorization. US federal government works are public domain under 17 U.S.C. § 105. No login is used, no access control is circumvented, and no personal data is collected. Requests are rate-limited and identify themselves honestly.

## Reliability

Upstream endpoints are smoke-tested daily by CI. If Grants.gov has an outage the run fails with a plain-English message instead of returning partial garbage — and you are not billed for results you did not receive.

## Related actors

- **Federal Register Scraper** — proposed and final rules, notices, executive orders
- **USAspending Scraper** — federal contract and grant awards, by recipient and agency
- **openFDA Recalls Scraper** — food, drug and device enforcement actions
- **ClinicalTrials.gov Scraper** — trials by condition, sponsor and phase
