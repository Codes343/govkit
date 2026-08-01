"""USAspending Federal Awards Scraper — Apify Actor entrypoint."""

from __future__ import annotations

import logging
from datetime import date

from apify import Actor

from govkit import inputs
from govkit.billing import Billing
from govkit.http import GovKitClient, UpstreamError
from govkit.sources import usaspending

logger = logging.getLogger(__name__)

DEFAULT_MAX_ITEMS = 1000
HARD_MAX_ITEMS = 50_000


async def main() -> None:
    async with Actor:
        raw = await Actor.get_input() or {}

        group = inputs.as_text(raw.get("awardCategory")) or "contracts"
        if group not in usaspending.AWARD_TYPE_GROUPS:
            await Actor.fail(
                status_message=(
                    f"Unknown award category {group!r}. Valid values: "
                    f"{', '.join(usaspending.AWARD_TYPE_GROUPS)}."
                )
            )
            return

        # USAspending requires a time period, so supply a sane default rather
        # than failing on an input the user never knew was mandatory.
        start_date = inputs.as_text(raw.get("startDate")) or "2020-01-01"
        end_date = inputs.as_text(raw.get("endDate")) or date.today().isoformat()

        max_items = inputs.as_int(
            raw.get("maxItems"),
            default=DEFAULT_MAX_ITEMS,
            minimum=1,
            maximum=HARD_MAX_ITEMS,
        )

        filters = {
            "award_types": usaspending.AWARD_TYPE_GROUPS[group],
            "start_date": start_date,
            "end_date": end_date,
            "keywords": inputs.as_list(raw.get("keywords")),
            "agencies": inputs.as_list(raw.get("agencies")),
            "recipient_search_text": inputs.as_list(raw.get("recipients")),
            "place_of_performance_states": inputs.as_list(raw.get("states")),
            "award_amount_min": inputs.as_float(raw.get("awardAmountMin")),
            "award_amount_max": inputs.as_float(raw.get("awardAmountMax")),
        }

        billing = Billing(Actor)
        await billing.charge_start()

        total = 0
        try:
            async with GovKitClient(usaspending.SOURCE) as client:
                async for page in usaspending.search(
                    client, max_items=max_items, **filters
                ):
                    accepted = await billing.push_many(page)
                    total += accepted
                    logger.info("Pushed %d awards (%d total)", accepted, total)
                    if billing.limit_reached:
                        await Actor.set_status_message(
                            f"Stopped at {total} results — your maximum run charge "
                            "was reached. Raise it in the run options to get more."
                        )
                        break
        except UpstreamError as exc:
            await Actor.fail(
                status_message=(
                    f"USAspending.gov could not be reached: {exc}. This is an "
                    "upstream outage, not a problem with your input. "
                    "Please retry shortly."
                )
            )
            return

        if total == 0:
            await Actor.set_status_message(
                "No awards matched your filters. Widen the date range, or try a "
                "different award category — contracts and grants are separate "
                "datasets and never appear in the same result."
            )
        else:
            await Actor.set_status_message(f"Done — {total} federal awards.")
