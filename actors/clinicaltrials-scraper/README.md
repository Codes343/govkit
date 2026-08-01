# ClinicalTrials.gov Scraper — Clinical Study Data API

Extract **clinical studies from ClinicalTrials.gov** as clean, flat, structured data. Search by condition, intervention, sponsor, location or recruitment status, and get back phase, study type, enrollment, eligibility criteria, interventions, collaborators, locations and every key date — **one row per study**, as JSON, CSV, Excel or Google Sheets.

No API key. No login. No nested JSON to unpack.

## What you can do with it

- **Find recruiting trials for a condition** — filter to `RECRUITING` and export with locations.
- **Competitive intelligence in biotech** — every trial run by a named sponsor, with phase and enrollment.
- **Patient recruitment** — trials by condition and location, with site counts and countries.
- **Track a drug or modality** — filter by intervention across all sponsors.
- **Research datasets** — pull tens of thousands of studies for analysis.
- **Feed an AI agent** — exposed over MCP, so agents can query clinical research directly.

## Input

Everything is optional. With no input you get 1,000 studies.

| Field | Type | Default | Description |
|---|---|---|---|
| `condition` | string | — | e.g. `"non-small cell lung cancer"` |
| `intervention` | string | — | e.g. `"semaglutide"` |
| `overallStatus` | array | — | `RECRUITING`, `COMPLETED`, `TERMINATED`, and 6 more |
| `sponsor` | string | — | e.g. `"Pfizer"` |
| `location` | string | — | e.g. `"Germany"` |
| `term` | string | — | Free-text across the whole record |
| `maxItems` | integer | `1000` | Stop after N studies (max 50,000) |

### Example input

```json
{
  "condition": "type 2 diabetes",
  "intervention": "semaglutide",
  "overallStatus": ["RECRUITING", "NOT_YET_RECRUITING"],
  "maxItems": 2000
}
```

## Output

One row per study — flattened from the API's 11 nested modules.

```json
{
  "nctId": "NCT07619157",
  "briefTitle": "A Study of ONO-3310 in Healthy Adult Male Subjects",
  "officialTitle": "A Phase I Study to Investigate the Safety, Tolerability...",
  "overallStatus": "RECRUITING",
  "phases": ["PHASE1"],
  "studyType": "INTERVENTIONAL",
  "conditions": ["Type 2 Diabetes"],
  "leadSponsor": "Ono Pharmaceutical Co. Ltd",
  "leadSponsorClass": "INDUSTRY",
  "collaborators": [],
  "enrollmentCount": 64,
  "enrollmentType": "ESTIMATED",
  "startDate": "2026-01",
  "primaryCompletionDate": "2026-09",
  "briefSummary": "This study evaluates the safety and tolerability...",
  "interventions": ["ONO-3310", "Placebo"],
  "sex": "MALE",
  "minimumAge": "18 Years",
  "maximumAge": "55 Years",
  "locationCount": 3,
  "countries": ["Japan", "United States"],
  "url": "https://clinicaltrials.gov/study/NCT07619157",
  "source": "clinicaltrials.gov"
}
```

Fields that are genuinely absent are omitted rather than returned as `null` or `""`.

## Why not just call the API yourself?

You can — the ClinicalTrials.gov v2 API is free and public. This actor exists because the raw API returns:

- a **`protocolSection` of ~11 nested modules** — sponsor, design, eligibility, arms, contacts, conditions — that you must walk to get one usable row
- **dates as `{"date": "2009-05"}` objects**, often with no day component
- **repeated agency and collaborator objects** with overlapping name fields
- **cursor pagination via `nextPageToken`**, not page numbers
- an **edge filter that returns HTTP 403** to most non-browser clients — a plain, polite crawler User-Agent gets blocked outright

This actor flattens the nesting, normalizes the dates, follows the cursor, sends a request the API actually accepts, and gives you a stable one-row-per-study schema with scheduling and export.

## Pricing

Pay per event — you are billed only for results actually delivered.

| Event | Price |
|---|---|
| Actor start | $0.005 per run |
| Result | $0.003 per study |

1,000 studies ≈ **$3.01**. Apify's free plan includes $5 of monthly credit, so your first ~1,600 results cost nothing.

## Data source and legality

Data comes from the official ClinicalTrials.gov v2 REST API (`clinicaltrials.gov/api/v2`), operated by the US National Library of Medicine at the NIH. It requires no authentication. US federal government works are public domain under 17 U.S.C. § 105. No login is used, no access control is circumvented, and no personal data is collected — study records are public registrations, not patient data.

## Reliability

Upstream endpoints are smoke-tested daily by CI. If ClinicalTrials.gov has an outage the run fails with a plain-English message instead of returning partial garbage — and you are not billed for results you did not receive.

## Related actors

- **Grants.gov Scraper** — federal research funding opportunities and deadlines
- **USAspending Scraper** — federal grant and contract awards, by recipient and agency
- **FDA Recalls Scraper** — food, drug and device enforcement actions
- **Federal Register Scraper** — proposed and final rules, notices, executive orders
