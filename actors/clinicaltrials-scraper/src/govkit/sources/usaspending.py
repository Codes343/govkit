"""USAspending.gov — federal contract, grant and loan awards.

API: https://api.usaspending.gov/api/v2/search/spending_by_award/ (POST, no auth)

Answers "who received federal money, from which agency, for what". The award
type codes are the part everyone gets wrong, so they are named here rather than
left to the caller.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from govkit.http import GovKitClient
from govkit.normalize import clean_date, clean_money, clean_str, clean_text, compact

SOURCE = "usaspending.gov"
SEARCH_URL = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
AWARD_URL_TEMPLATE = "https://www.usaspending.gov/award/{id}"

PAGE_SIZE = 100  # documented maximum

# USAspending rejects a mixed request: every code in one call must belong to the
# same award family. These groups are what the UI's category tabs map to.
AWARD_TYPE_GROUPS: dict[str, list[str]] = {
    "contracts": ["A", "B", "C", "D"],
    "grants": ["02", "03", "04", "05"],
    "direct_payments": ["06", "10"],
    "loans": ["07", "08"],
    "other": ["09", "11", "-1"],
    "idvs": [
        "IDV_A",
        "IDV_B",
        "IDV_B_A",
        "IDV_B_B",
        "IDV_B_C",
        "IDV_C",
        "IDV_D",
        "IDV_E",
    ],
}

# "Award ID" means different things per family, so the field list must match the
# group being requested; these are the fields valid for all non-IDV families.
FIELDS = [
    "Award ID",
    "Recipient Name",
    "Award Amount",
    "Total Outlays",
    "Description",
    "Awarding Agency",
    "Awarding Sub Agency",
    "Start Date",
    "End Date",
    "Award Type",
    "recipient_id",
]


def normalize(award: dict[str, Any]) -> dict[str, Any]:
    generated_id = clean_str(award.get("generated_internal_id"))
    return compact(
        {
            "awardId": clean_str(award.get("Award ID")),
            "recipientName": clean_str(award.get("Recipient Name")),
            "awardAmount": clean_money(award.get("Award Amount")),
            "totalOutlays": clean_money(award.get("Total Outlays")),
            "description": clean_text(award.get("Description")),
            "awardingAgency": clean_str(award.get("Awarding Agency")),
            "awardingSubAgency": clean_str(award.get("Awarding Sub Agency")),
            "startDate": clean_date(award.get("Start Date")),
            "endDate": clean_date(award.get("End Date")),
            "awardType": clean_str(award.get("Award Type")),
            "recipientId": clean_str(award.get("recipient_id")),
            "agencySlug": clean_str(award.get("agency_slug")),
            "url": (AWARD_URL_TEMPLATE.format(id=generated_id) if generated_id else None),
            "source": SOURCE,
        }
    )


def build_body(
    *,
    award_types: list[str],
    start_date: str,
    end_date: str,
    keywords: list[str] | None = None,
    agencies: list[str] | None = None,
    recipient_search_text: list[str] | None = None,
    place_of_performance_states: list[str] | None = None,
    award_amount_min: float | None = None,
    award_amount_max: float | None = None,
    page: int = 1,
    limit: int = PAGE_SIZE,
) -> dict[str, Any]:
    filters: dict[str, Any] = {
        "award_type_codes": award_types,
        "time_period": [{"start_date": start_date, "end_date": end_date}],
    }
    if keywords:
        filters["keywords"] = keywords
    if agencies:
        filters["agencies"] = [
            {"type": "awarding", "tier": "toptier", "name": a} for a in agencies
        ]
    if recipient_search_text:
        filters["recipient_search_text"] = recipient_search_text
    if place_of_performance_states:
        filters["place_of_performance_locations"] = [
            {"country": "USA", "state": s.upper()} for s in place_of_performance_states
        ]
    if award_amount_min is not None or award_amount_max is not None:
        bound: dict[str, float] = {}
        if award_amount_min is not None:
            bound["lower_bound"] = award_amount_min
        if award_amount_max is not None:
            bound["upper_bound"] = award_amount_max
        filters["award_amounts"] = [bound]

    return {
        "filters": filters,
        "fields": FIELDS,
        "page": page,
        "limit": limit,
        "sort": "Award Amount",
        "order": "desc",
        "subawards": False,
    }


async def search(
    client: GovKitClient, *, max_items: int, **filters: Any
) -> AsyncIterator[list[dict[str, Any]]]:
    """Yield pages of normalized awards until exhausted or max_items met."""
    page = 1
    yielded = 0

    while yielded < max_items:
        limit = min(PAGE_SIZE, max_items - yielded)
        body = build_body(page=page, limit=limit, **filters)
        payload = await client.post_json(SEARCH_URL, body)

        results = payload.get("results") or []
        if not results:
            return

        batch = [normalize(a) for a in results]
        yielded += len(batch)
        yield batch

        if not (payload.get("page_metadata") or {}).get("hasNext"):
            return
        page += 1
