"""Grants.gov Funding Opportunities Scraper — Apify Actor entrypoint."""

from __future__ import annotations

import logging

from apify import Actor

from govkit import inputs
from govkit.billing import Billing
from govkit.http import GovKitClient, UpstreamError
from govkit.sources import grants_gov

logger = logging.getLogger(__name__)

DEFAULT_MAX_ITEMS = 1000
HARD_MAX_ITEMS = 50_000


async def main() -> None:
    async with Actor:
        raw = await Actor.get_input() or {}

        statuses = inputs.as_list(raw.get("oppStatuses")) or ["posted", "forecasted"]
        invalid = inputs.invalid_choices(statuses, grants_gov.VALID_STATUSES)
        if invalid:
            await Actor.fail(
                status_message=(
                    f"Unknown opportunity status {invalid}. "
                    f"Valid values: {', '.join(grants_gov.VALID_STATUSES)}."
                )
            )
            return

        max_items = inputs.as_int(
            raw.get("maxItems"),
            default=DEFAULT_MAX_ITEMS,
            minimum=1,
            maximum=HARD_MAX_ITEMS,
        )
        include_details = bool(raw.get("includeDetails", True))

        filters = {
            "keyword": inputs.as_text(raw.get("keyword")),
            "statuses": statuses,
            "agencies": inputs.as_list(raw.get("agencies")),
            "eligibilities": inputs.as_list(raw.get("eligibilities")),
            "funding_categories": inputs.as_list(raw.get("fundingCategories")),
            "funding_instruments": inputs.as_list(raw.get("fundingInstruments")),
            "aln": inputs.as_text(raw.get("aln")),
            "opportunity_number": inputs.as_text(raw.get("opportunityNumber")),
        }

        billing = Billing(Actor)
        await billing.charge_start()

        total = 0
        try:
            async with GovKitClient(grants_gov.SOURCE) as client:
                async for page in grants_gov.search(
                    client, max_items=max_items, **filters
                ):
                    if include_details:
                        page = await grants_gov.enrich(client, page)

                    accepted = await billing.push_many(page)
                    total += accepted
                    logger.info("Pushed %d opportunities (%d total)", accepted, total)

                    if billing.limit_reached:
                        await Actor.set_status_message(
                            f"Stopped at {total} results — your maximum run charge "
                            "was reached. Raise it in the run options to get more."
                        )
                        break
        except UpstreamError as exc:
            # Grants.gov being down is not the customer's fault. Fail loudly with a
            # readable message; anything already delivered has already been billed.
            await Actor.fail(
                status_message=(
                    f"Grants.gov could not be reached: {exc}. "
                    "This is an upstream outage, not a problem with your input. "
                    "Please retry shortly."
                )
            )
            return

        if total == 0:
            await Actor.set_status_message(
                "No opportunities matched your filters. Try a broader keyword, or "
                "add 'closed' and 'archived' to oppStatuses to search past grants."
            )
        else:
            await Actor.set_status_message(f"Done — {total} funding opportunities.")
