"""Federal Register Rules & Notices Scraper — Apify Actor entrypoint."""

from __future__ import annotations

import logging

from apify import Actor

from govkit.billing import Billing
from govkit.http import GovKitClient, UpstreamError
from govkit.sources import federal_register as fr

logger = logging.getLogger(__name__)

DEFAULT_MAX_ITEMS = 1000
HARD_MAX_ITEMS = 50_000


def _as_list(value: object) -> list[str] | None:
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

        doc_types = _as_list(raw.get("documentTypes"))
        if doc_types:
            invalid = [t for t in doc_types if t not in fr.DOCUMENT_TYPES]
            if invalid:
                await Actor.fail(
                    status_message=(
                        f"Unknown document type {invalid}. Valid values: "
                        f"{', '.join(fr.DOCUMENT_TYPES)}."
                    )
                )
                return

        max_items = raw.get("maxItems") or DEFAULT_MAX_ITEMS
        try:
            max_items = max(1, min(int(max_items), HARD_MAX_ITEMS))
        except (TypeError, ValueError):
            max_items = DEFAULT_MAX_ITEMS

        filters = {
            "term": (raw.get("term") or "").strip() or None,
            "document_types": doc_types,
            "agencies": _as_list(raw.get("agencies")),
            "published_after": (raw.get("publishedAfter") or "").strip() or None,
            "published_before": (raw.get("publishedBefore") or "").strip() or None,
            "order": raw.get("order") or "newest",
        }

        billing = Billing(Actor)
        await billing.charge_start()

        total = 0
        try:
            async with GovKitClient(fr.SOURCE) as client:
                async for page in fr.search(client, max_items=max_items, **filters):
                    accepted = await billing.push_many(page)
                    total += accepted
                    logger.info("Pushed %d documents (%d total)", accepted, total)
                    if billing.limit_reached:
                        await Actor.set_status_message(
                            f"Stopped at {total} results — your maximum run charge "
                            "was reached. Raise it in the run options to get more."
                        )
                        break
        except UpstreamError as exc:
            await Actor.fail(
                status_message=(
                    f"The Federal Register API could not be reached: {exc}. "
                    "This is an upstream outage, not a problem with your input. "
                    "Please retry shortly."
                )
            )
            return

        if total == 0:
            await Actor.set_status_message(
                "No documents matched your filters. Try a broader search term or "
                "widen the publication date range."
            )
        else:
            await Actor.set_status_message(f"Done — {total} Federal Register documents.")
