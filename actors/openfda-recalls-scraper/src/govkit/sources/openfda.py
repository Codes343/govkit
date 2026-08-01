"""openFDA — food, drug and device recall/enforcement reports.

API: https://api.fda.gov/{food,drug,device}/enforcement.json (GET, no auth)

openFDA is keyless up to a modest daily quota and caps `skip` at 25,000, which
is the real pagination ceiling rather than the result count.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from govkit.http import GovKitClient, UpstreamError
from govkit.normalize import clean_date, clean_str, clean_text, compact

SOURCE = "api.fda.gov"
BASE_URL = "https://api.fda.gov/{category}/enforcement.json"

CATEGORIES = ("food", "drug", "device")

PAGE_SIZE = 1000  # documented maximum without an API key
MAX_SKIP = 25_000  # openFDA refuses to page past this

CLASSIFICATIONS = {
    "Class I": "Reasonable probability of serious health consequences or death",
    "Class II": "May cause temporary or medically reversible health consequences",
    "Class III": "Not likely to cause adverse health consequences",
}


def normalize(record: dict[str, Any], category: str) -> dict[str, Any]:
    classification = clean_str(record.get("classification"))
    return compact(
        {
            "recallNumber": clean_str(record.get("recall_number")),
            "eventId": clean_str(record.get("event_id")),
            "category": category,
            "status": clean_str(record.get("status")),
            "classification": classification,
            "classificationMeaning": CLASSIFICATIONS.get(classification or ""),
            "recallingFirm": clean_str(record.get("recalling_firm")),
            "productDescription": clean_text(record.get("product_description")),
            "productQuantity": clean_str(record.get("product_quantity")),
            "reasonForRecall": clean_text(record.get("reason_for_recall")),
            "distributionPattern": clean_text(record.get("distribution_pattern")),
            "voluntaryOrMandated": clean_str(record.get("voluntary_mandated")),
            "initialFirmNotification": clean_str(record.get("initial_firm_notification")),
            "reportDate": clean_date(record.get("report_date")),
            "recallInitiationDate": clean_date(record.get("recall_initiation_date")),
            "centerClassificationDate": clean_date(
                record.get("center_classification_date")
            ),
            "terminationDate": clean_date(record.get("termination_date")),
            "city": clean_str(record.get("city")),
            "state": clean_str(record.get("state")),
            "country": clean_str(record.get("country")),
            "postalCode": clean_str(record.get("postal_code")),
            "codeInfo": clean_text(record.get("code_info")),
            "source": SOURCE,
        }
    )


def build_search(
    *,
    reported_after: str | None = None,
    reported_before: str | None = None,
    classifications: list[str] | None = None,
    statuses: list[str] | None = None,
    firm: str | None = None,
    keyword: str | None = None,
) -> str | None:
    """Build an openFDA Lucene query. Clauses AND together, values OR within."""
    clauses: list[str] = []

    if reported_after or reported_before:
        # openFDA dates are YYYYMMDD with no separators.
        lo = (reported_after or "1900-01-01").replace("-", "")
        hi = (reported_before or "2100-12-31").replace("-", "")
        clauses.append(f"report_date:[{lo} TO {hi}]")

    def any_of(field: str, values: list[str]) -> str:
        quoted = " OR ".join(f'"{v}"' for v in values)
        return f"{field}:({quoted})"

    if classifications:
        clauses.append(any_of("classification", classifications))
    if statuses:
        clauses.append(any_of("status", statuses))
    if firm:
        clauses.append(f'recalling_firm:"{firm}"')
    if keyword:
        clauses.append(
            f'(reason_for_recall:"{keyword}" OR product_description:"{keyword}")'
        )

    return " AND ".join(clauses) if clauses else None


async def search(
    client: GovKitClient,
    *,
    max_items: int,
    categories: list[str] | None = None,
    **filters: Any,
) -> AsyncIterator[list[dict[str, Any]]]:
    """Yield pages of normalized recalls across the requested categories."""
    wanted = [c for c in (categories or list(CATEGORIES)) if c in CATEGORIES]
    query = build_search(**filters)
    yielded = 0

    for category in wanted:
        url = BASE_URL.format(category=category)
        skip = 0

        while yielded < max_items and skip < MAX_SKIP:
            limit = min(PAGE_SIZE, max_items - yielded, MAX_SKIP - skip)
            try:
                payload = await client.get_json(url, search=query, limit=limit, skip=skip)
            except UpstreamError as exc:
                # openFDA answers "no documents match" with HTTP 404. That is an
                # empty result for this category, not a failure of the run.
                if exc.status == 404:
                    break
                raise

            results = payload.get("results") or []
            if not results:
                break

            batch = [normalize(r, category) for r in results]
            yielded += len(batch)
            skip += len(results)
            yield batch

            total = ((payload.get("meta") or {}).get("results") or {}).get("total")
            if isinstance(total, int) and skip >= total:
                break
            if len(results) < limit:
                break
