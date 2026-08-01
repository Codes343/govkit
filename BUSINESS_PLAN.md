# GovKit — Autonomous Business Plan

**Target:** ≥ $20 USD/month profit. **Budget:** $0. **Owner workload:** ~45 min one-time, ~0/month after.

---

## 1. Executive Summary

**GovKit** is a portfolio of paid data-extraction tools ("Actors") published on **Apify Store**, serving structured US federal open-government data — grant opportunities, contract awards, regulatory filings, product recalls, and clinical trials — to GovCon firms, grant writers, researchers, journalists, and AI agents.

The core insight from research: **for a $0-budget digital business, the binding constraint is distribution, not product.** Gumroad "brings you almost no buyers"; itch.io asset packs earn $20–30/mo but demand 30+ hrs/month of human work. Both fail Rule 1 or Rule 4.

Apify Store is the rare channel that supplies **all four** things a zero-budget autonomous business needs:

| Need | Apify supplies it |
|---|---|
| Free hosting + compute | $5/mo free credits, no credit card |
| Built-in buyer traffic | 40k+ actors, 4M+ developers; actor pages rank on Google |
| Payment + billing infra | Stripe, invoicing, plan management, monthly payout on the 11th |
| Zero support burden | Self-serve; docs + input schema answer questions |

Developers keep **80%** of revenue minus platform compute. Because every GovKit actor calls a **keyless, free, government JSON API over plain HTTP** — no browser, no proxies — compute cost is near zero and gross margin approaches the full 80%.

**Why this niche:** a competition sweep found 9+ actors for ATS job scraping and 6+ for SEC EDGAR, but **zero** for Grants.gov, USAspending, or FDA recalls. Meanwhile the commercial value of this data is proven — GovWin IQ and Bloomberg Government sell it at $10k+/yr.

---

## 2. The Chosen Business Model

Publish 5 pay-per-event Apify Actors sharing one codebase:

| # | Actor | Upstream API | Auth | Buyer |
|---|---|---|---|---|
| 1 | **Grants.gov Funding Opportunities Scraper** | `api.grants.gov/v1/api/search2` | none | Grant writers, nonprofits, universities |
| 2 | **USAspending Federal Awards Scraper** | `api.usaspending.gov/api/v2` | none | GovCon sales, analysts, journalists |
| 3 | **Federal Register Rules & Notices Scraper** | `federalregister.gov/api/v1` | none | Compliance, policy, legal |
| 4 | **openFDA Recalls & Enforcement Scraper** | `api.fda.gov` | none | Food/pharma QA, retail compliance |
| 5 | **ClinicalTrials.gov Studies Scraper** | `clinicaltrials.gov/api/v2` | none | Biotech CI, recruiters, researchers |

All five verified live and returning HTTP 200 without credentials on 2026-07-31.

**Revenue mechanic — pay per event (PPE):**
- `actor-start`: **$0.005**
- `dataset-item`: **$0.003** (= $3 per 1,000 records)

Apify's free tier ($5 credits) lets a prospect pull ~1,600 records before paying — generous enough to hook, small enough to convert serious users.

---

## 3. Why This Beats the Other 29 Ideas

30 ideas scored 1–5 on seven axes. **EV** = mean of the seven, with *Likelihood of $20/mo* double-weighted (it is the pass/fail criterion).

Legend — Cost: 5 = truly $0. Auto: 5 = zero human work. Comp: 5 = uncontested. Demand / Scale / Speed / **Likely**: 5 = best.

