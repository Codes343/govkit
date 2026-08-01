"""Grants.gov Funding Opportunities Scraper — Apify Actor entrypoint."""

from __future__ import annotations

import logging

from apify import Actor

from govkit.billing import Billing
from govkit.http import GovKitClient, UpstreamError
from govkit.sources import grants_gov

logger = logging.getLogger(__name__)

DEFAULT_MAX_ITEMS = 1000
HARD_MAX_ITEMS = 50_000


def _as_list(value: object) -> list[str] | None:
    """Accept either a real array or a comma-separated string from the input."""
    if value is None:
        return None
    if isinstance(value, str):
        parts = [p.strip() for p in value.split(",")]
    elif isinstance(value, list):
        parts = [str(p).strip() for p in value]
    else:
        return None
    parts = [p for p in parts if p]
    return parts or None


async def main() -> None:
    async with Actor:
        raw = await Actor.get_input() or {}

        statuses = _as_list(raw.get("oppStatuses")) or ["posted", "forecasted"]
        invalid = [s for s in statuses if s not in grants_gov.VALID_STATUSES]
        if invalid:
            await Actor.fail(
                status_message=(
                    f"Unknown opportunity status {invalid}. "
                    f"Valid values: {', '.join(grants_gov.VALID_STATUSES)}."
                )
            )
            return

        max_items = raw.get("maxItems") or DEFAULT_MAX_ITEMS
        try:
            max_items = max(1, min(int(max_items), HARD_MAX_ITEMS))
        except (TypeError, ValueError):
            max_items = DEFAULT_MAX_ITEMS

        include_details = bool(raw.get("includeDetails", True))

        filters = {
            "keyword": (raw.get("keyword") or "").strip() or None,
            "statuses": statuses,
            "agencies": _as_list(raw.get("agencies")),
            "eligibilities": _as_list(raw.get("eligibilities")),
            "funding_categories": _as_list(raw.get("fundingCategories")),
            "funding_instruments": _as_list(raw.get("fundingInstruments")),
            "aln": (raw.get("aln") or "").strip() or None,
            "opportunity_number": (raw.get("opportunityNumber") or "").strip() or None,
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
