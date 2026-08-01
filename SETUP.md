# Setup — the only steps a human has to do

Everything else is built. This is ~45 minutes, once. After this, your ongoing
workload is zero: deployment, monitoring, reporting and support are automated.

You need these six steps because Apify and financial regulation require a
legally responsible human to create the account, prove identity, and accept the
publishing terms. Nothing here can be automated by me.

**Total cost: $0.00. No credit card is required at any point.**

---

## 1. Create a free Apify account — 5 min

Go to <https://console.apify.com/sign-up>.

- Sign up with GitHub or email.
- **Do not** enter a credit card. The free plan gives $5/month of platform
  credit and that is all this business consumes.
- When asked for a username, this becomes your Store profile URL
  (`apify.com/<username>`), so pick one of these in order of preference:
  1. `fedstack`
  2. `fedstack-data`
  3. `civicfeed`
  4. `opengrid-data`

Write down which one you got — tell me and I'll update the READMEs and the
cross-links between actors.

---

## 2. Push this repo to GitHub — 5 min

From `fedstack/`:

```bash
git init && git add -A && git commit -m "Fedstack: federal open-data actors"
```

Then create an empty repo on GitHub and push to it. A **public** repo is
preferred: GitHub Actions minutes are unlimited on public repos, and the
transparency is a mild trust signal for buyers of a data product.

---

## 3. Create an Apify API token and give it to CI — 5 min

In Apify Console: **Settings → API & Integrations → Personal API tokens →
Create new token**. Name it `fedstack-ci`. Copy it.

Then in your GitHub repo: **Settings → Secrets and variables → Actions → New
repository secret**.

- Name: `APIFY_TOKEN`
- Value: the token you just copied

That single secret is what lets every future code change deploy itself.

---

## 4. Deploy the actors — 5 min

In GitHub: **Actions → Deploy actors → Run workflow**.

It will validate the manifests, run the tests, and push both actors to your
Apify account. Watch it go green. If it fails, the error message names the
exact problem.

*(Local alternative, if you'd rather: `python scripts/build_actor.py --push`
with `APIFY_TOKEN` set in your environment.)*

---

## 5. Turn on monetization and set the prices — 15 min

This is the step that makes it a business rather than a hobby. Do it for
**each** of the two actors.

In Apify Console → **Actors → `grants-gov-scraper` → Publication →
Monetization**:

1. Choose **Pay per event**.
2. Add these two events exactly (names must match the code in
   `src/fedstack/billing.py`):

   | Event name | Title | Price (USD) |
   |---|---|---|
   | `actor-start` | Actor start | `0.005` |
   | `dataset-item` | Result delivered | `0.003` |

3. Repeat identically for `federal-register-scraper`.

Full detail and the reasoning behind these numbers is in [PRICING.md](PRICING.md).

**While you are in Console, do the two billing chores:**

- **Settings → Billing → Payout details.** Fill in your identity and payout
  method. Apify cannot send you money without this. Payouts run monthly on the
  11th.
- **Note the minimum payout threshold** shown on that page and tell me the
  number. It feeds risk R4 in the business plan — if it's high, revenue simply
  accrues until it's met, which changes the cash-flow projection but not the
  business.

---

## 6. Publish to the Store — 10 min

For each actor: **Publication → Publish to Apify Store**, accept the terms,
and set the SEO fields.

**Do not skip the SEO fields.** Research on Store discovery is unambiguous:
`seoTitle` and `seoDescription` are weighted heavily and most developers leave
them blank. This is the single highest-leverage thing on the page.

Copy these in verbatim.

### `grants-gov-scraper`

- **SEO title:**
  `Grants.gov Scraper - Federal Grant Opportunities API & Data Export`
- **SEO description:**
  `Extract US federal grant opportunities from Grants.gov: award amounts, deadlines, eligibility, agency contacts and full descriptions. Export to JSON, CSV, Excel or Google Sheets. No API key needed.`

### `federal-register-scraper`

- **SEO title:**
  `Federal Register Scraper - Rules, Notices & Regulations Data API`
- **SEO description:**
  `Extract Federal Register documents: proposed rules, final rules, notices and presidential documents with agencies, dockets, RINs, CFR references and comment deadlines. Export to JSON, CSV or Excel.`

---

## That's it

Tell me when steps 1–6 are done, plus:

- the **username** you got in step 1,
- the **minimum payout threshold** from step 5.

I'll update the cross-links, then build the remaining three actors
(USAspending, openFDA, ClinicalTrials.gov) per the roadmap.

---

## What happens automatically from here

| When | What |
|---|---|
| Every push to `master` | Tests run, actors redeploy |
| Daily, 06:00 UTC | All upstream government APIs are smoke-tested; a GitHub issue is opened if one breaks, and closed when it recovers |
| Every Monday, 13:00 UTC | Revenue and traction report posted to a GitHub tracking issue |
| Monthly, the 11th | Apify pays out |

## The one thing to watch

Check the **Issues** tab on the Apify Store page for each actor every couple of
weeks. That is the only inbound channel a customer has. If the same question
appears twice, that's a product defect — send it to me and I'll fix the input
schema or README so it stops being asked. Per the plan, if this ever exceeds
30 minutes a month, the design is wrong and I'll change it.