| # | Idea | Cost | Auto | Comp | Demand | Scale | Speed | **Likely** | **EV** |
|---|---|---|---|---|---|---|---|---|---|
| **1** | **Apify federal open-data actors** | **5** | **5** | **5** | **4** | **4** | **4** | **4** | **4.25** |
| 2 | Apify actors, other underserved niche | 5 | 5 | 4 | 4 | 4 | 4 | 4 | 4.13 |
| 3 | Paid MCP server (Smithery/mcp.so) | 5 | 5 | 4 | 4 | 4 | 3 | 3 | 3.75 |
| 4 | Open-core CLI + paid pro on Polar | 5 | 4 | 3 | 4 | 4 | 3 | 3 | 3.50 |
| 5 | Programmatic SEO + SaaS affiliate | 5 | 5 | 2 | 4 | 5 | 1 | 3 | 3.25 |
| 6 | Free web tool + Ko-fi/BMC tip jar | 5 | 5 | 3 | 3 | 3 | 3 | 2 | 3.13 |
| 7 | GitHub Sponsors on an OSS library | 5 | 4 | 3 | 3 | 3 | 2 | 2 | 2.88 |
| 8 | Niche RSS/alerting email digest, paid | 5 | 4 | 3 | 3 | 3 | 3 | 2 | 2.88 |
| 9 | itch.io game asset packs | 5 | 2 | 2 | 3 | 3 | 3 | 3 | 2.88 |
| 10 | Hugging Face Space + paid API | 4 | 4 | 3 | 3 | 3 | 3 | 2 | 2.75 |
| 11 | Notion / Obsidian template packs | 5 | 3 | 1 | 4 | 3 | 4 | 2 | 2.75 |
| 12 | Cloudflare Worker micro-API + Stripe | 5 | 5 | 3 | 3 | 4 | 2 | 2 | 2.75 |
| 13 | Curated dataset sales (Kaggle/HF/Gumroad) | 5 | 4 | 3 | 2 | 3 | 3 | 2 | 2.63 |
| 14 | Figma community plugin/template | 5 | 3 | 2 | 3 | 3 | 3 | 2 | 2.50 |
| 15 | Discord bot, freemium | 5 | 4 | 2 | 3 | 3 | 2 | 2 | 2.50 |
| 16 | VS Code extension + license key | 5 | 4 | 2 | 3 | 3 | 2 | 2 | 2.50 |
| 17 | Newsletter w/ sponsorships | 5 | 3 | 2 | 3 | 4 | 1 | 2 | 2.38 |
| 18 | Print-on-demand (Redbubble/Teepublic) | 5 | 3 | 1 | 3 | 3 | 3 | 2 | 2.38 |
| 19 | YouTube automation channel | 5 | 2 | 1 | 3 | 4 | 1 | 2 | 2.13 |
| 20 | Amazon KDP low-content books | 5 | 3 | 1 | 3 | 3 | 2 | 2 | 2.25 |
| 21 | Stock photo/vector via AI gen | 5 | 3 | 1 | 2 | 3 | 2 | 2 | 2.13 |
| 22 | Browser extension freemium | 2 | 4 | 2 | 3 | 3 | 2 | 2 | 2.13 |
| 23 | AI wrapper SaaS (own site) | 3 | 4 | 1 | 3 | 4 | 2 | 2 | 2.13 |
| 24 | Etsy digital downloads | 2 | 3 | 1 | 4 | 3 | 3 | 2 | 2.13 |
| 25 | Fiverr/Upwork productized gig | 5 | 1 | 2 | 4 | 2 | 4 | 2 | 2.13 |
| 26 | Affiliate review microsite | 5 | 4 | 1 | 3 | 3 | 1 | 2 | 2.13 |
| 27 | Crypto/DeFi yield or arbitrage bot | 1 | 4 | 2 | 3 | 4 | 2 | 1 | 1.88 |
| 28 | Dropshipping | 1 | 2 | 1 | 3 | 4 | 2 | 1 | 1.63 |
| 29 | Paid Discord/community membership | 5 | 1 | 2 | 2 | 2 | 1 | 1 | 1.63 |
| 30 | Mobile app w/ IAP | 1 | 3 | 1 | 3 | 4 | 1 | 1 | 1.63 |

**Why #1 beats each near-rival:**

- **vs #2 (other Apify niches):** same mechanics, but ATS/SEC/Maps/Amazon niches already have 6–9 incumbents and the Store algorithm favours incumbents by usage count. Federal data has zero. Same effort, uncontested shelf.
- **vs #3 (paid MCP server):** MCP monetization is real but the marketplaces are young and billing is fragmented across Stripe MPP / x402 / per-hub schemes. Apify's billing is mature and already pays out. *(Note: Apify actors are auto-exposed over MCP anyway — so #1 captures most of #3's upside for free.)*
- **vs #4/#7 (OSS + sponsors):** donations are unreliable; conversion from free users to sponsors is <0.1% and requires an audience I don't have.
- **vs #5 (programmatic SEO):** excellent long-run EV and near-zero cost, but time-to-first-revenue is 4–9 months and it needs an affiliate program approval. Kept as the **Phase 3 growth channel**, not the primary bet.
- **vs #9/#11/#18/#20/#24 (marketplace creative goods):** all fail Rule 4 — evidenced by the itch.io creator earning $20–30/mo for **30+ hrs/month**. GovKit's marginal hour cost after launch is zero.
- **vs #22/#24/#27/#28/#30:** all require upfront spend ($5 Chrome dev fee, $0.20/Etsy listing, capital, inventory, $99 Apple fee). Violate Rule 2.

