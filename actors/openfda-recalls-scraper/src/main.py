"""openFDA Recalls & Enforcement Scraper — Apify Actor entrypoint."""

from __future__ import annotations

import logging

from apify import Actor

from govkit import inputs
from govkit.billing import Billing
from govkit.http import GovKitClient, UpstreamError
from govkit.sources import openfda

logger = logging.getLogger(__name__)

DEFAULT_MAX_ITEMS = 1000
HARD_MAX_ITEMS = 50_000


async def main() -> None:
    async with Actor:
        raw = await Actor.get_input() or {}

        categories = inputs.as_list(raw.get("categories")) or list(openfda.CATEGORIES)
        invalid = inputs.invalid_choices(categories, openfda.CATEGORIES)
        if invalid:
            await Actor.fail(
                status_message=(
                    f"Unknown category {invalid}. Valid values: "
                    f"{', '.join(openfda.CATEGORIES)}."
                )
            )
            return

        max_items = inputs.as_int(
            raw.get("maxItems"),
            default=DEFAULT_MAX_ITEMS,
            minimum=1,
            maximum=HARD_MAX_ITEMS,
        )

        filters = {
            "reported_after": inputs.as_text(raw.get("reportedAfter")),
            "reported_before": inputs.as_text(raw.get("reportedBefore")),
            "classifications": inputs.as_list(raw.get("classifications")),
            "statuses": inputs.as_list(raw.get("statuses")),
            "firm": inputs.as_text(raw.get("recallingFirm")),
            "keyword": inputs.as_text(raw.get("keyword")),
        }

        billing = Billing(Actor)
        await billing.charge_start()

        total = 0
        try:
            async with GovKitClient(openfda.SOURCE) as client:
                async for page in openfda.search(
                    client, max_items=max_items, categories=categories, **filters
                ):
                    accepted = await billing.push_many(page)
                    total += accepted
                    logger.info("Pushed %d recalls (%d total)", accepted, total)
                    if billing.limit_reached:
                        await Actor.set_status_message(
                            f"Stopped at {total} results — your maximum run charge "
                            "was reached. Raise it in the run options to get more."
                        )
                        break
        except UpstreamError as exc:
            await Actor.fail(
                status_message=(
                    f"openFDA could not be reached: {exc}. This is an upstream "
                    "outage, not a problem with your input. Please retry shortly."
                )
            )
            return

        if total == 0:
            await Actor.set_status_message(
                "No recalls matched your filters. Try widening the date range or "
                "removing the classification filter."
            )
        else:
            await Actor.set_status_message(f"Done — {total} recall records.")
