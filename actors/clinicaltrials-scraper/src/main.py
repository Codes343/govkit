"""ClinicalTrials.gov Studies Scraper — Apify Actor entrypoint."""

from __future__ import annotations

import logging

from apify import Actor

from govkit import inputs
from govkit.billing import Billing
from govkit.http import GovKitClient, UpstreamError
from govkit.sources import clinicaltrials

logger = logging.getLogger(__name__)

DEFAULT_MAX_ITEMS = 1000
HARD_MAX_ITEMS = 50_000


async def main() -> None:
    async with Actor:
        raw = await Actor.get_input() or {}

        statuses = inputs.as_list(raw.get("overallStatus"))
        invalid = inputs.invalid_choices(statuses, clinicaltrials.OVERALL_STATUSES)
        if invalid:
            await Actor.fail(
                status_message=(
                    f"Unknown study status {invalid}. Valid values: "
                    f"{', '.join(clinicaltrials.OVERALL_STATUSES)}."
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
            "condition": inputs.as_text(raw.get("condition")),
            "intervention": inputs.as_text(raw.get("intervention")),
            "term": inputs.as_text(raw.get("term")),
            "sponsor": inputs.as_text(raw.get("sponsor")),
            "location": inputs.as_text(raw.get("location")),
            "overall_status": statuses,
        }

        billing = Billing(Actor)
        await billing.charge_start()

        total = 0
        try:
            async with GovKitClient(clinicaltrials.SOURCE) as client:
                async for page in clinicaltrials.search(
                    client, max_items=max_items, **filters
                ):
                    accepted = await billing.push_many(page)
                    total += accepted
                    logger.info("Pushed %d studies (%d total)", accepted, total)
                    if billing.limit_reached:
                        await Actor.set_status_message(
                            f"Stopped at {total} results — your maximum run charge "
                            "was reached. Raise it in the run options to get more."
                        )
                        break
        except UpstreamError as exc:
            await Actor.fail(
                status_message=(
                    f"ClinicalTrials.gov could not be reached: {exc}. This is an "
                    "upstream outage, not a problem with your input. "
                    "Please retry shortly."
                )
            )
            return

        if total == 0:
            await Actor.set_status_message(
                "No studies matched your filters. Try a broader condition, or "
                "remove the status filter to include completed studies."
            )
        else:
            await Actor.set_status_message(f"Done — {total} clinical studies.")