---

## 4. Risk Analysis

| # | Risk | Severity | Probability | Mitigation |
|---|---|---|---|---|
| R1 | **No discovery.** Most actors get 0–5 users; Store ranking favours incumbents. | **Critical** | **High** | This is *the* risk. Mitigations: (a) uncontested niche, (b) 5 actors → 5 shots + cross-discovery, (c) optimize `seoTitle`/`seoDescription` (weighted heavily, usually neglected), (d) actor names match real Google queries, (e) Phase 3 external content. |
| R2 | Upstream API breaks or changes schema | High | Medium | Daily GitHub Actions smoke test hits all 5 endpoints, validates schema, auto-opens a GitHub issue. Actor fails soft with a clear message rather than charging for garbage. |
| R3 | Apify changes monetization terms | High | Low-Med | Already materialized once: rental model sunsets 2026-10-01. PPE is the *surviving* model, so we're building on the endorsed path. Code is portable — the scraping logic is plain Python, redeployable to Cloudflare Workers + Stripe. |
| R4 | Payout minimum not reached | Medium | Medium | Apify pays monthly; if a minimum applies, revenue accrues and pays out later. Delays cash, doesn't kill the business. **Verify on signup.** |
| R5 | Buyers won't pay for free public data | High | Medium | They already do — GovWin/Bloomberg Gov charge $10k+/yr. Value is in normalization, pagination, dedupe, scheduling, and delivery to Sheets/S3/webhooks, not in the bytes. |
| R6 | Compute cost exceeds revenue | Medium | Low | HTTP-only, 128 MB RAM, no browser/proxies. A 1,000-record run costs fractions of a cent and bills $3.01. |
| R7 | Rate limiting / IP ban from .gov | Medium | Low | Polite concurrency (≤5), backoff, honest `User-Agent` with contact URL, respect `Retry-After`. All data is explicitly public domain. |
| R8 | Support burden appears (violates Rule 1) | Medium | Medium | Exhaustive README + rich input-schema help text. If issues recur, fix the *product*, not the ticket. Hard cap: if support >30 min/month, redesign. |
| R9 | Copycats clone the actors | Low | High | Fine — first-mover accrues the usage count the ranking algorithm rewards. Defend with reliability score and breadth, not secrecy. |

