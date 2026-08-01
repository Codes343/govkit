# Pricing

## The configured prices

| Event | Name in code | Price | Charged when |
|---|---|---|---|
| Actor start | `actor-start` | $0.005 | Once, at the start of every run |
| Result delivered | `dataset-item` | $0.003 | Per record actually written to the dataset |

These names must match `src/fedstack/billing.py` exactly, and are configured in
Apify Console per actor (SETUP.md step 5). If you change one, change both.

## Why these numbers

**$0.003 per record ($3 per 1,000).** Three constraints pin this down:

1. **It must clear the free tier meaningfully.** Apify's free plan gives $5/month
   of credit, which buys ~1,600 of our records. That is enough for a prospect to
   pull a real, useful dataset and decide the actor works — but not enough to run
   a business on, which is the point at which they upgrade.
2. **It must beat the alternative.** A developer's alternative is writing the
   integration themselves: roughly a day of work to handle four date formats,
   `"none"`-as-a-string, HTML descriptions, pipe-delimited filters, cursor
   pagination, and a second endpoint for detail. At $3/1,000 records the actor is
   cheaper than the first hour of that.
3. **It must be far below the incumbents.** GovWin IQ and Bloomberg Government
   sell adjacent data at $10k+/year. Being three orders of magnitude cheaper is
   the wedge, so there is no reason to price near them.

**$0.005 per run.** Deliberately near-zero. It exists only so that a run which
legitimately returns zero results still covers its own compute. Pricing the
*start* high would punish exactly the exploratory runs that turn a visitor into
a customer.

**Why not per-run pricing instead?** Because a run can return 5 records or
50,000. Per-run pricing either robs the small user or bankrupts us on the large
one. Per-result is the only model where our revenue and the customer's value
move together.

## Unit economics

```
1,000 detailed records
  gross          = $0.005 + (1,000 x $0.003)   = $3.005
  Apify 20%      = -$0.601
  compute        ~ -$0.01   (HTTP only, 128 MB, no browser, no proxies)
  ------------------------------------------------------------
  net to us                                    ~ $2.39
```

**Break-even for the $20/month goal: ~8,400 records/month delivered.**

The margin holds because every Fedstack actor is plain HTTP against a keyless
JSON API. There is no headless browser, no residential proxy ($8/GB), and no
paid upstream. That single architectural choice is what makes a $3 price point
profitable — and it is also why we will not add a source that needs a browser
or a paid API key without re-running this math first.

## Changing prices later

Raising prices on an actor with existing users is a real risk to a fragile
early revenue line. Prefer, in order:

1. Add a *new* higher-value event (e.g. a `document-download` event) rather than
   raising `dataset-item`.
2. Ship a separate premium actor.
3. Only then, adjust the base rate.

Any change must be reflected in three places or the reporting silently lies:
Apify Console, `PRICE_*` in `scripts/revenue_report.py`, and the Pricing section
of each actor's `README.md`.
