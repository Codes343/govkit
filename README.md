# Fedstack

Paid data-extraction Actors on [Apify Store](https://apify.com/store) that turn
US federal open-government APIs into clean, structured, exportable datasets.

**Goal: $20/month profit, $0 budget, zero ongoing human work.**
Full reasoning, the 30 evaluated alternatives, risk analysis and projections are
in [BUSINESS_PLAN.md](BUSINESS_PLAN.md).

## Status

| | |
|---|---|
| Actors built | 2 of 5 (Grants.gov, Federal Register) |
| Code | Tested, linted, deploys itself |
| Blocking on | Human setup — see [SETUP.md](SETUP.md), ~45 min, one time |

## Actors

| Actor | Source | Auth needed |
|---|---|---|
| [`grants-gov-scraper`](actors/grants-gov-scraper) | `api.grants.gov` | none |
| [`federal-register-scraper`](actors/federal-register-scraper) | `federalregister.gov/api/v1` | none |
| *(planned)* `usaspending-scraper` | `api.usaspending.gov` | none |
| *(planned)* `openfda-recalls-scraper` | `api.fda.gov` | none |
| *(planned)* `clinicaltrials-scraper` | `clinicaltrials.gov/api/v2` | none |

Every source is a keyless public API over plain HTTP — no browsers, no proxies.
That is a deliberate architectural constraint, and it is what makes the pricing
in [PRICING.md](PRICING.md) profitable.

## Layout

```
src/fedstack/          Shared core — the single source of truth
  http.py              Rate-limited, retrying JSON client
  billing.py           Pay-per-event charging + spend-ceiling enforcement
  normalize.py         Date/money/HTML cleaning
  sources/             One module per upstream API
actors/<name>/         One deployable Apify Actor
  .actor/              Manifest, input schema, dataset view
  src/main.py          Entrypoint: read input, stream pages, bill
  README.md            The Store listing and primary SEO surface
scripts/               Build, validate, smoke-test, report
tests/                 Unit tests (mocked HTTP)
```

`src/fedstack` is copied into each actor at build time by
`scripts/build_actor.py`, because Apify deploys a single directory and there is
no private package registry on a $0 budget. Those copies are gitignored.

## Development

```bash
pip install -e ".[dev]"
pytest -q                        # unit tests, no network
python scripts/check_actors.py   # validate every actor manifest
python scripts/smoke_test.py     # hit the real .gov APIs
python scripts/build_actor.py    # vendor the core into each actor
```

Deploy happens automatically on push to `master`. To deploy by hand:

```bash
python scripts/build_actor.py --push
```

## Automation

| When | What | Where |
|---|---|---|
| Push to `master` | Test, validate, deploy all actors | `.github/workflows/deploy.yml` |
| Daily 06:00 UTC | Smoke-test upstream APIs; open/close an issue | `.github/workflows/smoke-test.yml` |
| Mondays 13:00 UTC | Revenue and traction report to a tracking issue | `.github/workflows/revenue-report.yml` |
| Every PR | Lint, format check, tests | `.github/workflows/ci.yml` |

## Data and legality

All sources are US federal government works, public domain under
17 U.S.C. § 105, accessed through documented public APIs that require no
authentication. No login is used, no access control is circumvented, no
robots.txt is bypassed, and no personal data is collected. Requests are
rate-limited and carry an honest, contactable `User-Agent`.