**Kill criteria (Rule: don't invest in a failing strategy).** If **90 days after publish** total gross revenue < $5 *and* combined actor users < 10 → stop, and pivot to idea #5 (programmatic SEO on the same federal data, monetized by affiliate + AdSense), reusing the entire data pipeline.

---

## 5. Automation Architecture

```
                   ┌──────────────────────────────────────────┐
                   │  GitHub  (govkit repo, free)           │
                   │  • one shared Python package             │
                   │  • 5 actor manifests                     │
                   └───────────────┬──────────────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
   ┌──────────▼─────────┐  ┌───────▼────────┐  ┌────────▼──────────┐
   │ GH Action: deploy  │  │ GH Action:     │  │ GH Action:        │
   │ on push to master  │  │ daily smoke    │  │ weekly revenue    │
   │ → apify push × 5   │  │ test all APIs  │  │ report → issue    │
   └──────────┬─────────┘  │ → issue on fail│  └────────┬──────────┘
              │            └────────────────┘           │
   ┌──────────▼───────────────────────────────────────────────────┐
   │  APIFY PLATFORM                                              │
   │  ┌────────────┐ ┌────────────┐ ┌────────────┐               │
   │  │ Actor 1..5 │ │ PPE billing│ │ Store page │← Google/AI SEO │
   │  └─────┬──────┘ └─────┬──────┘ └────────────┘               │
   │        │              │                                      │
   │        │              └──→ Stripe → payout (11th monthly)    │
   │        │                                                     │
   │        └──→ auto-exposed as MCP tools → AI agents            │
   └──────────┬───────────────────────────────────────────────────┘
              │ HTTPS, keyless, ≤5 concurrent, backoff
   ┌──────────▼───────────────────────────────────────────────────┐
   │ grants.gov · usaspending.gov · federalregister.gov ·         │
   │ api.fda.gov · clinicaltrials.gov                             │
   └──────────────────────────────────────────────────────────────┘
```

**Every automation:**

| Automation | Mechanism | Replaces human task |
|---|---|---|
| Deploy on commit | GitHub Action → `apify push` | Manual deployment |
| Daily upstream health check | GitHub Action, cron 06:00 UTC | Manually noticing breakage |
| Auto-issue on failure | `gh issue create` in the workflow | Monitoring |
| Weekly revenue report | GH Action → Apify API → issue comment | Checking dashboards |
| Customer "support" | Input schema help + README + graceful errors | Answering emails |
| Billing, invoices, refunds | Apify/Stripe | Bookkeeping |
| Payouts | Apify, monthly on the 11th | Invoicing |
| Discovery/marketing | SEO fields + Store cross-discovery | Advertising |
| Agent distribution | Apify auto-exposes actors over MCP | BD/integrations |
| Pagination, retry, dedupe, rate limiting | Shared `govkit/core.py` | — |

**What cannot be automated, and why:** account creation, identity/tax/payout details, and clicking "Publish" — Apify and financial regulation require a legally responsible human. Total: one ~45-minute session.

---

## 6. Revenue Model

Gross per 1,000-record run = $0.005 + (1,000 × $0.003) = **$3.005**
Developer share = 80% = **$2.40**; minus ~$0.01 compute → **≈ $2.39 net per 1,000 records.**

**Break-even for the $20/month goal: ≈ 8,400 records/month billed.** Any of these clears it:

- 1 GovCon analyst pulling the full Grants.gov open set (~2,800 records) 3×/month, or
- 3 users × ~2,800 records/month, or
- 1 AI agent polling 280 new records/day, or
- ~8 casual users × 1,000 records.

For scale: Grants.gov alone currently exposes 210 posted + 21 forecasted + 648 closed + 3,739 archived opportunities on a single AI keyword query. USAspending and Federal Register are an order of magnitude larger.

---

## 7. Month-by-Month Projection

Deliberately conservative — assumes no viral event and no paid promotion.

| Month | Actors live | Users | Records billed | Gross | **Net to us** | Cumulative |
|---|---|---|---|---|---|---|
| Aug 2026 (M0) | 2 | 0–2 | ~500 | $1.51 | **$1.20** | $1.20 |
| Sep (M1) | 5 | 2–5 | ~3,000 | $9.02 | **$7.20** | $8.40 |
| Oct (M2) | 5 | 5–10 | ~7,000 | $21.03 | **$16.80** | $25.20 |
| **Nov (M3)** | 5 + 2 | 10–18 | **~9,500** | $28.55 | **$22.80 ✅** | $48.00 |
| Dec (M4) | 7 | 15–25 | ~14,000 | $42.06 | **$33.60** | $81.60 |
| Jan 2027 (M5) | 7 + SEO site | 25–40 | ~22,000 | $66.09 | **$52.80** | $134.40 |
| Feb (M6) | 9 | 35–55 | ~32,000 | $96.13 | **$76.80** | $211.20 |

**Goal crossed: Month 3 (November 2026).** Downside case (half these numbers) crosses in Month 5. Kill criteria trigger if M3 gross < $5.

**Reinvestment rule (Rule 3 / scaling).** Spend only from realized revenue, only when expected ROI > cost:
- First $29 of profit → **do not** buy the Apify Starter plan; it buys credits we don't consume. Hold.
- At ≥ $50/mo revenue → evaluate a $10–12/yr domain for an SEO content site pointing at the actors. Justified only if Store SEO is already producing measurable click-through.
- Never spend on ads. CAC on a $3/run product cannot pay back.

---

## 8. Exact Software Stack

| Layer | Choice | Cost |
|---|---|---|
| Language | Python 3.12 | $0 |
| SDK | `apify` (Apify Python SDK) | $0 |
| HTTP | `httpx` (async, HTTP/2, connection pooling) | $0 |
| Validation | `pydantic` v2 | $0 |
| Container | Apify base image `apify/actor-python:3.12` | $0 |
| Tests | `pytest`, `pytest-asyncio`, `respx` | $0 |
| Lint/format | `ruff` | $0 |
| VCS | Git + GitHub (public repo) | $0 |
| CI/CD | GitHub Actions (2,000 free min/mo; public repos unlimited) | $0 |
| Hosting/compute | Apify ($5/mo free credits, no card) | $0 |
| Payments | Apify → Stripe → bank | 20% rev share |
| Analytics | Apify Console: Insights → Monetization | $0 |
| Local dev | `apify-cli` via npx | $0 |

**Every service used:** GitHub, GitHub Actions, Apify Platform, Apify Store, Stripe (via Apify), grants.gov, usaspending.gov, federalregister.gov, api.fda.gov, clinicaltrials.gov. **Total recurring cost: $0.00.**

---

## 9. Legal / Human-Required Steps

One session, ~45 minutes, one time:

1. **Create a free Apify account** — apify.com/sign-up. No credit card required.
2. **Choose the profile username** — `govkit` (fallbacks: `govkit-data`, `civicfeed`, `opengrid-data`).
3. **Create an API token** — Console → Settings → Integrations → API tokens. Paste into `.env` locally and into GitHub repo secret `APIFY_TOKEN`.
4. **Complete billing/payout details** — Console → Settings → Billing. Required to receive money; involves identity and bank/PayPal details. *Human-only by law.* **While there, note the minimum payout threshold** (feeds risk R4).
5. **Click "Publish to Store"** on each actor and accept the Apify Store publishing terms.
6. *(Optional, later)* Register a free SAM.gov API key to unlock the contract-opportunities actor in Phase 2.

**Legal posture:** all five sources are US federal government works — public domain under 17 U.S.C. § 105 — accessed through documented public APIs with no authentication, no ToS acceptance, and no circumvention. No personal data is collected. No robots.txt is bypassed. This is the lowest-risk data category available.

---

## 10. Build Roadmap

**Phase 0 — Foundation** *(automated, in progress)*
Repo scaffold; shared `govkit` core (async HTTP client, retry/backoff, pagination, rate limiting, PPE charging helper); pytest suite; ruff config.

**Phase 1 — First two actors** *(automated)*
Grants.gov and Federal Register: `main.py`, `.actor/actor.json`, `input_schema.json`, SEO-optimized `README.md`, `Dockerfile`, PPE pricing manifest. Tests green locally.

**Phase 2 — CI/CD + monitoring** *(automated)*
Deploy workflow, daily smoke-test workflow, weekly revenue-report workflow.

**Phase 3 — Human handoff** *(~45 min, the owner)*
The 6 steps in §9. Everything else is already built and waiting.

**Phase 4 — Remaining three actors** *(automated)*
USAspending, openFDA, ClinicalTrials.gov.

**Phase 5 — Measure and iterate** *(automated, monthly)*
Read Apify Insights; double down on whichever actor gets traction; re-run the competition sweep for the next uncontested niche; evaluate kill criteria at day 90.

---

## 11. Self-Critique

**Why will this fail?** Almost certainly for one reason: **nobody finds the actors.** Product quality is not the risk; a 99% zero-user base rate is. Everything else — the code, the APIs, the billing — is solved and verified. So the plan allocates its scarce resource (breadth) directly at that risk: five uncontested listings instead of one polished one, SEO fields treated as the primary product surface, and a hard 90-day kill test.

**How can competitors beat me?** By cloning an actor once it shows usage. They can and will. But the ranking algorithm rewards accumulated usage, so first-mover in an empty category is the defensible position — which is exactly what's being taken.

**Is there a simpler version?** Yes: one actor, Grants.gov only. Rejected — it concentrates all risk in a single discovery lottery ticket when marginal tickets cost nothing but automated build time.

**Can I remove more human involvement?** The remaining human steps are account creation, identity/payout verification, and clicking Publish — all legally or contractually mandated. Post-launch human workload is zero; monitoring, deployment, reporting, and support are all automated or designed out.

**Weakest remaining assumption:** that buyers will pay for data that is free at the source. Partially de-risked by the existence of GovWin IQ and Bloomberg Government at $10k+/yr, and by the fact that six SEC EDGAR actors profitably resell an equally free API. Not eliminated — which is what the 90-day kill test is for.
